#!/bin/bash
# 初回起動時に一度だけ実行される（docker compose down -v で消せば、また実行される）。
# 点検専用の「読み取り専用ユーザー」を作る。これは現場の作法そのものだ——
# 点検に書き込み権限は要らない。要らない権限は最初から渡さない（最小権限）。
set -e

# パスワードは -v で psql の変数として渡し、SQL 側は :'名前' で受ける。
# ヒアドキュメントを 'EOSQL' とクォートして bash の展開を止めているのがポイント。
# こうすると引用符の処理を psql に任せられるので、パスワードに ' や \ が入っても壊れない。
# （SQL文字列に値を直接埋め込まない、という課題1〜2で通した原則の実物だ。）
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
     -v checker_password="$CHECKER_PASSWORD" \
     -v db_name="$POSTGRES_DB" <<-'EOSQL'
    -- 点検専用ユーザー。パスワードは環境変数から（スクリプトに直書きしない）。
    CREATE ROLE checker LOGIN PASSWORD :'checker_password';

    -- pg_monitor: 監視のための「読む権限」の詰め合わせ（PostgreSQL 10 以降の組み込みロール）。
    -- 中身は pg_read_all_settings / pg_read_all_stats / pg_stat_scan_tables の3つ。
    -- これが無いと、pg_stat_activity の query 列が他人のセッションでは NULL になり、
    -- 「SQLは通るのに中身が見えない」という分かりにくい詰まり方をする。
    GRANT pg_monitor TO checker;

    -- このデータベースに接続してよい、という許可。
    GRANT CONNECT ON DATABASE :"db_name" TO checker;

    -- PostgreSQL 15 以降、public スキーマから PUBLIC の CREATE 権限は外れたが、
    -- USAGE は誰にでも残っている。なのでこの行は厳密には冗長だが、意図を明示するために書く。
    GRANT USAGE ON SCHEMA public TO checker;

    -- ON ALL TABLES は「今この瞬間に在るテーブル」への一括GRANT。
    -- このスクリプト(01)は 02-sample-data.sql より先に走るので、ここではまだテーブルは0件——
    -- つまりこの行は、いま何も付与していない。手でテーブルを足したときのために残してある。
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO checker;

    -- 実際に効いているのはこちら。「これから postgres が作るテーブル」に SELECT を予約する。
    -- 02-sample-data.sql も postgres が実行するので、サンプルのテーブルはこれで拾われる。
    -- 既存のテーブルには遡らない。順序が逆だったら checker は何も読めなかった。
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO checker;
EOSQL

echo "checker ロールを作成した（読み取り専用 + pg_monitor）"
