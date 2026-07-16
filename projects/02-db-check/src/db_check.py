#!/usr/bin/env python3
"""課題2: DB日次点検ツール — 参考実装（solutions ブランチ）。

これは「答え」だ。詰まったときの安全網として置いてある。
まず自分で書いてみて、どうしても進めないところだけ覗くのがおすすめ。

鉄則（README と同じ。コードでどう守っているかを見比べてほしい）:
  1. 点検ツール自身が障害の原因になってはならない
     → 接続タイムアウトと実行タイムアウトを「両方」設定する。片方だけでは無限に待つ。
     → 読むのは統計ビューだけ。実テーブルを全件スキャンしない。
  2. 読み取り専用・最小権限。「直す」機能を混ぜない
     → checker ロールで接続する。pg_terminate_backend のような対処は実装しない。
  3. 点検結果そのものが機密になりうる
     → 接続情報はマスクしてから出す。SQL文には個人情報が写り込むので扱いに注意する。
"""
import argparse
import json
import logging
import os
import re
import shutil
import sys
import time
import urllib.parse

import psycopg
from dotenv import load_dotenv

log = logging.getLogger("db_check")

# 状態モデルは課題1と同じ。小さな道具は現場でも持ち回る。
_SEVERITY = {"OK": 0, "UNKNOWN": 1, "WARNING": 2, "CRITICAL": 3}


def worst_status(statuses):
    if not statuses:
        return "UNKNOWN"
    return max(statuses, key=lambda s: _SEVERITY.get(s, 1))


def status_to_exit_code(status):
    return {"OK": 0, "WARNING": 1, "CRITICAL": 2, "UNKNOWN": 3}.get(status, 3)


# ── 純関数（自動採点の対象）──────────────────────────────────────────

def mask_dsn(dsn):
    """接続文字列のパスワードを *** に置き換える（鉄則3）。

    ログにも画面にも、パスワードを出さないための関門。
    接続文字列の書き方は1つではないので、両方を塞ぐ:
      1. URL形式    postgresql://user:pass@host/db
      2. キー=値形式 host=... password=... （URLの ?password=... も同じ形）
    """
    masked = dsn

    # 1. URL形式: netloc の中のパスワードを潰す。
    parsed = urllib.parse.urlsplit(dsn)
    if parsed.password:
        userinfo = parsed.username or ""
        hostinfo = parsed.hostname or ""
        if parsed.port:
            hostinfo = f"{hostinfo}:{parsed.port}"
        netloc = f"{userinfo}:***@{hostinfo}" if userinfo else f":***@{hostinfo}"
        masked = urllib.parse.urlunsplit(
            (parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment)
        )

    # 2. "password=..." の形（キー=値形式・クエリ文字列）を最後にまとめて潰す。
    #    URL形式は上で既に *** になっているので、ここでは何も起きない。
    return re.sub(r"(password\s*=\s*)[^\s&]+", r"\1***", masked)


def judge_ratio(used, total, warn_pct, crit_pct):
    """使用率(%)で判定する。total が 0 や None なら測れないので "UNKNOWN"。"""
    if not total:  # 0 と None の両方を弾く（0除算を起こさない）
        return "UNKNOWN"
    pct = used / total * 100
    if pct >= crit_pct:
        return "CRITICAL"
    if pct >= warn_pct:
        return "WARNING"
    return "OK"


def diff_snapshot(prev, curr):
    """前回と今回のスナップショットを比べ、両方にあるキーの増減を返す。

    片方にしか無いキーは比較できないので含めない。
    prev が空（初回）なら {} を返す＝比べる相手がいない。
    """
    return {k: curr[k] - prev[k] for k in curr if k in prev}


# ── 収集（統計ビューを読むだけ。個別の失敗は UNKNOWN にして続行）────────

def check_connectivity(conn, warn_ms, crit_ms):
    started = time.monotonic()
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
        cur.fetchone()
    elapsed_ms = (time.monotonic() - started) * 1000
    status = "OK"
    if elapsed_ms >= crit_ms:
        status = "CRITICAL"
    elif elapsed_ms >= warn_ms:
        status = "WARNING"
    return {"name": "connectivity", "status": status, "value": round(elapsed_ms, 1), "unit": "ms"}


def check_uptime(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT extract(epoch FROM now() - pg_postmaster_start_time())")
        seconds = float(cur.fetchone()[0])
    # 単体では善し悪しを言えない項目。前日より短くなっていたら「再起動した」と分かる
    # （＝前日差分で気づく）。立ち上げ直後を毎回 WARNING にしても意味がないので OK のままにする。
    return {"name": "uptime", "status": "OK", "value": round(seconds / 3600, 2), "unit": "hours"}


def check_recovery(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT pg_is_in_recovery()")
        in_recovery = cur.fetchone()[0]
    return {
        "name": "recovery_state",
        "status": "OK",
        "value": "standby" if in_recovery else "primary",
    }


def check_db_size(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT pg_database_size(current_database())")
        size_bytes = int(cur.fetchone()[0])
    return {
        "name": "db_size",
        "status": "OK",  # 単体では善し悪しを言えない。前日差分で見る項目。
        "value": round(size_bytes / 1024 / 1024, 2),
        "unit": "MB",
    }


def check_disk_free(warn_pct, crit_pct, path="/"):
    """容量監視の本体はDBの外（ファイルシステム）にある。"""
    usage = shutil.disk_usage(path)
    return {
        "name": "disk_usage",
        "status": judge_ratio(usage.used, usage.total, warn_pct, crit_pct),
        "value": round(usage.used / usage.total * 100, 1),
        "unit": "%",
    }


def check_connections(conn, warn_pct, crit_pct):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT (SELECT count(*) FROM pg_stat_activity
                     WHERE backend_type = 'client backend'),
                   (SELECT setting::int FROM pg_settings WHERE name = 'max_connections')
            """
        )
        used, total = cur.fetchone()
    return {
        "name": "connections",
        "status": judge_ratio(used, total, warn_pct, crit_pct),
        "value": f"{used}/{total}",
    }


def check_long_queries(conn, seconds):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT count(*) FROM pg_stat_activity
             WHERE state = 'active'
               AND pid <> pg_backend_pid()
               AND now() - query_start > make_interval(secs => %s)
            """,
            (seconds,),
        )
        n = cur.fetchone()[0]
    return {"name": "long_queries", "status": "WARNING" if n else "OK", "value": n}


def check_idle_in_transaction(conn, seconds):
    """PostgreSQL 固有の重要項目。放置されたトランザクションは
    ロックを掴んだままVACUUMを妨げ、じわじわ効いてくる。"""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT count(*) FROM pg_stat_activity
             WHERE state = 'idle in transaction'
               AND pid <> pg_backend_pid()
               AND now() - xact_start > make_interval(secs => %s)
            """,
            (seconds,),
        )
        n = cur.fetchone()[0]
    return {"name": "idle_in_transaction", "status": "WARNING" if n else "OK", "value": n}


def check_locks(conn):
    """ロックを取らずにロックを調べる（鉄則1）。"""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT count(*) FROM pg_stat_activity
             WHERE wait_event_type = 'Lock'
               AND pid <> pg_backend_pid()
            """
        )
        n = cur.fetchone()[0]
    return {"name": "lock_waits", "status": "CRITICAL" if n else "OK", "value": n}


def check_temp_files(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT temp_files, temp_bytes FROM pg_stat_database WHERE datname = current_database()"
        )
        files, size_bytes = cur.fetchone()
    # 累積値なので、単体では意味が薄い。前日差分で見る。
    return {
        "name": "temp_files",
        "status": "OK",
        "value": int(files or 0),
        "temp_mb": round(int(size_bytes or 0) / 1024 / 1024, 2),
    }


def check_dead_tuples(conn, warn_rows):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT relname, n_dead_tup, last_autovacuum
              FROM pg_stat_user_tables
             ORDER BY n_dead_tup DESC
             LIMIT 1
            """
        )
        row = cur.fetchone()
    if not row:
        return {"name": "dead_tuples", "status": "OK", "value": 0}
    relname, dead, last_vacuum = row
    return {
        "name": "dead_tuples",
        "status": "WARNING" if dead >= warn_rows else "OK",
        "value": int(dead),
        "table": relname,
        "last_autovacuum": last_vacuum.isoformat() if last_vacuum else None,
    }


# ── 組み立て ─────────────────────────────────────────────────────────

def collect(conn, args):
    """全項目を実行。1つ失敗しても他は続行する（部分障害でも止まらない）。"""
    checks = [
        ("connectivity", lambda: check_connectivity(conn, args.conn_warn_ms, args.conn_crit_ms)),
        ("uptime", lambda: check_uptime(conn)),
        ("recovery_state", lambda: check_recovery(conn)),
        ("db_size", lambda: check_db_size(conn)),
        ("disk_usage", lambda: check_disk_free(args.warn, args.crit)),
        ("connections", lambda: check_connections(conn, args.warn, args.crit)),
        ("long_queries", lambda: check_long_queries(conn, args.slow_secs)),
        ("idle_in_transaction", lambda: check_idle_in_transaction(conn, args.slow_secs)),
        ("lock_waits", lambda: check_locks(conn)),
        ("temp_files", lambda: check_temp_files(conn)),
        ("dead_tuples", lambda: check_dead_tuples(conn, args.dead_warn)),
    ]
    results = []
    for name, fn in checks:
        try:
            results.append(fn())
        except Exception as e:
            log.warning("%s の収集に失敗: %s", name, e)
            results.append({"name": name, "status": "UNKNOWN", "value": None, "error": str(e)})
    return results


def load_snapshot(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_snapshot(path, results):
    numeric = {r["name"]: r["value"] for r in results if isinstance(r.get("value"), (int, float))}
    try:
        with open(path, "w") as f:
            json.dump(numeric, f, ensure_ascii=False, indent=2)
    except OSError as e:
        log.warning("スナップショットを保存できなかった: %s", e)


def render_text(results, overall, deltas):
    lines = []
    for r in results:
        value = "-" if r.get("value") is None else r["value"]
        unit = r.get("unit", "")
        extra = f"  ({r['error']})" if r.get("error") else ""
        delta = ""
        if r["name"] in deltas and deltas[r["name"]]:
            delta = f"  [前日比 {deltas[r['name']]:+}]"
        lines.append(f"[{r['status']:<9}] {r['name']:<20} {value}{unit}{delta}{extra}")
    lines.append(f"\n全体: {overall}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="PostgreSQL の日次点検")
    parser.add_argument("--warn", type=float, default=70, help="使用率の WARNING 閾値(%%)")
    parser.add_argument("--crit", type=float, default=90, help="使用率の CRITICAL 閾値(%%)")
    parser.add_argument("--conn-warn-ms", type=float, default=100, help="応答時間の WARNING(ms)")
    parser.add_argument("--conn-crit-ms", type=float, default=1000, help="応答時間の CRITICAL(ms)")
    parser.add_argument("--slow-secs", type=float, default=300, help="長時間とみなす秒数")
    parser.add_argument("--dead-warn", type=int, default=200, help="dead tuple の WARNING 行数")
    parser.add_argument("--snapshot", default="snapshot.local.json", help="前日比較用の保存先")
    parser.add_argument("--json", action="store_true", help="JSON で出力する")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # .env を読み込む。docker compose は .env を自分で読むが、この Python は読まない。
    # 「秘密はコードでなく .env に置く」を、compose 側とツール側の両方で同じ1ファイルから満たす。
    load_dotenv()

    dsn = os.environ.get("DB_DSN")
    if not dsn:
        log.error("DB_DSN が無い。cp .env.example .env をしたか確認する（.env の DB_DSN を読む）")
        return status_to_exit_code("UNKNOWN")

    # 秘密は出さない。マスクしてから記録する（鉄則3）。
    log.info("点検開始: %s", mask_dsn(dsn))

    prev = load_snapshot(args.snapshot)

    try:
        # 接続タイムアウトと実行タイムアウトを「両方」設定する（鉄則1）。
        # options の statement_timeout はサーバ側で重いSQLを打ち切る保険。
        with psycopg.connect(
            dsn, connect_timeout=5, options="-c statement_timeout=5000"
        ) as conn:
            conn.read_only = True  # 読み取り専用を接続レベルでも宣言する
            results = collect(conn, args)
    except Exception as e:
        log.error("接続そのものに失敗: %s", e)
        results = [{"name": "connectivity", "status": "CRITICAL", "value": None, "error": str(e)}]

    overall = worst_status([r["status"] for r in results])

    curr = {r["name"]: r["value"] for r in results if isinstance(r.get("value"), (int, float))}
    deltas = diff_snapshot(prev, curr)

    if args.json:
        print(json.dumps(
            {"overall": overall, "exit_code": status_to_exit_code(overall),
             "checks": results, "deltas": deltas},
            ensure_ascii=False, indent=2, default=str,
        ))
    else:
        print(render_text(results, overall, deltas))

    save_snapshot(args.snapshot, results)
    log.info("点検終了: %s", overall)
    return status_to_exit_code(overall)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
