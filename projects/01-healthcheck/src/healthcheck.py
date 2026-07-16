#!/usr/bin/env python3
"""課題1: サーバーヘルスチェックCLI（あなたが実装する）。

このファイルの ★TODO★ を実装すると、自動採点（tests/）が緑になる。
自動採点が見るのは、下の「純関数」3つ——つまり "判定" の部分だ。
判定は OS に依存しないので、テストできる。ここを最初に固める。

収集（subprocess で df / uptime などを叩く）・表示（テキスト/JSON）・
argparse・logging・main() は、コース本文（課題1の道しるべ）を読みながら
自分で組み上げていく。困ったら solutions ブランチに参考実装がある。

状態は4つ:
    "OK"       正常
    "WARNING"  注意（warn 以上 crit 未満）
    "CRITICAL" 危険（crit 以上）
    "UNKNOWN"  そもそも測れなかった（コマンド失敗など）

終了コードは監視の世界の共通語（Nagios 互換）:
    OK=0  WARNING=1  CRITICAL=2  UNKNOWN=3
"""
import sys


# ── 純関数（★TODO★：ここを実装する。自動採点の対象）─────────────────

def judge(value, warn, crit):
    """値を閾値と比べて "OK"/"WARNING"/"CRITICAL" を返す。

    値は「大きいほど悪い」もの（ディスク使用率%・CPU%・ロードアベレージ等）を想定。
    - value が crit 以上         → "CRITICAL"
    - value が warn 以上 crit 未満 → "WARNING"
    - それ未満                   → "OK"
    （境界は「以上」で含める。例: warn=70 のとき 70 は WARNING）
    """
    raise NotImplementedError("judge を実装しよう（課題1の道しるべ参照）")


def worst_status(statuses):
    """複数チェックの状態リストから、全体の状態（いちばん深刻なもの）を返す。

    深刻さの順: CRITICAL > WARNING > UNKNOWN > OK
    - 1つでも "CRITICAL" があれば "CRITICAL"
    - なければ "WARNING" があれば "WARNING"
    - なければ "UNKNOWN" があれば "UNKNOWN"
    - すべて "OK" なら "OK"
    - 空のリスト（何も測れなかった）なら "UNKNOWN"

    ポイント: 「危険(CRITICAL/WARNING)」と「測れない(UNKNOWN)」を混ぜない。
    UNKNOWN が勝手に CRITICAL に化けてはいけない。
    """
    raise NotImplementedError("worst_status を実装しよう")


def status_to_exit_code(status):
    """状態の文字列を終了コードに変換する。

    "OK"→0  "WARNING"→1  "CRITICAL"→2  "UNKNOWN"→3
    """
    raise NotImplementedError("status_to_exit_code を実装しよう")


# ── 収集・表示・main（自分で組み上げる。自動採点の対象外）──────────────
# ヒントは課題1の道しるべ（レッスン proj-07）にある。
# 収集の失敗は UNKNOWN にして、他のチェックは続行する（部分障害でも全体を止めない）。

def main(argv=None):
    """CLI 本体。argparse で閾値を受け取り、収集→判定→表示し、終了コードを返す。"""
    # ★TODO★ 課題1の道しるべに沿って組み上げる。
    raise NotImplementedError("main を実装しよう")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
