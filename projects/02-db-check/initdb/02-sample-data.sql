-- 点検する相手が空っぽだと、点検している実感が湧かない。
-- 業務システムらしいテーブルを用意し、更新と削除も一度走らせておく。
-- （更新・削除をすると「不要になった行の残骸」＝dead tuple が生まれる。
--   点検項目の一つがこれを見るので、最初から観測できる状態にしておく。）

CREATE TABLE servers (
    id          SERIAL PRIMARY KEY,
    hostname    TEXT NOT NULL UNIQUE,
    role        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE health_checks (
    id          SERIAL PRIMARY KEY,
    server_id   INTEGER NOT NULL REFERENCES servers(id),
    metric      TEXT NOT NULL,
    value       NUMERIC NOT NULL,
    status      TEXT NOT NULL,
    checked_at  TIMESTAMPTZ NOT NULL DEFAULT now()
)
-- 教材の都合で、このテーブルだけ autovacuum を止めてある。
-- 既定のままだと、掃除が始まる目安が「50 + 0.2 × 行数」≒222行なのに対して、
-- 下で作る残骸は約342行。放っておくと1分ほどで掃除され、n_dead_tup が 0 になり、
-- 「点検項目10が何を見ているのか」を観測できなくなってしまう。
-- 本番でこれをやってはいけない（掃除されず、テーブルが際限なく膨らむ）。
WITH (autovacuum_enabled = false);

INSERT INTO servers (hostname, role) VALUES
    ('web-01', 'web'), ('web-02', 'web'), ('db-01', 'db'), ('batch-01', 'batch');

-- それらしい点検履歴を作る（1000行）。
INSERT INTO health_checks (server_id, metric, value, status)
SELECT
    (i % 4) + 1,
    (ARRAY['disk_usage', 'load_average', 'memory_usage'])[(i % 3) + 1],
    (random() * 100)::numeric(5, 2),
    (ARRAY['OK', 'OK', 'OK', 'WARNING', 'CRITICAL'])[(i % 5) + 1]
FROM generate_series(1, 1000) AS i;

-- 更新と削除を走らせて、dead tuple（不要になった行の残骸）を発生させる。
--   UPDATE: status='CRITICAL' の 200行 → 200
--   DELETE: id が7の倍数の   142行 → 142
--   合計およそ 342 行の残骸が、点検項目10（n_dead_tup）から観測できる。
UPDATE health_checks SET status = 'OK' WHERE status = 'CRITICAL';
DELETE FROM health_checks WHERE id % 7 = 0;

-- 統計情報を最新にしておく（点検が読むのは統計ビューなので）。
ANALYZE servers;
ANALYZE health_checks;
