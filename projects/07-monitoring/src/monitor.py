#!/usr/bin/env python3
"""最終課題: 統合監視システム — 参考実装（solutions ブランチ）。

これは「答え」だ。詰まったときの安全網として置いてある。
まず自分で書いてみて、どうしても進めないところだけ覗くのがおすすめ。
"""
import argparse
import json
import logging
import shutil
import sys
import time

import requests
from dotenv import load_dotenv
import os

log = logging.getLogger("monitor")

_SEVERITY = {"OK": 0, "UNKNOWN": 1, "WARNING": 2, "CRITICAL": 3}


def worst_status(statuses):
    if not statuses:
        return "UNKNOWN"
    return max(statuses, key=lambda s: _SEVERITY.get(s, 1))


def status_to_exit_code(status):
    return {"OK": 0, "WARNING": 1, "CRITICAL": 2, "UNKNOWN": 3}.get(status, 3)


# ── 純関数（自動採点の対象）──────────────────────────────────────────

def parse_config(config):
    """設定を検証して (interval_seconds, 監視対象のリスト) を返す。"""
    interval = config.get("interval_seconds")
    if not isinstance(interval, (int, float)) or interval <= 0:
        raise ValueError("interval_seconds は 0 より大きい数にすること")

    targets = config.get("targets")
    if not isinstance(targets, list) or not targets:
        raise ValueError("targets には監視対象を1件以上書くこと")

    normalized = []
    for t in targets:
        name = t.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("name の無い対象がある（すべての対象に名前を付けること）")
        kind = t.get("type")
        if kind not in ("http", "disk"):
            raise ValueError(f"対象 {name}: type が不正です（http か disk）")
        out = dict(t)
        if kind == "http":
            url = t.get("url")
            if not isinstance(url, str) or not url.startswith(("http://", "https://")):
                raise ValueError(f"対象 {name}: url は http:// か https:// で始めること")
            out.setdefault("warn_ms", 500)
            out.setdefault("crit_ms", 2000)
        else:
            if not t.get("path"):
                raise ValueError(f"対象 {name}: disk には path が必要です")
            out.setdefault("warn", 70)
            out.setdefault("crit", 90)
        normalized.append(out)
    return interval, normalized


def judge_http(status_code, elapsed_ms, warn_ms, crit_ms):
    """HTTPチェックの判定。繋がらない・200以外は CRITICAL、あとは応答時間で。"""
    if status_code is None:
        return "CRITICAL"
    if status_code != 200:
        return "CRITICAL"
    if elapsed_ms >= crit_ms:
        return "CRITICAL"
    if elapsed_ms >= warn_ms:
        return "WARNING"
    return "OK"


def should_alert(prev_status, curr_status):
    """状態が変わったときだけ声を上げる（悪化も回復も）。同じ状態では黙る。"""
    if prev_status is None:
        return curr_status != "OK"
    return prev_status != curr_status


# ── チェック（対象の障害は結果として返す。例外にしない）────────────────

def check_http(target):
    """URLを叩いて応答コードと時間を測る。繋がらなければ status_code=None。"""
    started = time.monotonic()
    try:
        resp = requests.get(target["url"], timeout=5)
        elapsed_ms = (time.monotonic() - started) * 1000
        status = judge_http(resp.status_code, elapsed_ms, target["warn_ms"], target["crit_ms"])
        return {"metric": "http_health", "value": round(elapsed_ms, 1), "status": status}
    except requests.RequestException:
        return {"metric": "http_health", "value": 0, "status": judge_http(None, None, 0, 0)}


def check_disk(target):
    """ディスク使用率（課題2で使った shutil.disk_usage の再利用）。"""
    try:
        usage = shutil.disk_usage(target["path"])
        pct = usage.used / usage.total * 100
        if pct >= target["crit"]:
            status = "CRITICAL"
        elif pct >= target["warn"]:
            status = "WARNING"
        else:
            status = "OK"
        return {"metric": "disk_usage", "value": round(pct, 1), "status": status}
    except OSError:
        return {"metric": "disk_usage", "value": 0, "status": "UNKNOWN"}


CHECKERS = {"http": check_http, "disk": check_disk}


# ── 記録（課題5のAPIへ。失敗しても監視は止めない）──────────────────────

class Recorder:
    """課題5のAPIに結果を送る係。サーバーIDは初回に登録して覚えておく。"""

    def __init__(self, api_base, api_key):
        self.api_base = api_base.rstrip("/")
        self.headers = {"X-API-Key": api_key}
        self._ids = {}

    def _server_id(self, name):
        if name in self._ids:
            return self._ids[name]
        # 登録を試みる。既に居れば(409)一覧から探す。
        resp = requests.post(f"{self.api_base}/servers",
                             json={"hostname": name, "role": "monitored"},
                             headers=self.headers, timeout=5)
        if resp.status_code == 201:
            self._ids[name] = resp.json()["id"]
        elif resp.status_code == 409:
            for server in requests.get(f"{self.api_base}/servers", timeout=5).json():
                if server["hostname"] == name:
                    self._ids[name] = server["id"]
                    break
        if name not in self._ids:
            raise RuntimeError(f"サーバー {name} を登録できなかった")
        return self._ids[name]

    def record(self, name, result):
        server_id = self._server_id(name)
        resp = requests.post(f"{self.api_base}/servers/{server_id}/checks",
                             json=result, headers=self.headers, timeout=5)
        resp.raise_for_status()


# ── ループ ───────────────────────────────────────────────────────────

def run_cycle(targets, recorder, prev_statuses):
    """全対象を1周チェックして記録する。対象1件の失敗で全体を止めない。"""
    statuses = []
    for target in targets:
        name = target["name"]
        result = CHECKERS[target["type"]](target)
        statuses.append(result["status"])

        if should_alert(prev_statuses.get(name), result["status"]):
            log.warning("%s が %s になった (%s=%s)",
                        name, result["status"], result["metric"], result["value"])
        prev_statuses[name] = result["status"]

        # 記録の失敗は「監視自身の障害」。対象の障害と混ぜず、ログに残して続行する。
        try:
            recorder.record(name, result)
        except Exception as e:
            log.error("%s の結果を記録できなかった（監視は続ける）: %s", name, e)
    return statuses


def main(argv=None):
    parser = argparse.ArgumentParser(description="統合監視: 定期チェックとAPIへの記録")
    parser.add_argument("--config", default="config.json", help="設定ファイル")
    parser.add_argument("--once", action="store_true", help="1周だけ実行して終わる")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_dotenv()

    try:
        with open(args.config) as f:
            config = json.load(f)
        interval, targets = parse_config(config)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        log.error("設定が読めない: %s", e)
        return status_to_exit_code("UNKNOWN")

    api_base = config.get("api_base", "http://127.0.0.1:8000")
    recorder = Recorder(api_base, os.environ.get("API_KEY", ""))

    prev_statuses = {}
    log.info("監視開始: %d対象 / %s秒間隔 / 記録先 %s", len(targets), interval, api_base)
    while True:
        statuses = run_cycle(targets, recorder, prev_statuses)
        if args.once:
            return status_to_exit_code(worst_status(statuses))
        time.sleep(interval)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
