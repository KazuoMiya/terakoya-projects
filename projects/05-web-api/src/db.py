"""課題5: DBアクセス層（あなたが実装する）。

SQLを書く場所を、このファイル1つに閉じ込める。app.py にはSQLを1行も書かない。

なぜ分けるのか。この課題の最後に「SQLite → PostgreSQL 差し替え」という挑戦が
待っているからだ。SQLがあちこちに散らばっていると、差し替えは全ファイル改修になる。
1モジュールに閉じてあれば、取り替えるのはこのファイルだけで済む。
（課題2で点検を「1項目＝1関数」に揃えたのと同じ、差し替えられる設計だ。）

DBファイルの場所は環境変数 API_DB_PATH（無ければ "api.db"）。
採点テストはこの変数に一時ファイルを指定して、あなたの本物のDBを汚さずに検査する。

テーブル定義（init_db）は仕様で決まっているので、最初から実装してある。
あなたが書くのは、その下の6つの関数だ。

Project 5: DB access layer (you implement this).

All SQL lives in this one file. Not a single line of SQL goes into app.py.

Why the split? Because the challenge waiting at the end of this project is
"swap SQLite for PostgreSQL." If SQL is scattered everywhere, the swap means
rewriting every file. Confined to one module, the only thing you replace is
this file. (It is the same swappable design as Project 2, where each check
became "one item = one function.")

The DB file location comes from the environment variable API_DB_PATH
(default "api.db"). The grading tests point this variable at a temporary
file, so they never touch your real DB.

The table definitions (init_db) are fixed by the spec, so they are already
implemented. What you write is the six functions below them.
"""
import os
import sqlite3

DB_PATH = os.environ.get("API_DB_PATH", "api.db")


def connect():
    """接続を作る。行を辞書風に読めるようにしておくと後が楽だ。

    Create a connection. Making rows readable like dicts pays off later.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # 外部キー制約は SQLite では既定でオフ。オンにする（存在しない server_id を弾く）。
    # Foreign keys are off by default in SQLite. Turn them on (rejects nonexistent server_id).
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """テーブルが無ければ作る（何度呼んでも安全＝冪等）。実装済み——これが仕様の形だ。

    Create the tables if absent (safe to call any number of times = idempotent).
    Already implemented — this is the shape the spec requires.
    """
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS servers (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                hostname TEXT NOT NULL UNIQUE,
                role     TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS health_checks (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id  INTEGER NOT NULL REFERENCES servers(id),
                metric     TEXT NOT NULL,
                value      REAL NOT NULL,
                status     TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


# ── ここから下を実装する（★TODO★）─────────────────────────────────────
# ── Implement everything below this line (★TODO★) ─────────────────────
# 注意: SQLの値の埋め込みは必ずプレースホルダ（?）で。f文字列で組み立てない。
# Note: always embed SQL values with placeholders (?). Never build SQL with f-strings.

def insert_server(hostname, role):
    """サーバーを登録して、新しい id を返す。

    ヒント: with connect() as conn: で cursor = conn.execute("INSERT ...", (値,))
           新しい id は cursor.lastrowid にある。

    Register a server and return the new id.

    Hint: inside with connect() as conn: use cursor = conn.execute("INSERT ...", (values,))
          The new id is in cursor.lastrowid.
    """
    raise NotImplementedError(
        "insert_server を実装しよう（課題5の道しるべ参照） / Implement insert_server (see the Project 5 guide)"
    )


def get_server(server_id):
    """id で1件取る。無ければ None。あれば dict(row) で辞書にして返すと扱いやすい。

    Fetch one row by id. None if missing. If found, returning dict(row) makes it easy to handle.
    """
    raise NotImplementedError("get_server を実装しよう / Implement get_server")


def get_server_by_hostname(hostname):
    """hostname で1件取る。無ければ None（登録時の重複チェックに使う）。

    Fetch one row by hostname. None if missing (used for the duplicate check at registration).
    """
    raise NotImplementedError("get_server_by_hostname を実装しよう / Implement get_server_by_hostname")


def list_servers():
    """全サーバーを id 順の一覧（辞書のリスト）で返す。

    Return all servers ordered by id, as a list of dicts.
    """
    raise NotImplementedError("list_servers を実装しよう / Implement list_servers")


def insert_check(server_id, metric, value, status):
    """点検結果を1件記録して、新しい id を返す。

    Record one check result and return the new id.
    """
    raise NotImplementedError("insert_check を実装しよう / Implement insert_check")


def list_checks(server_id, limit=20):
    """そのサーバーの点検結果を新しい順（id の降順）に limit 件返す。

    Return that server's check results, newest first (id descending), up to limit rows.
    """
    raise NotImplementedError("list_checks を実装しよう / Implement list_checks")
