"""課題3の自動採点。

ログファイルが無くても判定できる純関数（parse_line / bucket_by_hour / detect_spike）を
確かめる。ファイル読み・レポート・通知は環境に依存するので、ここでは採点しない。

このファイルは直さなくてよい。読むと「何が期待されているか」が分かる。

実行（projects/03-log-analysis の中で）:
    python -m unittest -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import log_check  # noqa: E402


class TestParseLine(unittest.TestCase):
    def test_error_line(self):
        r = log_check.parse_line("2026-07-15 14:23:55 ERROR db connection timeout host=db-01")
        self.assertEqual(r["time"], "2026-07-15 14:23:55")
        self.assertEqual(r["level"], "ERROR")
        self.assertEqual(r["message"], "db connection timeout host=db-01")

    def test_info_line_with_double_space(self):
        # INFO の後ろの空白は2個。空白1個を決め打ちすると落ちる。
        r = log_check.parse_line("2026-07-14 00:00:11 INFO  request handled path=/health status=200")
        self.assertEqual(r["level"], "INFO")
        self.assertEqual(r["message"], "request handled path=/health status=200")

    def test_warn_line(self):
        r = log_check.parse_line("2026-07-14 09:33:42 WARN  slow query took 2.9s table=health_checks")
        self.assertEqual(r["level"], "WARN")

    def test_traceback_line_is_none(self):
        # 本物のログには必ず「形式に合わない行」が混ざる。落ちずに None。
        self.assertIsNone(log_check.parse_line("Traceback (most recent call last):"))

    def test_continuation_line_is_none(self):
        self.assertIsNone(log_check.parse_line('  File "app.py", line 42, in handle_payment'))

    def test_empty_line_is_none(self):
        self.assertIsNone(log_check.parse_line(""))

    def test_garbage_is_none(self):
        self.assertIsNone(log_check.parse_line("ConnectionError: [Errno 111] Connection refused"))


class TestBucketByHour(unittest.TestCase):
    RECORDS = [
        {"time": "2026-07-15 13:07:55", "level": "ERROR", "message": "a"},
        {"time": "2026-07-15 13:26:55", "level": "ERROR", "message": "b"},
        {"time": "2026-07-15 13:33:42", "level": "WARN", "message": "c"},
        {"time": "2026-07-15 14:00:55", "level": "ERROR", "message": "d"},
        {"time": "2026-07-15 14:05:11", "level": "INFO", "message": "e"},
    ]

    def test_counts_errors_per_hour(self):
        self.assertEqual(
            log_check.bucket_by_hour(self.RECORDS),
            {"2026-07-15 13": 2, "2026-07-15 14": 1},
        )

    def test_level_filter(self):
        # WARN を数えたいときもある。level 引数で切り替えられること。
        self.assertEqual(
            log_check.bucket_by_hour(self.RECORDS, level="WARN"),
            {"2026-07-15 13": 1},
        )

    def test_empty_records(self):
        self.assertEqual(log_check.bucket_by_hour([]), {})


class TestDetectSpike(unittest.TestCase):
    def test_clear_spike(self):
        series = [("h1", 2), ("h2", 3), ("h3", 2), ("h4", 44)]
        # h4 のベースラインは (2+3+2)/3 ≒ 2.33。44 >= 7 かつ 44 >= 10 → 急増。
        self.assertEqual(log_check.detect_spike(series), ["h4"])

    def test_no_spike_when_flat(self):
        series = [("h1", 3), ("h2", 2), ("h3", 3), ("h4", 2)]
        self.assertEqual(log_check.detect_spike(series), [])

    def test_min_count_guard(self):
        # 1件→3件は「3倍増」だが、絶対数が小さい。鳴らさない（アラート疲れの防波堤）。
        series = [("h1", 1), ("h2", 3)]
        self.assertEqual(log_check.detect_spike(series), [])

    def test_min_count_can_be_tuned(self):
        # min_count を下げれば同じデータでも鳴る。ガードの意味がここで分かる。
        series = [("h1", 1), ("h2", 3)]
        self.assertEqual(log_check.detect_spike(series, min_count=3), ["h2"])

    def test_zero_baseline_with_enough_count_is_spike(self):
        # それまで0件 → いきなり12件。0×factor=0 なので倍率は必ず満たす。
        # min_count が実質の門番になる。0除算や None を返して落ちないこと。
        series = [("h1", 0), ("h2", 0), ("h3", 12)]
        self.assertEqual(log_check.detect_spike(series), ["h3"])

    def test_first_element_never_flagged(self):
        # 先頭は比べる相手がいない。どんなに大きくても急増とは言えない。
        series = [("h1", 100)]
        self.assertEqual(log_check.detect_spike(series), [])

    def test_empty_series(self):
        self.assertEqual(log_check.detect_spike([]), [])

    def test_boundary_is_inclusive(self):
        # ちょうど factor 倍・ちょうど min_count は「以上」で含める（課題1からの約束）。
        series = [("h1", 4), ("h2", 12)]
        # ベースライン4、factor3 → 12 >= 12 かつ 12 >= 10 → 急増。
        self.assertEqual(log_check.detect_spike(series), ["h2"])

    def test_multiple_spikes(self):
        series = [("h1", 2), ("h2", 2), ("h3", 30), ("h4", 2), ("h5", 40)]
        result = log_check.detect_spike(series)
        self.assertIn("h3", result)
        self.assertIn("h5", result)


class TestStateModelIsAvailable(unittest.TestCase):
    """課題1の状態モデルは配ってある（作り直さなくてよい）ことの確認。"""

    def test_worst_status(self):
        self.assertEqual(log_check.worst_status(["OK", "WARNING"]), "WARNING")

    def test_status_to_exit_code(self):
        self.assertEqual(log_check.status_to_exit_code("WARNING"), 1)


if __name__ == "__main__":
    unittest.main()
