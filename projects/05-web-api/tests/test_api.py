"""課題5の自動採点。

TestClient（サーバーを起動せずにAPIを呼べるテスト道具）で、README の仕様どおりに
振る舞うかを確かめる。DBは一時ファイルを使うので、あなたの api.db は汚さない。

このファイルは直さなくてよい。読むと「何が期待されているか」が分かる。

実行（projects/05-web-api の中で。venv に requirements.txt が入っていること）:
    python -m unittest -v

Auto-grading for Project 5.

Uses TestClient (a test tool that calls the API without starting a server)
to verify the behavior matches the README spec. The DB is a temporary file,
so your api.db stays untouched.

You do not need to edit this file. Reading it tells you what is expected.

Run (inside projects/05-web-api, with requirements.txt installed in the venv):
    python -m unittest -v
"""
import os
import sys
import tempfile
import unittest

# ── テスト用の環境を、アプリを読み込む「前に」用意する ──────────────────
# ── Prepare the test environment BEFORE importing the app ──────────────
_tmpdir = tempfile.TemporaryDirectory()
os.environ["API_DB_PATH"] = os.path.join(_tmpdir.name, "test.db")
os.environ["API_KEY"] = "test-key"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fastapi.testclient import TestClient  # noqa: E402

import app as app_module  # noqa: E402

AUTH = {"X-API-Key": "test-key"}


def make_client():
    return TestClient(app_module.app)


class TestHealth(unittest.TestCase):
    def test_health_is_ok(self):
        # 雛形の時点で緑になる1本。ここから始めよう。 / The one test that is green in the skeleton. Start here.
        with make_client() as client:
            r = client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"status": "ok"})


class TestServers(unittest.TestCase):
    def setUp(self):
        # 各テストをまっさらなDBで始める。 / Start every test with a clean DB.
        if os.path.exists(os.environ["API_DB_PATH"]):
            os.remove(os.environ["API_DB_PATH"])

    def test_create_server_returns_201_and_id(self):
        with make_client() as client:
            r = client.post("/servers", json={"hostname": "web-01", "role": "web"}, headers=AUTH)
            self.assertEqual(r.status_code, 201)
            body = r.json()
            self.assertIn("id", body)
            self.assertEqual(body["hostname"], "web-01")

    def test_create_without_api_key_is_401(self):
        with make_client() as client:
            r = client.post("/servers", json={"hostname": "web-01", "role": "web"})
            self.assertEqual(r.status_code, 401)

    def test_create_with_wrong_api_key_is_401(self):
        with make_client() as client:
            r = client.post("/servers", json={"hostname": "web-01", "role": "web"},
                            headers={"X-API-Key": "wrong"})
            self.assertEqual(r.status_code, 401)

    def test_get_does_not_require_api_key(self):
        with make_client() as client:
            client.post("/servers", json={"hostname": "web-01", "role": "web"}, headers=AUTH)
            r = client.get("/servers")
            self.assertEqual(r.status_code, 200)

    def test_missing_hostname_is_422(self):
        with make_client() as client:
            r = client.post("/servers", json={"role": "web"}, headers=AUTH)
            self.assertEqual(r.status_code, 422)

    def test_empty_hostname_is_422(self):
        with make_client() as client:
            r = client.post("/servers", json={"hostname": "", "role": "web"}, headers=AUTH)
            self.assertEqual(r.status_code, 422)

    def test_too_long_hostname_is_422(self):
        with make_client() as client:
            r = client.post("/servers", json={"hostname": "x" * 65, "role": "web"}, headers=AUTH)
            self.assertEqual(r.status_code, 422)

    def test_duplicate_hostname_is_409(self):
        with make_client() as client:
            client.post("/servers", json={"hostname": "web-01", "role": "web"}, headers=AUTH)
            r = client.post("/servers", json={"hostname": "web-01", "role": "db"}, headers=AUTH)
            self.assertEqual(r.status_code, 409)

    def test_list_servers(self):
        with make_client() as client:
            client.post("/servers", json={"hostname": "web-01", "role": "web"}, headers=AUTH)
            client.post("/servers", json={"hostname": "db-01", "role": "db"}, headers=AUTH)
            r = client.get("/servers")
            self.assertEqual(r.status_code, 200)
            hostnames = [s["hostname"] for s in r.json()]
            self.assertEqual(sorted(hostnames), ["db-01", "web-01"])

    def test_get_one_server(self):
        with make_client() as client:
            created = client.post("/servers", json={"hostname": "web-01", "role": "web"},
                                  headers=AUTH).json()
            r = client.get(f"/servers/{created['id']}")
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json()["hostname"], "web-01")

    def test_get_missing_server_is_404(self):
        with make_client() as client:
            r = client.get("/servers/9999")
            self.assertEqual(r.status_code, 404)

    def test_error_body_does_not_leak_internals(self):
        # エラーメッセージも設計のうち。内部情報（テーブル名・SQL・Traceback）を出さない。
        # Error messages are part of the design. Leak no internals (table names, SQL, tracebacks).
        with make_client() as client:
            r = client.get("/servers/9999")
            text = r.text.lower()
            for leak in ("sqlite", "traceback", "select ", "sql"):
                self.assertNotIn(leak, text)


class TestChecks(unittest.TestCase):
    def setUp(self):
        if os.path.exists(os.environ["API_DB_PATH"]):
            os.remove(os.environ["API_DB_PATH"])

    def _server(self, client):
        return client.post("/servers", json={"hostname": "web-01", "role": "web"},
                           headers=AUTH).json()

    def test_record_check_returns_201(self):
        with make_client() as client:
            s = self._server(client)
            r = client.post(f"/servers/{s['id']}/checks",
                            json={"metric": "disk_usage", "value": 42.5, "status": "OK"},
                            headers=AUTH)
            self.assertEqual(r.status_code, 201)

    def test_record_check_requires_api_key(self):
        with make_client() as client:
            s = self._server(client)
            r = client.post(f"/servers/{s['id']}/checks",
                            json={"metric": "disk_usage", "value": 42.5, "status": "OK"})
            self.assertEqual(r.status_code, 401)

    def test_record_check_for_missing_server_is_404(self):
        with make_client() as client:
            r = client.post("/servers/9999/checks",
                            json={"metric": "disk_usage", "value": 42.5, "status": "OK"},
                            headers=AUTH)
            self.assertEqual(r.status_code, 404)

    def test_invalid_status_is_422(self):
        # 状態は課題1から使ってきた4値だけ。それ以外は入口で弾く。
        # Only the four statuses used since Project 1. Reject everything else at the door.
        with make_client() as client:
            s = self._server(client)
            r = client.post(f"/servers/{s['id']}/checks",
                            json={"metric": "disk_usage", "value": 42.5, "status": "BROKEN"},
                            headers=AUTH)
            self.assertEqual(r.status_code, 422)

    def test_unknown_status_is_allowed(self):
        with make_client() as client:
            s = self._server(client)
            r = client.post(f"/servers/{s['id']}/checks",
                            json={"metric": "log_errors", "value": 0, "status": "UNKNOWN"},
                            headers=AUTH)
            self.assertEqual(r.status_code, 201)

    def test_non_numeric_value_is_422(self):
        with make_client() as client:
            s = self._server(client)
            r = client.post(f"/servers/{s['id']}/checks",
                            json={"metric": "disk_usage", "value": "たくさん", "status": "OK"},
                            headers=AUTH)
            self.assertEqual(r.status_code, 422)

    def test_list_checks_newest_first(self):
        with make_client() as client:
            s = self._server(client)
            for i, status in enumerate(["OK", "WARNING", "CRITICAL"]):
                client.post(f"/servers/{s['id']}/checks",
                            json={"metric": "disk_usage", "value": 40 + i, "status": status},
                            headers=AUTH)
            r = client.get(f"/servers/{s['id']}/checks")
            self.assertEqual(r.status_code, 200)
            statuses = [c["status"] for c in r.json()]
            self.assertEqual(statuses[0], "CRITICAL")  # 最新が先頭 / newest first

    def test_list_checks_respects_limit(self):
        with make_client() as client:
            s = self._server(client)
            for i in range(5):
                client.post(f"/servers/{s['id']}/checks",
                            json={"metric": "disk_usage", "value": i, "status": "OK"},
                            headers=AUTH)
            r = client.get(f"/servers/{s['id']}/checks?limit=2")
            self.assertEqual(len(r.json()), 2)

    def test_list_checks_for_missing_server_is_404(self):
        with make_client() as client:
            r = client.get("/servers/9999/checks")
            self.assertEqual(r.status_code, 404)


if __name__ == "__main__":
    unittest.main()
