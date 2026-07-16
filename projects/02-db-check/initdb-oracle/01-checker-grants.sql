-- Oracle選択トラック用。初回起動時に一度だけ実行される。
-- （主線は PostgreSQL。このファイルは --profile oracle で起動した人にだけ効く。）
--
-- checker ユーザー自体は、コンテナが APP_USER/APP_USER_PASSWORD から作ってくれる。
-- ここで足すのは「点検に必要な、読む権限」だけだ。

-- v$ ビュー（v$instance, v$session など）を読むための権限。
-- これが無いと、点検SQLが ORA-00942（表またはビューが存在しません）で落ちる。
-- 一般ユーザーには最初から見えない、というのが Oracle の作法。
GRANT SELECT_CATALOG_ROLE TO checker;

-- 接続と、自分のセッションを見るための最低限。
GRANT CREATE SESSION TO checker;

-- 注意: 点検に書き込み権限は渡さない（鉄則2）。
-- ALTER SYSTEM KILL SESSION のような「対処」の権限も渡さない。
