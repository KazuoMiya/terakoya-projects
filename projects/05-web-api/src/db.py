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
"""
import os
import sqlite3

DB_PATH = os.environ.get("API_DB_PATH", "api.db")


def connect():
    """接続を作る。行を辞書風に読めるようにしておくと後が楽だ。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # 外部キー制約は SQLite では既定でオフ。オンにする（存在しない server_id を弾く）。
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """テーブルが無ければ作る（何度呼んでも安全＝冪等）。実装済み——これが仕様の形だ。"""
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
# 注意: SQLの値の埋め込みは必ずプレースホルダ（?）で。f文字列で組み立てない。

def insert_server(hostname, role):
    """サーバーを登録して、新しい id を返す。

    ヒント: with connect() as conn: で cursor = conn.execute("INSERT ...", (値,))
           新しい id は cursor.lastrowid にある。
    """
    raise NotImplementedError("insert_server を実装しよう（課題5の道しるべ参照）")


def get_server(server_id):
    """id で1件取る。無ければ None。あれば dict(row) で辞書にして返すと扱いやすい。"""
    raise NotImplementedError("get_server を実装しよう")


def get_server_by_hostname(hostname):
    """hostname で1件取る。無ければ None（登録時の重複チェックに使う）。"""
    raise NotImplementedError("get_server_by_hostname を実装しよう")


def list_servers():
    """全サーバーを id 順の一覧（辞書のリスト）で返す。"""
    raise NotImplementedError("list_servers を実装しよう")


def insert_check(server_id, metric, value, status):
    """点検結果を1件記録して、新しい id を返す。"""
    raise NotImplementedError("insert_check を実装しよう")


def list_checks(server_id, limit=20):
    """そのサーバーの点検結果を新しい順（id の降順）に limit 件返す。"""
    raise NotImplementedError("list_checks を実装しよう")
