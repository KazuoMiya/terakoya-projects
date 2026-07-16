#!/usr/bin/env python3
"""課題3: ログ解析・障害検知ツール — 参考実装（solutions ブランチ）。

これは「答え」だ。詰まったときの安全網として置いてある。
まず自分で書いてみて、どうしても進めないところだけ覗くのがおすすめ。

この課題の要点（コードでどう守っているかを見比べてほしい）:
  - 1行ずつ読む。ログを全部メモリに載せない
  - 壊れた行で落ちない。数えて、飛ばして、続行する
  - 急増検知は「倍率 × 絶対数の下限」の二段構え（アラート疲れの防波堤）
  - 通知は異常のときだけ。正常時は沈黙する
  - Webhook URL は「URLの形をしたパスワード」。.env に置き、コードに書かない
"""
import argparse
import logging
import os
import re
import sys

log = logging.getLogger("log_check")

# 状態モデルは課題1と同じ。小さな道具は現場でも持ち回る。
_SEVERITY = {"OK": 0, "UNKNOWN": 1, "WARNING": 2, "CRITICAL": 3}


def worst_status(statuses):
    if not statuses:
        return "UNKNOWN"
    return max(statuses, key=lambda s: _SEVERITY.get(s, 1))


def status_to_exit_code(status):
    return {"OK": 0, "WARNING": 1, "CRITICAL": 2, "UNKNOWN": 3}.get(status, 3)


# ── 純関数（自動採点の対象）──────────────────────────────────────────

# 行の形: "2026-07-15 14:23:55 ERROR db connection timeout host=db-01"
_LINE_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (INFO|WARN|ERROR)\s+(.*)$"
)


def parse_line(line):
    """ログ1行を {"time", "level", "message"} に分解。形式に合わなければ None。"""
    m = _LINE_RE.match(line)
    if not m:
        return None
    return {"time": m.group(1), "level": m.group(2), "message": m.group(3).strip()}


def bucket_by_hour(records, level="ERROR"):
    """指定レベルの件数を時間帯（日時の先頭13文字）ごとに数える。"""
    counts = {}
    for r in records:
        if r["level"] != level:
            continue
        hour = r["time"][:13]
        counts[hour] = counts.get(hour, 0) + 1
    return counts


def detect_spike(series, factor=3.0, min_count=10):
    """それまでの平均（ベースライン）× factor 以上、かつ min_count 以上なら急増。

    倍率だけだと「1件→3件」でも鳴る。min_count（絶対数の下限）が
    アラート疲れへの防波堤になる。先頭は比べる相手がいないので対象外。
    """
    spikes = []
    total = 0
    for i, (label, count) in enumerate(series):
        if i > 0:
            baseline = total / i
            if count >= baseline * factor and count >= min_count:
                spikes.append(label)
        total += count
    return spikes


# ── 読む（1行ずつ。全部メモリに載せない）──────────────────────────────

def read_log(path):
    """ログを1行ずつ読み、(レコード一覧, 読めなかった行数) を返す。"""
    records = []
    skipped = 0
    with open(path, encoding="utf-8") as f:
        for line in f:  # ← 1行ずつ。read() で全部読まない
            r = parse_line(line.rstrip("\n"))
            if r is None:
                if line.strip():  # 空行は数えない
                    skipped += 1
                continue
            records.append(r)
    return records, skipped


# ── レポート（Markdown）─────────────────────────────────────────────

def render_report(records, skipped, hourly, spikes):
    """人に読ませるための Markdown レポートを組み立てる。"""
    total = {"INFO": 0, "WARN": 0, "ERROR": 0}
    for r in records:
        if r["level"] in total:
            total[r["level"]] += 1

    lines = ["# ログ点検レポート", ""]
    lines.append(f"- 解析した行: {len(records)}（読めなかった行: {skipped}）")
    lines.append(f"- 件数: ERROR {total['ERROR']} / WARN {total['WARN']} / INFO {total['INFO']}")
    lines.append("")

    if spikes:
        lines.append("## ⚠ 急増を検知した時間帯")
        lines.append("")
        for label in spikes:
            lines.append(f"- **{label}時台**: ERROR {hourly.get(label, 0)} 件")
        lines.append("")

    lines.append("## 時間帯別 ERROR 件数（多い順・上位5）")
    lines.append("")
    lines.append("| 時間帯 | 件数 |")
    lines.append("|---|---|")
    for hour, n in sorted(hourly.items(), key=lambda x: -x[1])[:5]:
        mark = " ⚠" if hour in spikes else ""
        lines.append(f"| {hour} | {n}{mark} |")
    lines.append("")
    return "\n".join(lines)


# ── 通知（異常のときだけ。正常時は沈黙）────────────────────────────────

def notify(webhook_url, text):
    """Slack Incoming Webhook に1件だけ知らせる。失敗してもツールは落とさない。"""
    try:
        import requests  # 通知するときだけ使う

        resp = requests.post(webhook_url, json={"text": text}, timeout=5)
        if resp.status_code == 200:
            log.info("通知を送った")
            return True
        log.warning("通知に失敗した: HTTP %s", resp.status_code)
    except Exception as e:
        log.warning("通知に失敗した: %s", e)
    return False


def main(argv=None):
    parser = argparse.ArgumentParser(description="ログの集計と急増検知")
    parser.add_argument("logfile", nargs="?", default="logs/app.log", help="解析するログ")
    parser.add_argument("--factor", type=float, default=3.0, help="急増とみなす倍率")
    parser.add_argument("--min-count", type=int, default=10, help="急増とみなす最低件数")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # .env を読む（docker compose と違い、Python は自動では読まない——課題2でやった通り）
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass  # 通知を使わないなら無くても動く

    try:
        records, skipped = read_log(args.logfile)
    except OSError as e:
        log.error("ログが読めない: %s", e)
        return status_to_exit_code("UNKNOWN")

    hourly = bucket_by_hour(records)  # ERROR を時間帯ごとに
    series = sorted(hourly.items())  # 時刻順に並べてから急増を探す
    spikes = detect_spike(series, factor=args.factor, min_count=args.min_count)

    print(render_report(records, skipped, hourly, spikes))

    overall = "WARNING" if spikes else "OK"

    # 通知は異常のときだけ。正常時は沈黙する（アラート疲れを作らない）。
    if spikes:
        text = "⚠ ログ急増検知: " + ", ".join(
            f"{label}時台 ERROR {hourly.get(label, 0)}件" for label in spikes
        )
        webhook = os.environ.get("SLACK_WEBHOOK_URL")
        if webhook:
            notify(webhook, text)
        else:
            log.info("通知先が未設定なので表示のみ: %s", text)

    log.info("点検終了: %s", overall)
    return status_to_exit_code(overall)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
