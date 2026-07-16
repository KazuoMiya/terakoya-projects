"""課題1の自動採点。

判定の純関数（judge / worst_status / status_to_exit_code）が仕様どおりかを確かめる。
このファイルは直さなくてよい。読むと「何が期待されているか」が分かる。

実行（projects/01-healthcheck の中で）:
    python -m unittest -v
"""
import os
import sys
import unittest

# src/ を import できるようにする（このリポジトリの課題共通の作法）。
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import healthcheck  # noqa: E402


class TestJudge(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(healthcheck.judge(10, warn=70, crit=90), "OK")

    def test_warning(self):
        self.assertEqual(healthcheck.judge(75, warn=70, crit=90), "WARNING")

    def test_critical(self):
        self.assertEqual(healthcheck.judge(95, warn=70, crit=90), "CRITICAL")

    def test_boundary_warn_is_inclusive(self):
        # ちょうど warn の値は WARNING（「以上」で含める）。
        self.assertEqual(healthcheck.judge(70, warn=70, crit=90), "WARNING")

    def test_boundary_crit_is_inclusive(self):
        # ちょうど crit の値は CRITICAL。
        self.assertEqual(healthcheck.judge(90, warn=70, crit=90), "CRITICAL")


class TestWorstStatus(unittest.TestCase):
    def test_all_ok(self):
        self.assertEqual(healthcheck.worst_status(["OK", "OK"]), "OK")

    def test_warning_wins_over_ok(self):
        self.assertEqual(healthcheck.worst_status(["OK", "WARNING", "OK"]), "WARNING")

    def test_critical_wins(self):
        self.assertEqual(healthcheck.worst_status(["WARNING", "CRITICAL", "OK"]), "CRITICAL")

    def test_unknown_when_only_unknown_and_ok(self):
        self.assertEqual(healthcheck.worst_status(["OK", "UNKNOWN"]), "UNKNOWN")

    def test_warning_beats_unknown(self):
        # 「危険」は「測れない」より優先。UNKNOWN が WARNING を隠さない。
        self.assertEqual(healthcheck.worst_status(["UNKNOWN", "WARNING"]), "WARNING")

    def test_critical_beats_unknown(self):
        self.assertEqual(healthcheck.worst_status(["UNKNOWN", "CRITICAL"]), "CRITICAL")

    def test_empty_is_unknown(self):
        # 何も測れなかった → 測れない。
        self.assertEqual(healthcheck.worst_status([]), "UNKNOWN")


class TestStatusToExitCode(unittest.TestCase):
    def test_mapping(self):
        self.assertEqual(healthcheck.status_to_exit_code("OK"), 0)
        self.assertEqual(healthcheck.status_to_exit_code("WARNING"), 1)
        self.assertEqual(healthcheck.status_to_exit_code("CRITICAL"), 2)
        self.assertEqual(healthcheck.status_to_exit_code("UNKNOWN"), 3)


if __name__ == "__main__":
    unittest.main()
