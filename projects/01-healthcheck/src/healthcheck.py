#!/usr/bin/env python3
"""課題1: サーバーヘルスチェックCLI — 参考実装（solutions ブランチ）。

これは「答え」だ。詰まったときの安全網として置いてある。
まず自分で書いてみて、どうしても進めないところだけ覗くのがおすすめ。
写すだけでは力にならない——なぜこう書くのかを、コース本文と見比べてほしい。
"""
import argparse
import json
import logging
import subprocess
import sys

log = logging.getLogger("healthcheck")


# ── 純関数（自動採点の対象）──────────────────────────────────────────

def judge(value, warn, crit):
    """値を閾値と比べて "OK"/"WARNING"/"CRITICAL"（大きいほど悪い前提）。"""
    if value >= crit:
        return "CRITICAL"
    if value >= warn:
        return "WARNING"
    return "OK"


_SEVERITY = {"OK": 0, "UNKNOWN": 1, "WARNING": 2, "CRITICAL": 3}


def worst_status(statuses):
    """状態リストから全体の状態（CRITICAL > WARNING > UNKNOWN > OK）。"""
    if not statuses:
        return "UNKNOWN"
    return max(statuses, key=lambda s: _SEVERITY.get(s, 1))


def status_to_exit_code(status):
    """状態 → 終了コード（OK=0/WARNING=1/CRITICAL=2/UNKNOWN=3）。"""
    return {"OK": 0, "WARNING": 1, "CRITICAL": 2, "UNKNOWN": 3}.get(status, 3)


# ── 収集（subprocess。失敗は例外にせず UNKNOWN として返す）────────────

def _run(cmd):
    """コマンドを実行して標準出力を返す。失敗時は RuntimeError。"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(f"実行できない: {e}")
    if r.returncode != 0:
        raise RuntimeError(f"終了コード {r.returncode}: {r.stderr.strip()}")
    return r.stdout


def check_disk_usage(warn, crit, path="/"):
    """ディスク使用率(%)を df から取る。"""
    out = _run(["df", "-P", path])
    # 2行目の5列目 "42%" を数値に。
    line = out.splitlines()[1]
    percent = int(line.split()[4].rstrip("%"))
    return {"name": "disk_usage", "status": judge(percent, warn, crit), "value": percent}


def check_load_average(warn, crit):
    """1分間のロードアベレージを uptime から取る。"""
    out = _run(["uptime"])
    # Linux は "load average: 1.85, 1.42, 1.10"、Mac は "load averages: 1.85 1.42 1.10"。
    # どちらでも拾えるように "load average" で割り、区切りを空白に均してから先頭を取る。
    after = out.lower().split("load average", 1)[1].lstrip("s").lstrip(":")
    one_min = float(after.replace(",", " ").split()[0])
    return {"name": "load_average", "status": judge(one_min, warn, crit), "value": one_min}


CHECKS = [check_disk_usage, check_load_average]


def collect(warn, crit):
    """全チェックを実行。個別の失敗は UNKNOWN にして続行する。"""
    results = []
    for fn in CHECKS:
        try:
            results.append(fn(warn, crit))
        except Exception as e:  # 部分障害でも全体を止めない
            log.warning("%s の収集に失敗: %s", fn.__name__, e)
            name = fn.__name__.replace("check_", "")
            results.append({"name": name, "status": "UNKNOWN", "value": None, "error": str(e)})
    return results


# ── 表示 ─────────────────────────────────────────────────────────────

def render_text(results, overall):
    lines = []
    for r in results:
        value = "-" if r.get("value") is None else r["value"]
        extra = f"  ({r['error']})" if r.get("error") else ""
        lines.append(f"[{r['status']:<9}] {r['name']:<12} {value}{extra}")
    lines.append(f"\n全体: {overall}")
    return "\n".join(lines)


def render_json(results, overall):
    return json.dumps(
        {"overall": overall, "exit_code": status_to_exit_code(overall), "checks": results},
        ensure_ascii=False, indent=2,
    )


# ── main ─────────────────────────────────────────────────────────────

def main(argv=None):
    parser = argparse.ArgumentParser(description="サーバーの状態を点検する")
    parser.add_argument("--warn", type=float, default=70, help="WARNING の閾値")
    parser.add_argument("--crit", type=float, default=90, help="CRITICAL の閾値")
    parser.add_argument("--json", action="store_true", help="JSON で出力する")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    log.info("点検開始 (warn=%s crit=%s)", args.warn, args.crit)

    results = collect(args.warn, args.crit)
    overall = worst_status([r["status"] for r in results])

    print(render_json(results, overall) if args.json else render_text(results, overall))
    log.info("点検終了: %s", overall)
    return status_to_exit_code(overall)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
