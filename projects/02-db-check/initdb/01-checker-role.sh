#!/bin/bash
# 初回起動時に一度だけ実行される（docker compose down -v で消せば、また実行される）。
# Runs only once, at the first startup (wipe with docker compose down -v and it runs again).
# 点検専用の「読み取り専用ユーザー」を作る。これは現場の作法そのものだ——
# 点検に書き込み権限は要らない。要らない権限は最初から渡さない（最小権限）。
# Creates the read-only user dedicated to inspections. This is exactly how the
# field works — inspections need no write access. Permissions that are not
# needed are never handed out in the first place (least privilege).
set -e

# パスワードは -v で psql の変数として渡し、SQL 側は :'名前' で受ける。
# The password is passed to psql as a variable with -v, and the SQL side receives it as :'name'.
# ヒアドキュメントを 'EOSQL' とクォートして bash の展開を止めているのがポイント。
# The key point: quoting the heredoc as 'EOSQL' stops bash expansion.
# こうすると引用符の処理を psql に任せられるので、パスワードに ' や \ が入っても壊れない。
# That leaves quote handling to psql, so a password containing ' or \ breaks nothing.
# （SQL文字列に値を直接埋め込まない、という課題1〜2で通した原則の実物だ。）
# (This is the real-life form of the principle held through Assignments 1-2:
# never embed values directly into SQL strings.)
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
     -v checker_password="$CHECKER_PASSWORD" \
     -v db_name="$POSTGRES_DB" <<-'EOSQL'
    -- 点検専用ユーザー。パスワードは環境変数から（スクリプトに直書きしない）。
    -- The inspection-only user. Its password comes from an environment variable
    -- (never hard-coded in the script).
    CREATE ROLE checker LOGIN PASSWORD :'checker_password';

    -- pg_monitor: 監視のための「読む権限」の詰め合わせ（PostgreSQL 10 以降の組み込みロール）。
    -- 中身は pg_read_all_settings / pg_read_all_stats / pg_stat_scan_tables の3つ。
    -- これが無いと、pg_stat_activity の query 列が他人のセッションでは NULL になり、
    -- 「SQLは通るのに中身が見えない」という分かりにくい詰まり方をする。
    -- pg_monitor: a bundle of "read permissions" for monitoring (a built-in role
    -- since PostgreSQL 10). It contains pg_read_all_settings / pg_read_all_stats
    -- / pg_stat_scan_tables. Without it, the query column of pg_stat_activity is
    -- NULL for other people's sessions, and you hit the confusing dead end of
    -- "the SQL runs, but you cannot see the contents".
    GRANT pg_monitor TO checker;

    -- このデータベースに接続してよい、という許可。
    -- Permission saying: you may connect to this database.
    GRANT CONNECT ON DATABASE :"db_name" TO checker;

    -- PostgreSQL 15 以降、public スキーマから PUBLIC の CREATE 権限は外れたが、
    -- USAGE は誰にでも残っている。なのでこの行は厳密には冗長だが、意図を明示するために書く。
    -- Since PostgreSQL 15, PUBLIC has lost CREATE on the public schema, but USAGE
    -- still remains for everyone. Strictly speaking this line is redundant, but
    -- it is written to make the intent explicit.
    GRANT USAGE ON SCHEMA public TO checker;

    -- ON ALL TABLES は「今この瞬間に在るテーブル」への一括GRANT。
    -- このスクリプト(01)は 02-sample-data.sql より先に走るので、ここではまだテーブルは0件——
    -- つまりこの行は、いま何も付与していない。手でテーブルを足したときのために残してある。
    -- ON ALL TABLES is a bulk GRANT on "the tables that exist at this very moment".
    -- This script (01) runs before 02-sample-data.sql, so there are still zero
    -- tables here — meaning this line grants nothing right now. It is kept for
    -- when you add tables by hand.
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO checker;

    -- 実際に効いているのはこちら。「これから postgres が作るテーブル」に SELECT を予約する。
    -- 02-sample-data.sql も postgres が実行するので、サンプルのテーブルはこれで拾われる。
    -- 既存のテーブルには遡らない。順序が逆だったら checker は何も読めなかった。
    -- This is the one that actually takes effect: it reserves SELECT on "tables
    -- postgres will create from now on". 02-sample-data.sql also runs as
    -- postgres, so the sample tables are picked up by this. It does not reach
    -- back to existing tables. If the order were reversed, checker could read nothing.
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO checker;
EOSQL

echo "checker ロールを作成した（読み取り専用 + pg_monitor） / Created the checker role (read-only + pg_monitor)"
