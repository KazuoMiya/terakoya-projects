#!/usr/bin/env python3
"""課題4: 構成情報の収集と差分検知 — 参考実装（solutions ブランチ）。

これは「答え」だ。詰まったときの安全網として置いてある。
まず自分で書いてみて、どうしても進めないところだけ覗くのがおすすめ。
"""
import argparse
import json
import logging
import subprocess
import sys

log = logging.getLogger("config_diff")

_SEVERITY = {"OK": 0, "UNKNOWN": 1, "WARNING": 2, "CRITICAL": 3}


def worst_status(statuses):
    if not statuses:
        return "UNKNOWN"
    return max(statuses, key=lambda s: _SEVERITY.get(s, 1))


def status_to_exit_code(status):
    return {"OK": 0, "WARNING": 1, "CRITICAL": 2, "UNKNOWN": 3}.get(status, 3)


# ── 純関数（自動採点の対象）──────────────────────────────────────────

VOLATILE_KEYS = {"collected_at"}


def normalize(snapshot):
    """揺れる値を落とし、リストをソートした新しい辞書を返す。元は変更しない。"""
    out = {}
    for key, value in snapshot.items():
        if key in VOLATILE_KEYS:
            continue
        out[key] = sorted(value) if isinstance(value, list) else value
    return out


def diff_config(prev, curr):
    """正規化済みスナップショット同士の差分。リストは中身で比べる。"""
    diff = {"added": {}, "removed": {}, "changed": {}}
    for key in curr:
        if key not in prev:
            diff["added"][key] = curr[key]
    for key in prev:
        if key not in curr:
            diff["removed"][key] = prev[key]
    for key in curr:
        if key not in prev or prev[key] == curr[key]:
            continue
        if isinstance(prev[key], list) and isinstance(curr[key], list):
            prev_set, curr_set = set(prev[key]), set(curr[key])
            diff["changed"][key] = {
                "added": sorted(curr_set - prev_set),
                "removed": sorted(prev_set - curr_set),
            }
        else:
            diff["changed"][key] = {"before": prev[key], "after": curr[key]}
    return diff


def judge_diff(diff):
    """差分ゼロが正常。何かあれば WARNING（善悪の判断は人間の仕事）。"""
    if diff["added"] or diff["removed"] or diff["changed"]:
        return "WARNING"
    return "OK"


def select_old_files(entries, days, now_epoch):
    """days 日以上前のファイルのパスを返す。選ぶだけで、消さない。"""
    cutoff = now_epoch - days * 86400
    return [path for path, mtime in entries if mtime <= cutoff]


# ── 収集（環境依存。取れない項目は記録して続行）───────────────────────

def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if r.returncode != 0:
        raise RuntimeError(f"終了コード {r.returncode}: {r.stderr.strip()[:120]}")
    return r.stdout


def collect_packages():
    # Ubuntu/Debian 前提（WSL2 もこれ）。"名前 バージョン" の一覧にする。
    out = _run(["dpkg-query", "-W", "-f", "${Package} ${Version}\n"])
    return [line for line in out.splitlines() if line.strip()]


def collect_services():
    out = _run(["systemctl", "list-units", "--type=service", "--state=running",
                "--no-legend", "--plain"])
    return [line.split()[0].removesuffix(".service") for line in out.splitlines() if line.strip()]


def collect_listen_ports():
    # ss -tlnH: TCP・LISTEN・数値表示・ヘッダ無し。4列目 "0.0.0.0:80" の末尾がポート。
    out = _run(["ss", "-tlnH"])
    ports = set()
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 4:
            ports.add(int(parts[3].rsplit(":", 1)[1]))
    return sorted(ports)


def collect_users():
    # ログインできるシェルを持つユーザーだけ（システムユーザーのノイズを避ける）。
    users = []
    with open("/etc/passwd") as f:
        for line in f:
            fields = line.strip().split(":")
            if len(fields) >= 7 and fields[6] in ("/bin/bash", "/bin/sh", "/bin/zsh"):
                users.append(fields[0])
    return users


def collect_cron():
    try:
        out = _run(["crontab", "-l"])
    except RuntimeError:
        return []  # crontab が空だと終了コード1。空は異常ではない。
    return [line for line in out.splitlines()
            if line.strip() and not line.strip().startswith("#")]


COLLECTORS = {
    "packages": collect_packages,
    "services_running": collect_services,
    "listen_ports": collect_listen_ports,
    "users": collect_users,
    "cron_entries": collect_cron,
}


def collect(now_label):
    """全項目を収集。取れない項目は notes に残して続行する。"""
    snapshot = {"collected_at": now_label}
    notes = []
    for name, fn in COLLECTORS.items():
        try:
            snapshot[name] = fn()
        except Exception as e:  # 部分障害でも全体を止めない
            log.warning("%s を収集できなかった: %s", name, e)
            notes.append(f"{name}: {e}")
    return snapshot, notes


# ── 表示 ─────────────────────────────────────────────────────────────

def render_report(diff, notes):
    lines = ["# 構成差分レポート", ""]
    if judge_diff(diff) == "OK":
        lines.append("差分なし（前回と同じ構成）。")
    for key, value in diff["added"].items():
        lines.append(f"+ 新しい項目: {key} = {value}")
    for key, value in diff["removed"].items():
        lines.append(f"- 消えた項目: {key} = {value}")
    for key, change in diff["changed"].items():
        if "added" in change:
            for item in change["added"]:
                lines.append(f"+ {key}: {item}")
            for item in change["removed"]:
                lines.append(f"- {key}: {item}")
        else:
            lines.append(f"* {key}: {change['before']} → {change['after']}")
    if notes:
        lines.append("")
        lines.append("収集できなかった項目（差分には数えない）:")
        for note in notes:
            lines.append(f"  ? {note}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="構成情報の収集と差分検知")
    parser.add_argument("--snapshot", default="snapshot.local.json",
                        help="前回スナップショットの保存先")
    parser.add_argument("--label", default="(unknown)", help="collected_at に入れる時刻ラベル")
    parser.add_argument("--json", action="store_true", help="差分を JSON で出力する")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    snapshot, notes = collect(args.label)
    if len(snapshot) <= 1:  # collected_at しか無い＝何も収集できなかった
        log.error("何も収集できなかった。この環境では動かせない可能性が高い")
        return status_to_exit_code("UNKNOWN")

    # 前回を読む。無ければ「初回」——保存だけして OK で終わる（比べる相手がいない）。
    try:
        with open(args.snapshot) as f:
            prev = json.load(f)
    except FileNotFoundError:
        prev = None
    except ValueError:
        log.error("前回スナップショットが壊れている: %s", args.snapshot)
        return status_to_exit_code("UNKNOWN")

    with open(args.snapshot, "w") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    if prev is None:
        print("初回実行: ベースラインを保存した。次回から差分が出る。")
        return status_to_exit_code("OK")

    diff = diff_config(normalize(prev), normalize(snapshot))
    status = judge_diff(diff)

    if args.json:
        print(json.dumps({"overall": status, "exit_code": status_to_exit_code(status),
                          "diff": diff}, ensure_ascii=False, indent=2))
    else:
        print(render_report(diff, notes))

    log.info("差分チェック終了: %s", status)
    return status_to_exit_code(status)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
