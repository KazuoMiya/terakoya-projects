"""課題2の自動採点。

DBが無くても判定できる純関数（mask_dsn / judge_ratio / diff_snapshot）を確かめる。
DBに繋ぐ部分は環境で結果が変わるので、ここでは採点しない
（expected-output.md と完了チェックリストで自分で確かめる）。

このファイルは直さなくてよい。読むと「何が期待されているか」が分かる。

実行（projects/02-db-check の中で）:
    python -m unittest -v

Auto-grading for Assignment 2.

Verifies the pure functions that can be judged without a DB (mask_dsn /
judge_ratio / diff_snapshot). The part that connects to the DB gives
different results in different environments, so it is not graded here
(you verify it yourself with expected-output.md and the completion checklist).

You do not need to edit this file. Reading it shows you what is expected.

Run (from inside projects/02-db-check):
    python -m unittest -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import db_check  # noqa: E402


class TestMaskDsn(unittest.TestCase):
    def test_masks_password(self):
        self.assertEqual(
            db_check.mask_dsn("postgresql://checker:s3cret@localhost:5432/terakoya"),
            "postgresql://checker:***@localhost:5432/terakoya",
        )

    def test_password_never_leaks(self):
        # いちばん大事なテスト。戻り値のどこにも生のパスワードが残っていないこと。
        # The most important test: the raw password must not survive anywhere in the return value.
        masked = db_check.mask_dsn("postgresql://checker:hunter2@db.example.com:5432/app")
        self.assertNotIn("hunter2", masked)

    def test_special_characters_in_password(self):
        masked = db_check.mask_dsn("postgresql://u:p%40ss-w0rd!@localhost:5432/db")
        self.assertNotIn("p%40ss-w0rd!", masked)
        self.assertIn("***", masked)

    def test_no_password_returns_unchanged(self):
        dsn = "postgresql://checker@localhost:5432/terakoya"
        self.assertEqual(db_check.mask_dsn(dsn), dsn)

    def test_keeps_host_and_database(self):
        masked = db_check.mask_dsn("postgresql://checker:s3cret@db.example.com:5432/terakoya")
        self.assertIn("db.example.com", masked)
        self.assertIn("terakoya", masked)
        self.assertIn("checker", masked)

    # 接続文字列の書き方は1つではない。関門なのだから、どちらも塞ぐ。
    # There is more than one way to write a connection string. This is a gate, so block both.

    def test_keyword_value_form_is_masked(self):
        # psycopg は "キー=値" の形も受け付ける。URL形式しか見ていないと素通しする。
        # psycopg also accepts the "key=value" form. Watching only the URL form waves it through.
        masked = db_check.mask_dsn("host=localhost user=checker password=s3cret dbname=terakoya")
        self.assertNotIn("s3cret", masked)
        self.assertIn("password=***", masked)
        self.assertIn("host=localhost", masked)
        self.assertIn("dbname=terakoya", masked)

    def test_query_string_form_is_masked(self):
        masked = db_check.mask_dsn("postgresql://checker@localhost:5432/terakoya?password=s3cret")
        self.assertNotIn("s3cret", masked)
        self.assertIn("***", masked)

    def test_keyword_value_without_password_unchanged(self):
        dsn = "host=localhost user=checker dbname=terakoya"
        self.assertEqual(db_check.mask_dsn(dsn), dsn)


class TestJudgeRatio(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(db_check.judge_ratio(50, 100, 70, 90), "OK")

    def test_warning(self):
        self.assertEqual(db_check.judge_ratio(75, 100, 70, 90), "WARNING")

    def test_critical(self):
        self.assertEqual(db_check.judge_ratio(95, 100, 70, 90), "CRITICAL")

    def test_boundary_warn_is_inclusive(self):
        self.assertEqual(db_check.judge_ratio(70, 100, 70, 90), "WARNING")

    def test_boundary_crit_is_inclusive(self):
        self.assertEqual(db_check.judge_ratio(90, 100, 70, 90), "CRITICAL")

    def test_zero_total_is_unknown(self):
        # 0除算で落とさない。「測れない」は UNKNOWN。 / No division-by-zero crash. "Unmeasurable" is UNKNOWN.
        self.assertEqual(db_check.judge_ratio(5, 0, 70, 90), "UNKNOWN")

    def test_none_total_is_unknown(self):
        self.assertEqual(db_check.judge_ratio(5, None, 70, 90), "UNKNOWN")

    def test_ratio_not_raw_value(self):
        # 使用率で見る。生の数ではない（50/200=25% は OK）。 / Judge by ratio, not raw count (50/200=25% is OK).
        self.assertEqual(db_check.judge_ratio(50, 200, 70, 90), "OK")


class TestDiffSnapshot(unittest.TestCase):
    def test_increase(self):
        self.assertEqual(
            db_check.diff_snapshot({"db_size": 100}, {"db_size": 150}), {"db_size": 50}
        )

    def test_decrease(self):
        self.assertEqual(
            db_check.diff_snapshot({"db_size": 100}, {"db_size": 80}), {"db_size": -20}
        )

    def test_no_change_is_zero(self):
        self.assertEqual(db_check.diff_snapshot({"temp_files": 5}, {"temp_files": 5}),
                         {"temp_files": 0})

    def test_key_only_in_curr_is_excluded(self):
        # 前日に無かった項目は比べようがない。 / An item absent yesterday has nothing to compare against.
        self.assertEqual(
            db_check.diff_snapshot({"a": 1}, {"a": 2, "b": 9}), {"a": 1}
        )

    def test_key_only_in_prev_is_excluded(self):
        self.assertEqual(db_check.diff_snapshot({"a": 1, "gone": 5}, {"a": 1}), {"a": 0})

    def test_empty_prev_is_empty_diff(self):
        # 初回。比べる相手がいない。 / First run. Nothing to compare with.
        self.assertEqual(db_check.diff_snapshot({}, {"db_size": 100}), {})

    def test_multiple_keys(self):
        self.assertEqual(
            db_check.diff_snapshot(
                {"db_size": 100, "temp_files": 5}, {"db_size": 150, "temp_files": 4}
            ),
            {"db_size": 50, "temp_files": -1},
        )


class TestStateModelIsAvailable(unittest.TestCase):
    """課題1の状態モデルは配ってある（作り直さなくてよい）ことの確認。

    Confirms that the Assignment 1 status model is provided (no need to rebuild it).
    """

    def test_worst_status(self):
        self.assertEqual(db_check.worst_status(["OK", "UNKNOWN", "WARNING"]), "WARNING")

    def test_status_to_exit_code(self):
        self.assertEqual(db_check.status_to_exit_code("CRITICAL"), 2)


if __name__ == "__main__":
    unittest.main()
