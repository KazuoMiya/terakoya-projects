#!/usr/bin/env python3
"""発展課題: dry-run 既定の掃除ツール — 参考実装（solutions ブランチ）。

このコース初の「変更系」ツール。鉄則は3つ:
    消す前に見せる。既定では消さない。消したら記録する。

使い方:
    python src/cleanup.py /tmp/cleanup-practice --days 30            # dry-run（何も消さない）
    python src/cleanup.py /tmp/cleanup-practice --days 30 --execute # 本当に消す
"""
import argparse
import logging
import os
import sys
import time

from config_diff import select_old_files  # 「選ぶ」は採点済みの純関数に任せる

log = logging.getLogger("cleanup")


def list_files(directory):
    """directory 直下のファイルを (パス, 最終更新エポック秒) の一覧にする。"""
    entries = []
    for name in os.listdir(directory):
        path = os.path.join(directory, name)
        if os.path.isfile(path):
            entries.append((path, os.path.getmtime(path)))
    return entries


def main(argv=None):
    parser = argparse.ArgumentParser(description="古いファイルの掃除（既定は dry-run）")
    parser.add_argument("directory", help="掃除する対象のフォルダ")
    parser.add_argument("--days", type=int, default=30, help="この日数以上前のファイルが対象")
    parser.add_argument("--execute", action="store_true",
                        help="本当に削除する（付けなければ一覧表示だけ）")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if not os.path.isdir(args.directory):
        log.error("フォルダが無い: %s", args.directory)
        return 3

    # 選ぶ（何度実行しても安全）と、消す（一度きり）を分ける。
    entries = list_files(args.directory)
    targets = select_old_files(entries, days=args.days, now_epoch=time.time())

    if not targets:
        print("消すものなし。")  # 冪等: 2回目はここで正常終了する
        return 0

    # 鉄則1: 消す前に見せる。
    mode = "" if args.execute else "[dry-run] "
    print(f"{mode}消す候補 {len(targets)}件" + ("" if args.execute else "（実際には消していない）") + ":")
    for path in targets:
        print(f"  {path}")

    # 鉄則2: 既定では消さない。
    if not args.execute:
        print("本当に消すには --execute を付ける。")
        return 0

    # 鉄則3: 消したら記録する。
    for path in targets:
        os.remove(path)
        log.info("削除した: %s", path)
    print(f"{len(targets)}件を削除した。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
