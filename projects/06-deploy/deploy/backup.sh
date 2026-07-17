#!/bin/bash
# 課題6: バックアップスクリプト。
#
# 使い方:  bash deploy/backup.sh <api.dbのパス> <バックアップ置き場>
# 例:      bash deploy/backup.sh ../05-web-api/api.db ~/backups
#
# ポイントは2つ。
#   1. ただの cp ではなく sqlite3 の .backup を使う。動いているDBを cp すると
#      書き込み途中の壊れたコピーを掴むことがある。.backup は安全に写す公式の方法だ。
#   2. バックアップは「リストアに成功して初めてバックアップ」。このスクリプトを
#      動かして満足せず、README のリストア演習まで必ずやること。
set -euo pipefail

DB_PATH="${1:?使い方: bash deploy/backup.sh <api.dbのパス> <バックアップ置き場>}"
BACKUP_DIR="${2:?バックアップ置き場も指定すること}"

if [ ! -f "$DB_PATH" ]; then
    echo "エラー: DBファイルが見つからない: $DB_PATH" >&2
    exit 1
fi

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
DEST="$BACKUP_DIR/api-$STAMP.db"

# 動いているDBでも安全に写せる、SQLite公式のバックアップ命令。
sqlite3 "$DB_PATH" ".backup '$DEST'"

# 写せたことを最低限確かめる（サイズ0のバックアップは事故のもと）。
if [ ! -s "$DEST" ]; then
    echo "エラー: バックアップが空だ: $DEST" >&2
    exit 1
fi

echo "バックアップ完了: $DEST ($(wc -c < "$DEST" | tr -d ' ') bytes)"
echo "次は「リストア演習」——戻せることを確かめて、初めてバックアップだ。"
