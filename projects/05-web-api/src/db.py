"""課題5: DBアクセス層 — 参考実装（solutions ブランチ）。"""
import os
import sqlite3

DB_PATH = os.environ.get("API_DB_PATH", "api.db")


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
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


def insert_server(hostname, role):
    with connect() as conn:
        cursor = conn.execute(
            "INSERT INTO servers (hostname, role) VALUES (?, ?)", (hostname, role)
        )
        return cursor.lastrowid


def get_server(server_id):
    with connect() as conn:
        row = conn.execute("SELECT * FROM servers WHERE id = ?", (server_id,)).fetchone()
    return dict(row) if row else None


def get_server_by_hostname(hostname):
    with connect() as conn:
        row = conn.execute("SELECT * FROM servers WHERE hostname = ?", (hostname,)).fetchone()
    return dict(row) if row else None


def list_servers():
    with connect() as conn:
        rows = conn.execute("SELECT * FROM servers ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def insert_check(server_id, metric, value, status):
    with connect() as conn:
        cursor = conn.execute(
            "INSERT INTO health_checks (server_id, metric, value, status) VALUES (?, ?, ?, ?)",
            (server_id, metric, value, status),
        )
        return cursor.lastrowid


def list_checks(server_id, limit=20):
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM health_checks WHERE server_id = ? ORDER BY id DESC LIMIT ?",
            (server_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]
