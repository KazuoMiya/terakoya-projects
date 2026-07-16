# 課題2: DB日次点検ツール

毎朝の「DBは無事か」を、コマンド一発で答えられるようにする。
接続できるか、容量は伸びていないか、詰まっているセッションはいないか——
運用の現場で人が目視でやっている点検を、そのまま道具にする。

> この README が課題の「正」だ。コース本文（レッスン proj-09〜12）は、この仕様の
> 読み解きと道しるべ。迷ったら、ここに書いてある完了条件へ戻ってくればいい。

**主線は PostgreSQL。Oracle の人は、まず PostgreSQL 版を作ってから、
最後の「Oracle選択トラック」で自分の現場の言葉に翻訳する**（点検の考え方は同じだからだ）。

## 3つの鉄則（この課題でいちばん大事なこと）

点検ツールは、書き方を一つ間違えると「守るはずの本番を、自分で倒す」道具になる。
この3つは、実装しながら何度も見返してほしい。

1. **点検ツール自身が障害の原因になってはならない。**
   接続タイムアウトと実行タイムアウトを**両方**設定する（片方だけでは無限に待つ）。
   読むのは軽い統計ビューだけで、実テーブルを全件スキャンしない。
   *「監視のために本番を止めた」は、実際に起きる事故だ。*
2. **読み取り専用・最小権限。「直す」機能を混ぜない。**
   点検ユーザーに書き込み権限を渡さない。セッションを強制切断するような
   「対処」はツールに実装しない。**検知と対処は、権限も判断する人も分ける。**
   *誤検知した点検ツールが本番バッチを殺す、が典型的な事故だ。*
3. **点検結果そのものが機密になりうる。**
   実行中のSQLには個人情報がそのまま写り込むことがある。接続情報のパスワードは
   マスクしてから出す。結果を保存・共有するときの置き場所まで含めて「秘密」だ。

## 検証環境（完成品。そのまま動く）

この課題で学ぶのは**DBの点検**であって、Docker ではない。環境は用意してある。

```bash
cp .env.example .env          # 秘密は .env へ（.gitignore 済み。コミットされない）
docker compose up -d          # PostgreSQL が起動する
docker compose ps             # STATUS が healthy になるまで待つ
```

初回起動時に、点検専用の**読み取り専用ユーザー `checker`** と、点検しがいのある
サンプルデータが自動で作られる。接続情報は `.env` の `DB_DSN` にある。

```bash
# 何かおかしくなったら、この2つで最初の状態に戻せる（安全網）
docker compose down -v        # コンテナもデータも消す
docker compose up -d          # まっさらから作り直す
```

Python の準備（課題0でやった venv の中で）:

```bash
pip install -r requirements.txt   # psycopg（PostgreSQL用ドライバ）が入る
```

## 作るもの

`src/db_check.py` を、次のことができる CLI に仕上げる。

1. `.env` の `DB_DSN` で PostgreSQL に接続する（読み取り専用の `checker` で）
2. 下の**10項目**を点検し、OK/WARNING/CRITICAL/UNKNOWN を判定する
3. テキストと JSON の両方で出せる
4. 全体の状態に応じた**終了コード**で終わる（課題1と同じ 0/1/2/3）
5. 1項目が失敗しても**他の項目は続行**する
6. 接続先を**マスクして**ログに残す（鉄則3）
7. 結果を JSON で保存し、**次回に前日差分**を出せる

## 点検する10項目

「どこを見るか」は書いてある。**SQL は自分で組み立てる**——それがこの課題の本体だ。

| # | 項目 | 何を見るか | 見どころ |
|---|---|---|---|
| 1 | 接続可否・応答時間 | `SELECT 1` を投げて往復時間を測る | 繋がらない＝最優先の異常 |
| 2 | 稼働時間 | `pg_postmaster_start_time()` | 単体では善し悪しを言えない。**前日より短くなっていたら再起動している** |
| 3 | リカバリ状態 | `pg_is_in_recovery()` | primary か standby か。想定と違えば重大 |
| 4 | DBサイズ | `pg_database_size(current_database())` | 単体では善し悪しを言えない。**前日差分**で見る |
| 5 | ディスク空き | Python の `shutil.disk_usage()` | **容量監視の本体はDBの外**にある |
| 6 | 接続数 | `pg_stat_activity` の件数 ÷ `pg_settings` の `max_connections` | 使用率で見る。枯渇すると誰も繋げない |
| 7 | 長時間実行クエリ | `pg_stat_activity`（`state`, `query_start`） | 詰まりの発見。自分自身は除外する |
| 8 | idle in transaction | `pg_stat_activity`（`state`, `xact_start`） | **PostgreSQL 固有の要注意項目**。放置されたトランザクションはロックを掴んだままになる |
| 9 | ロック待ち | `pg_stat_activity`（`wait_event_type`） | **ロックを取らずにロックを調べる**（鉄則1） |
| 10 | dead tuple・最終autovacuum | `pg_stat_user_tables` | PostgreSQL 日次点検の定番。溜まると性能が落ちる |

> **初回から dead_tuples が WARNING になるのは正常だ。** サンプルデータは、更新と削除で
> 約342行の「残骸」をわざと残してある（そのテーブルだけ自動掃除も止めてある）。
> 項目10が最初から何かを言ってくれる＝**その項目が生きている証拠**だ。
> 正常なDBに「全部OK」と出るだけの点検ツールは、何も証明していない。

> **なぜ「表領域の使用率」が無いのか**（Oracle 経験者向け）
> PostgreSQL のテーブルスペースは、Oracle と違って使用率や上限を持たない
> ただのディレクトリ割り当てだ。**容量監視の本体は OS のファイルシステム側**にある。
> だから項目5でディスクを見る。概念がそのまま移らない、いい例だ。

## 自動採点が見るところ

自動採点（`tests/test_db_check.py`）がテストするのは、**DBが無くても判定できる純関数3つ**。
DBに繋ぐ部分は環境で結果が変わるので採点しない（自分で確かめる）。

| 関数 | 役割 |
|---|---|
| `mask_dsn(dsn)` | 接続文字列のパスワードを `***` に置き換える（鉄則3） |
| `judge_ratio(used, total, warn_pct, crit_pct)` | 使用率で判定。`total` が 0/None なら `UNKNOWN`（0除算で落ちない） |
| `diff_snapshot(prev, curr)` | 前回と今回を比べて増減を返す（両方に在るキーだけ） |

`worst_status` と `status_to_exit_code` は**課題1で自分が書いたもの**なので、
道具として最初から入れてある。作り直さなくていい。

## 異常を作って、検知できることを確かめる

**点検ツールは「異常を見つけられて初めて、点検ツール」だ。**
正常なDBに対して「全部OK」が出ても、それは何も証明していない。
別のターミナルをもう1枚開いて、わざと異常を作る。

```bash
# ターミナル2: わざと「idle in transaction」と「ロック待ち」を作る
docker compose exec postgres psql -U postgres -d terakoya
```

```sql
-- psql の中で（コミットせずに放置する）
BEGIN;
UPDATE servers SET role = 'web' WHERE hostname = 'web-01';
-- ここで放置。これで「idle in transaction」が1件できる。
```

この状態で `python src/db_check.py` を実行し、**項目8が拾えているか**を確かめる。
確認できたら psql に戻って `ROLLBACK;` すれば元通りだ（`\q` で抜ける）。

## 完了条件（これがそろえば課題2は修了）

- [ ] `.env` の `DB_DSN` で接続でき、**読み取り専用の `checker`** で入っている
- [ ] 10項目すべてを点検している
- [ ] **接続タイムアウトと実行タイムアウトを両方**設定している（鉄則1）
- [ ] ログに接続先が出るが、**パスワードは `***`** になっている（鉄則3）
- [ ] 「直す」処理（セッション切断など）を**実装していない**（鉄則2）
- [ ] 1項目が失敗しても全体は落ちず、その項目が UNKNOWN になる
- [ ] テキストと JSON の両方で出せる／終了コードが全体状態と一致
- [ ] 結果を JSON 保存し、2回目の実行で**前日差分**が出る
- [ ] **わざと異常を作って、検知できることを確認した**（上の節）
- [ ] 自動採点が緑（`python -m unittest -v`）
- [ ] README の「使い方」を自分の言葉で追記／`RETROSPECTIVE.md` を埋めた

## テスト

```bash
# この課題のフォルダ（projects/02-db-check）の中で
python -m unittest -v
```

## 使い方

<!-- ★ここは、あなたのツールの使い方を自分の言葉で書く。expected-output.md も見本に。 -->

```bash
python src/db_check.py --warn 70 --crit 90
python src/db_check.py --json
```

## Oracle選択トラック（任意）

現場が Oracle の人へ。**点検の考え方は同じで、見る場所の名前が違うだけ**だ。
まず PostgreSQL 版を完成させてから、この対応表で翻訳する。

| 点検項目 | PostgreSQL | Oracle |
|---|---|---|
| 接続可否 | `SELECT 1` | `SELECT 1 FROM dual` |
| インスタンス状態 | `pg_is_in_recovery()` | `v$instance`（`status`, `database_status`） |
| 稼働時間 | `pg_postmaster_start_time()` | `v$instance.startup_time` |
| 容量 | DBサイズ＋**OSのディスク** | `dba_data_files` / `dba_free_space`（**表領域**という概念がある） |
| セッション数 | `pg_stat_activity` ÷ `max_connections` | `v$session` ÷ `v$parameter` の `sessions` |
| 長時間SQL | `pg_stat_activity.query_start` | `v$session`（`status='ACTIVE'`, `last_call_et`） |
| ロック待ち | `wait_event_type='Lock'` | `v$session.blocking_session` |
| 無効オブジェクト | ほぼ概念なし（近いのは無効インデックス） | `dba_objects`（`status='INVALID'`） |
| バックアップ結果 | **DBの外**（pg_dump のログ等） | `v$rman_status` / `v$backup_set` |

**Oracle 環境を動かすなら**（重い。メモリ4GB以上・ディスク10GB程度・初回pullが巨大）:

```bash
docker compose --profile oracle up -d    # 起動に数分かかる。healthy を待つ
```

Oracle でつまずく定番:
- **古い記事につられて Instant Client を入れ始める** → `python-oracledb` の Thin モードは
  クライアントライブラリ不要。`oracledb.connect()` だけでいい。
- **接続先を間違える（ORA-12514）** → 接続先は PDB の `FREEPDB1`（`host:1521/FREEPDB1`）。
- **`v$` ビューが見えない（ORA-00942）** → 点検ユーザーに `SELECT_CATALOG_ROLE` が要る。
- **バインド変数の書き方が違う** → psycopg は `%s`、oracledb は `:name`。

## 提出（課題完了の一周）

1. 作業ブランチを切る（例: `git switch -c task2-db-check`）
2. 実装して、`python -m unittest -v` が緑になるのを確認
3. push → Pull Request → **自動採点が緑** → セルフマージ
4. `RETROSPECTIVE.md` を埋める

> **壊しても大丈夫。** DBはDockerの中の使い捨てだ。`docker compose down -v` で
> まっさらに戻せる。本物のデータは1バイトも入っていない。恐る恐る触らなくていい。
