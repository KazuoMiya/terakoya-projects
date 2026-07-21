"""最終課題の自動採点。

純関数3つ（parse_config / judge_http / should_alert）を確かめる。
ループ・HTTP・記録は環境で結果が変わるので、ここでは採点しない
（READMEのデモシナリオで自分で確かめる）。

このファイルは直さなくてよい。読むと「何が期待されているか」が分かる。

実行（projects/07-monitoring の中で）:
    python -m unittest -v

Auto-grading for the final project.

Verifies the three pure functions (parse_config / judge_http / should_alert).
The loop, HTTP, and recording vary by environment, so they are not graded
here (check them yourself with the demo scenario in the README).

You do not need to edit this file. Reading it tells you what is expected.

Run (inside projects/07-monitoring):
    python -m unittest -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import monitor  # noqa: E402


def valid_config():
    return {
        "interval_seconds": 60,
        "targets": [
            {"name": "web-gate", "type": "http", "url": "http://localhost/health"},
            {"name": "this-disk", "type": "disk", "path": "/", "warn": 60, "crit": 85},
        ],
    }


class TestParseConfig(unittest.TestCase):
    def test_valid_config_passes(self):
        interval, targets = monitor.parse_config(valid_config())
        self.assertEqual(interval, 60)
        self.assertEqual(len(targets), 2)

    def test_http_defaults_are_filled(self):
        _, targets = monitor.parse_config(valid_config())
        web = next(t for t in targets if t["name"] == "web-gate")
        self.assertEqual(web["warn_ms"], 500)
        self.assertEqual(web["crit_ms"], 2000)

    def test_disk_thresholds_are_kept(self):
        _, targets = monitor.parse_config(valid_config())
        disk = next(t for t in targets if t["name"] == "this-disk")
        self.assertEqual(disk["warn"], 60)
        self.assertEqual(disk["crit"], 85)

    def test_zero_interval_is_rejected(self):
        c = valid_config(); c["interval_seconds"] = 0
        with self.assertRaises(ValueError):
            monitor.parse_config(c)

    def test_missing_targets_is_rejected(self):
        with self.assertRaises(ValueError):
            monitor.parse_config({"interval_seconds": 60, "targets": []})

    def test_bad_type_is_rejected_with_helpful_message(self):
        c = valid_config(); c["targets"][0]["type"] = "ping"
        with self.assertRaises(ValueError) as ctx:
            monitor.parse_config(c)
        # 「どの対象が」おかしいかがメッセージに入っていること。
        # The message must say WHICH target is wrong.
        self.assertIn("web-gate", str(ctx.exception))

    def test_http_without_url_is_rejected(self):
        c = valid_config(); del c["targets"][0]["url"]
        with self.assertRaises(ValueError):
            monitor.parse_config(c)

    def test_url_must_start_with_http(self):
        c = valid_config(); c["targets"][0]["url"] = "localhost/health"
        with self.assertRaises(ValueError):
            monitor.parse_config(c)

    def test_disk_without_path_is_rejected(self):
        c = valid_config(); del c["targets"][1]["path"]
        with self.assertRaises(ValueError):
            monitor.parse_config(c)

    def test_empty_name_is_rejected(self):
        c = valid_config(); c["targets"][0]["name"] = ""
        with self.assertRaises(ValueError):
            monitor.parse_config(c)


class TestJudgeHttp(unittest.TestCase):
    def test_connection_failure_is_critical(self):
        # 繋がらない＝対象が死んでいる。 / Cannot connect = the target is dead.
        self.assertEqual(monitor.judge_http(None, None, 500, 2000), "CRITICAL")

    def test_non_200_is_critical(self):
        self.assertEqual(monitor.judge_http(500, 12.0, 500, 2000), "CRITICAL")
        self.assertEqual(monitor.judge_http(404, 12.0, 500, 2000), "CRITICAL")

    def test_fast_200_is_ok(self):
        self.assertEqual(monitor.judge_http(200, 42.0, 500, 2000), "OK")

    def test_slow_200_is_warning(self):
        self.assertEqual(monitor.judge_http(200, 800.0, 500, 2000), "WARNING")

    def test_very_slow_200_is_critical(self):
        self.assertEqual(monitor.judge_http(200, 2500.0, 500, 2000), "CRITICAL")

    def test_boundaries_are_inclusive(self):
        self.assertEqual(monitor.judge_http(200, 500.0, 500, 2000), "WARNING")
        self.assertEqual(monitor.judge_http(200, 2000.0, 500, 2000), "CRITICAL")


class TestShouldAlert(unittest.TestCase):
    def test_same_status_stays_silent(self):
        # ここがアラート疲れの防波堤。言い続けない。 / The breakwater against alert fatigue. Don't keep repeating.
        self.assertFalse(monitor.should_alert("OK", "OK"))
        self.assertFalse(monitor.should_alert("CRITICAL", "CRITICAL"))

    def test_degradation_alerts(self):
        self.assertTrue(monitor.should_alert("OK", "CRITICAL"))
        self.assertTrue(monitor.should_alert("OK", "WARNING"))

    def test_recovery_alerts(self):
        # 回復も知らせる。「直った」を確認する人のためだ。
        # Announce recovery too — for the person who confirms "it's fixed."
        self.assertTrue(monitor.should_alert("CRITICAL", "OK"))

    def test_first_time_ok_is_silent(self):
        self.assertFalse(monitor.should_alert(None, "OK"))

    def test_first_time_abnormal_alerts(self):
        self.assertTrue(monitor.should_alert(None, "CRITICAL"))
        self.assertTrue(monitor.should_alert(None, "UNKNOWN"))


class TestGiftsFromTask1(unittest.TestCase):
    """課題1の道具は配ってある（作り直さなくてよい）ことの確認。

    Confirms the Project 1 tools are provided (no need to rebuild them).
    """

    def test_worst_status(self):
        self.assertEqual(monitor.worst_status(["OK", "CRITICAL", "WARNING"]), "CRITICAL")

    def test_status_to_exit_code(self):
        self.assertEqual(monitor.status_to_exit_code("UNKNOWN"), 3)


if __name__ == "__main__":
    unittest.main()
