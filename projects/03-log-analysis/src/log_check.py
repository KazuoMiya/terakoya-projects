#!/usr/bin/env python3
"""課題3: ログ解析・障害検知ツール — 参考実装（solutions ブランチ）。

これは「答え」だ。詰まったときの安全網として置いてある。
まず自分で書いてみて、どうしても進めないところだけ覗くのがおすすめ。

この課題の要点（README と同じ。コードでどう守っているかを見比べてほしい）:
  - 1行ずつ読む。ログを全部メモリに載せない（本番のログはGB級になる）
  - 壊れた行で落ちない。数えて、飛ばして、続行する
    （空行は「読めなかった行」に数えない。expected-output.md の規約）
  - 急増検知は「倍率 × 絶対数」の二段構え。倍率だけだと「1件→3件」でも
    鳴ってしまい、誰も読まない通知が量産される（アラート疲れ）
  - 通知は異常のときだけ。正常時は沈黙する。通知は点検のおまけなので、
    通知の失敗で点検自体を失敗にしない

状態と終了コードは課題1・2と同じ:
    "OK"=0  "WARNING"=1  "CRITICAL"=2  "UNKNOWN"=3
"""
import argparse
import os
import re
import sys

# ── 課題1で自分が書いたもの。ここでは道具として配ってある ──────────────

_SEVERITY = {"OK": 0, "UNKNOWN": 1, "WARNING": 2, "CRITICAL": 3}


def worst_status(statuses):
    """状態リストから全体の状態（CRITICAL > WARNING > UNKNOWN > OK）。"""
    if not statuses:
        return "UNKNOWN"
    return max(statuses, key=lambda s: _SEVERITY.get(s, 1))


def status_to_exit_code(status):
    """状態 → 終了コード（OK=0/WARNING=1/CRITICAL=2/UNKNOWN=3）。"""
    return {"OK": 0, "WARNING": 1, "CRITICAL": 2, "UNKNOWN": 3}.get(status, 3)


# ── 純関数（自動採点の対象）──────────────────────────────────────────

# 日時19文字 ＋ 空白 ＋ レベル ＋ 空白1個以上 ＋ メッセージ。
# レベルの後ろの空白は1個とは限らない（"INFO  ..." のように2個のこともある）ので \s+。
_LINE_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(INFO|WARN|ERROR)\s+(.*)$"
)


def parse_line(line):
    """ログ1行を {"time", "level", "message"} に分解。形式外は None（落ちない）。

    re.match は形式に合わないと None を返す。その None を、そのまま
    「ログの形をしていない」という答えとして使う。例外は投げない——
    本物のログにはスタックトレースの続きのような行が必ず混ざる。
    """
    m = _LINE_RE.match(line.rstrip("\n"))  # 末尾の改行をデータに混ぜない習慣
    if m is None:
        return None
    time_str, level, message = m.groups()
    return {"time": time_str, "level": level, "message": message.strip()}


def bucket_by_hour(records, level="ERROR"):
    """指定レベルの件数を時間帯ごとに数える。キーは日時の先頭13文字。

    "2026-07-15 14:23:55"[:13] → "2026-07-15 14"。桁が固定なので
    日時のパースは要らず、文字列のまま切れる。
    """
    counts = {}
    for record in records:
        if record["level"] != level:
            continue
        hour = record["time"][:13]
        counts[hour] = counts.get(hour, 0) + 1
    return counts


def detect_spike(series, factor=3.0, min_count=10):
    """急増した時間帯のラベル一覧を返す。判定は二段構え・境界は「以上」。

    - series は時刻順に並んだ (ラベル, 件数) の一覧
    - ベースライン＝それより前の全時間帯の平均。自分自身は混ぜない
    - 件数 >= ベースライン × factor かつ 件数 >= min_count で急増
    - 先頭は比べる相手がいないので対象外（÷0 もここで防げる）

    min_count が無いと「1件→3件で3倍増！」が毎晩鳴り、人は通知を
    読まなくなる。倍率のワナを絶対数の下限で塞ぐ——アラート疲れへの防波堤。
    """
    spikes = []
    total = 0
    for i, (label, count) in enumerate(series):
        if i >= 1:
            baseline = total / i
            if count >= baseline * factor and count >= min_count:
                spikes.append(label)
        total += count
    return spikes


# ── 読む・レポート・通知・main（自動採点の対象外）────────────────────

def read_log(path):
    """ログを1行ずつ読み、(レコード一覧, レベル別件数, 読めなかった行数) を返す。

    f.read() で全部読まない。for line in f: は何GBでも一定のメモリで進む。
    空行は「読めなかった行」に数えない（expected-output.md の規約）。
    """
    records = []
    level_counts = {"ERROR": 0, "WARN": 0, "INFO": 0}
    unparsed = 0
    with open(path, encoding="utf-8") as f:
        for line in f:  # 1行ずつ。全部は読み込まない
            if not line.strip():
                continue  # 空行は数えず飛ばす
            record = parse_line(line)
            if record is None:
                unparsed += 1  # 数えて、飛ばして、続行
                continue
            records.append(record)
            level_counts[record["level"]] = level_counts.get(record["level"], 0) + 1
    return records, level_counts, unparsed


def build_report(level_counts, unparsed, buckets, spikes, top_n=5):
    """Markdown のレポートを組み立てる。# と表は飾りでなく構造だ。"""
    parsed_total = sum(level_counts.values())
    lines = [
        "# ログ点検レポート",
        "",
        f"- 解析した行: {parsed_total}（読めなかった行: {unparsed}）",
        "- 件数: ERROR {ERROR} / WARN {WARN} / INFO {INFO}".format(**level_counts),
        "",
    ]
    if spikes:
        lines += ["## ⚠ 急増を検知した時間帯", ""]
        for label in spikes:
            lines.append(f"- **{label}時台**: ERROR {buckets[label]} 件")
        lines.append("")
    lines += [
        f"## 時間帯別 ERROR 件数（多い順・上位{top_n}）",
        "",
        "| 時間帯 | 件数 |",
        "|---|---|",
    ]
    ranked = sorted(buckets.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]
    for label, count in ranked:
        mark = " ⚠" if label in spikes else ""
        lines.append(f"| {label} | {count}{mark} |")
    return "\n".join(lines)


def notify(body):
    """Slack Incoming Webhook に通知する。URL 未設定なら表示のみで完了扱い。

    Webhook URL は「URLの形をしたパスワード」なので .env に置く（コードに書かない）。
    通知は点検のおまけ——失敗しても結果は画面にあり、点検自体は失敗にしない。
    """
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # python-dotenv が無くても、環境変数が立っていれば動く
    url = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    if not url:
        print("（通知先が未設定なので表示のみ。以下が通知本文）")
        print(body)
        return
    try:
        import requests
    except ImportError:
        print("requests が無いので送れない（pip install -r requirements.txt）。結果は上に表示済み")
        return
    try:
        requests.post(url, json={"text": body}, timeout=5)
    except requests.RequestException:
        print("通知に失敗した（結果は上に表示済み）")


def main(argv=None):
    parser = argparse.ArgumentParser(description="ログ解析・障害検知ツール")
    parser.add_argument("logfile", help="解析するログファイル（例: logs/app.log）")
    parser.add_argument("--factor", type=float, default=3.0,
                        help="急増判定の倍率（既定: 3.0）")
    parser.add_argument("--min-count", type=int, default=10,
                        help="急増判定の最低件数（既定: 10）")
    args = parser.parse_args(argv)

    try:
        records, level_counts, unparsed = read_log(args.logfile)
    except OSError as exc:
        print(f"ログが読めない: {exc}")
        return status_to_exit_code("UNKNOWN")
    if not records:
        print("ログが読めない: 形式に合う行が1行も無い")
        return status_to_exit_code("UNKNOWN")

    buckets = bucket_by_hour(records, level="ERROR")
    series = sorted(buckets.items())  # 日時の文字列は桁固定なので、並べ替え＝時刻順
    spikes = detect_spike(series, factor=args.factor, min_count=args.min_count)

    print(build_report(level_counts, unparsed, buckets, spikes))

    status = "WARNING" if spikes else "OK"
    if spikes:  # 通知は急増のときだけ。正常時は沈黙が正常の合図
        summary = " / ".join(f"{label}時台 ERROR {buckets[label]} 件" for label in spikes)
        notify(f"⚠ ログ急増を検知: {summary}（{args.logfile}）")
    return status_to_exit_code(status)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
