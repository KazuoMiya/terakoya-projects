#!/bin/bash
# 課題6: バックアップスクリプト。
# Project 6: backup script.
#
# 使い方:  bash deploy/backup.sh <api.dbのパス> <バックアップ置き場>
# 例:      bash deploy/backup.sh ../05-web-api/api.db ~/backups
# Usage:   bash deploy/backup.sh <path to api.db> <backup dir>
# Example: bash deploy/backup.sh ../05-web-api/api.db ~/backups
#
# ポイントは2つ。
#   1. ただの cp ではなく sqlite3 の .backup を使う。動いているDBを cp すると
#      書き込み途中の壊れたコピーを掴むことがある。.backup は安全に写す公式の方法だ。
#   2. バックアップは「リストアに成功して初めてバックアップ」。このスクリプトを
#      動かして満足せず、README のリストア演習まで必ずやること。
# Two points.
#   1. Use sqlite3's .backup, not a plain cp. cp on a live DB can grab a
#      corrupted mid-write copy. .backup is the official way to copy safely.
#   2. A backup only counts once a restore succeeds. Don't stop at running
#      this script — always go on to the restore drill in the README.
set -euo pipefail

DB_PATH="${1:?使い方 / Usage: bash deploy/backup.sh <api.dbのパス / path to api.db> <バックアップ置き場 / backup dir>}"
BACKUP_DIR="${2:?バックアップ置き場も指定すること / Specify the backup dir too}"

if [ ! -f "$DB_PATH" ]; then
    echo "エラー: DBファイルが見つからない / Error: DB file not found: $DB_PATH" >&2
    exit 1
fi

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
DEST="$BACKUP_DIR/api-$STAMP.db"

# 動いているDBでも安全に写せる、SQLite公式のバックアップ命令。
# SQLite's official backup command — copies safely even while the DB is live.
sqlite3 "$DB_PATH" ".backup '$DEST'"

# 写せたことを最低限確かめる（サイズ0のバックアップは事故のもと）。
# Minimal sanity check that the copy exists (a zero-byte backup is an accident waiting to happen).
if [ ! -s "$DEST" ]; then
    echo "エラー: バックアップが空だ / Error: backup is empty: $DEST" >&2
    exit 1
fi

echo "バックアップ完了 / Backup complete: $DEST ($(wc -c < "$DEST" | tr -d ' ') bytes)"
echo "次は「リストア演習」——戻せることを確かめて、初めてバックアップだ。 / Next: the restore drill — only when you can restore does it count as a backup."
