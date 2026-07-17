"""課題4の自動採点。

差分エンジンの純関数4つ（normalize / diff_config / judge_diff / select_old_files）を
確かめる。収集（OSコマンド）は環境で結果が変わるので、ここでは採点しない
（samples/ の2ファイルと expected-output.md で自分で確かめる）。

このファイルは直さなくてよい。読むと「何が期待されているか」が分かる。

実行（projects/04-config-diff の中で）:
    python -m unittest -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import config_diff  # noqa: E402


class TestNormalize(unittest.TestCase):
    def test_drops_volatile_keys(self):
        out = config_diff.normalize({"collected_at": "2026-07-16 06:00", "users": ["root"]})
        self.assertNotIn("collected_at", out)
        self.assertIn("users", out)

    def test_sorts_lists(self):
        out = config_diff.normalize({"users": ["root", "deploy", "www-data"]})
        self.assertEqual(out["users"], ["deploy", "root", "www-data"])

    def test_does_not_mutate_input(self):
        snap = {"collected_at": "x", "ports": [80, 22]}
        config_diff.normalize(snap)
        self.assertEqual(snap, {"collected_at": "x", "ports": [80, 22]})

    def test_non_list_values_pass_through(self):
        out = config_diff.normalize({"hostname": "web-01"})
        self.assertEqual(out["hostname"], "web-01")


class TestDiffConfig(unittest.TestCase):
    def test_no_diff_is_all_empty(self):
        a = {"users": ["deploy", "root"], "hostname": "web-01"}
        d = config_diff.diff_config(a, dict(a))
        self.assertEqual(d, {"added": {}, "removed": {}, "changed": {}})

    def test_added_key(self):
        d = config_diff.diff_config({}, {"users": ["root"]})
        self.assertEqual(d["added"], {"users": ["root"]})

    def test_removed_key(self):
        d = config_diff.diff_config({"users": ["root"]}, {})
        self.assertEqual(d["removed"], {"users": ["root"]})

    def test_list_diff_reports_items_not_whole_list(self):
        # 「リストが変わった」ではなく「何が増え、何が減ったか」。
        d = config_diff.diff_config({"ports": [22, 80]}, {"ports": [22, 8080]})
        self.assertEqual(d["changed"]["ports"]["added"], [8080])
        self.assertEqual(d["changed"]["ports"]["removed"], [80])

    def test_package_version_change_appears_as_add_and_remove(self):
        d = config_diff.diff_config(
            {"packages": ["openssl 3.0.13", "nginx 1.24"]},
            {"packages": ["openssl 3.0.15", "nginx 1.24"]},
        )
        self.assertEqual(d["changed"]["packages"]["added"], ["openssl 3.0.15"])
        self.assertEqual(d["changed"]["packages"]["removed"], ["openssl 3.0.13"])

    def test_scalar_change_has_before_after(self):
        d = config_diff.diff_config({"hostname": "web-01"}, {"hostname": "web-02"})
        self.assertEqual(d["changed"]["hostname"], {"before": "web-01", "after": "web-02"})

    def test_unchanged_list_not_reported(self):
        d = config_diff.diff_config({"users": ["a", "b"]}, {"users": ["a", "b"]})
        self.assertEqual(d["changed"], {})


class TestJudgeDiff(unittest.TestCase):
    def test_empty_diff_is_ok(self):
        # 差分ゼロが正常。
        self.assertEqual(
            config_diff.judge_diff({"added": {}, "removed": {}, "changed": {}}), "OK"
        )

    def test_any_change_is_warning(self):
        self.assertEqual(
            config_diff.judge_diff(
                {"added": {}, "removed": {}, "changed": {"ports": {"added": [8080], "removed": []}}}
            ),
            "WARNING",
        )

    def test_added_only_is_warning(self):
        self.assertEqual(
            config_diff.judge_diff({"added": {"x": 1}, "removed": {}, "changed": {}}), "WARNING"
        )


class TestSelectOldFiles(unittest.TestCase):
    DAY = 86400

    def test_selects_older_than_days(self):
        now = 1_000 * self.DAY
        entries = [
            ("/var/log/app.log.1", now - 40 * self.DAY),
            ("/var/log/app.log", now - 1 * self.DAY),
        ]
        self.assertEqual(
            config_diff.select_old_files(entries, days=30, now_epoch=now),
            ["/var/log/app.log.1"],
        )

    def test_boundary_exactly_days_old_is_included(self):
        now = 1_000 * self.DAY
        entries = [("/tmp/old.tmp", now - 30 * self.DAY)]
        self.assertEqual(
            config_diff.select_old_files(entries, days=30, now_epoch=now), ["/tmp/old.tmp"]
        )

    def test_nothing_old_returns_empty(self):
        now = 1_000 * self.DAY
        entries = [("/tmp/new.tmp", now - 1 * self.DAY)]
        self.assertEqual(config_diff.select_old_files(entries, days=30, now_epoch=now), [])

    def test_selects_only_does_not_delete(self):
        # 戻り値はパスの一覧。この関数は選ぶだけで、消す仕事を持たない。
        now = 1_000 * self.DAY
        out = config_diff.select_old_files([("/a", 0), ("/b", now)], days=30, now_epoch=now)
        self.assertIsInstance(out, list)
        self.assertEqual(out, ["/a"])


class TestSamplesEndToEnd(unittest.TestCase):
    """samples/ の2ファイルで、正規化→差分→判定の一周が仕様どおりかを確かめる。

    ここが緑なら、あなたの差分エンジンは expected-output.md と同じ結論を出せる。
    """

    @classmethod
    def setUpClass(cls):
        import json

        base = os.path.join(os.path.dirname(__file__), "..", "samples")
        with open(os.path.join(base, "baseline.json")) as f:
            cls.prev = json.load(f)
        with open(os.path.join(base, "current.json")) as f:
            cls.curr = json.load(f)

    def test_collected_at_never_appears_in_diff(self):
        d = config_diff.diff_config(
            config_diff.normalize(self.prev), config_diff.normalize(self.curr)
        )
        for part in ("added", "removed", "changed"):
            self.assertNotIn("collected_at", d[part])

    def test_expected_changes_are_found(self):
        d = config_diff.diff_config(
            config_diff.normalize(self.prev), config_diff.normalize(self.curr)
        )
        c = d["changed"]
        self.assertEqual(c["packages"]["added"], ["openssl 3.0.15-0ubuntu1"])
        self.assertEqual(c["packages"]["removed"], ["openssl 3.0.13-0ubuntu3"])
        self.assertEqual(c["listen_ports"]["added"], [8080])
        self.assertEqual(c["services_running"]["removed"], ["nginx"])
        self.assertEqual(c["users"]["added"], ["tempuser"])
        self.assertEqual(c["cron_entries"]["added"], ["@reboot /tmp/.cache/update.sh"])

    def test_overall_is_warning(self):
        d = config_diff.diff_config(
            config_diff.normalize(self.prev), config_diff.normalize(self.curr)
        )
        self.assertEqual(config_diff.judge_diff(d), "WARNING")
        self.assertEqual(config_diff.status_to_exit_code(config_diff.judge_diff(d)), 1)


if __name__ == "__main__":
    unittest.main()
