#!/usr/bin/env python3
"""課題3: ログ解析・障害検知ツール（あなたが実装する）。

自動採点が見るのは、下の「純関数」3つ——ログファイルが無くても判定できる部分だ。
ファイルを読む・レポートを書く・通知する部分は、expected-output.md と
完了チェックリストで自分で確かめる。

この課題の要点:
  - 1行ずつ読む。ログを全部メモリに載せない（本番のログはGB級になる）
  - 壊れた行で落ちない。数えて、飛ばして、続行する
  - 急増検知には「絶対数の下限」を必ず付ける。倍率だけだと
    「1件→3件」でも鳴ってしまい、誰も読まない通知が量産される（アラート疲れ）
  - 通知は異常のときだけ。正常時は沈黙する

状態と終了コードは課題1・2と同じ:
    "OK"=0  "WARNING"=1  "CRITICAL"=2  "UNKNOWN"=3

Assignment 3: a log analysis / incident detection tool (you implement it).

Auto-grading looks only at the three "pure functions" below — the parts that
can be judged without a log file. You verify the file-reading, report-writing,
and notification parts yourself with expected-output.md and the completion
checklist.

The key points of this assignment:
  - Read line by line. Never load the whole log into memory (production logs
    reach GB scale)
  - Do not crash on a broken line. Count it, skip it, keep going
  - Spike detection must always carry a minimum absolute count. With a ratio
    alone, even "1 → 3 occurrences" fires, and you mass-produce notifications
    nobody reads (alert fatigue)
  - Notify only on anomalies. Stay silent when things are normal

Statuses and exit codes are the same as Assignments 1 and 2:
    "OK"=0  "WARNING"=1  "CRITICAL"=2  "UNKNOWN"=3
"""
import sys

# ── 課題1で自分が書いたもの。ここでは道具として配ってある ──────────────
# ── What you wrote in Assignment 1, handed out here as a tool ──────────────

_SEVERITY = {"OK": 0, "UNKNOWN": 1, "WARNING": 2, "CRITICAL": 3}


def worst_status(statuses):
    """状態リストから全体の状態（CRITICAL > WARNING > UNKNOWN > OK）。

    Overall status from a list of statuses (CRITICAL > WARNING > UNKNOWN > OK).
    """
    if not statuses:
        return "UNKNOWN"
    return max(statuses, key=lambda s: _SEVERITY.get(s, 1))


def status_to_exit_code(status):
    """状態 → 終了コード（OK=0/WARNING=1/CRITICAL=2/UNKNOWN=3）。

    Status → exit code (OK=0/WARNING=1/CRITICAL=2/UNKNOWN=3).
    """
    return {"OK": 0, "WARNING": 1, "CRITICAL": 2, "UNKNOWN": 3}.get(status, 3)


# ── 純関数（★TODO★：ここを実装する。自動採点の対象）─────────────────
# ── Pure functions (★TODO★: implement these — the target of auto-grading) ───

def parse_line(line):
    """ログ1行を分解して辞書で返す。形式に合わない行は None を返す。

    ログの形式（logs/app.log がこの形）:
        "2026-07-15 14:23:55 ERROR db connection timeout host=db-01"
         └── 日時 ──────────┘ └レベル┘ └── メッセージ ─────────────┘

    - 戻り値: {"time": "2026-07-15 14:23:55", "level": "ERROR",
               "message": "db connection timeout host=db-01"}
    - レベルは INFO / WARN / ERROR の3種類
    - 形式に合わない行（スタックトレースの続き・空行など）は **None**。
      例外を投げて全体を止めてはいけない。本物のログには必ず変な行が混ざる。
    - レベルとメッセージの間の空白は1個とは限らない（"INFO  request..." のように
      2個のこともある）。メッセージの前後の空白は取り除いて返す。

    ヒント: 標準ライブラリ re の re.match が使える。r"..." の生文字列で書く。

    Split one log line into a dict and return it. Return None for lines that
    do not match the format.

    The log format (logs/app.log looks like this):
        "2026-07-15 14:23:55 ERROR db connection timeout host=db-01"
         └── datetime ──────┘ └level┘ └── message ─────────────────┘

    - Return value: {"time": "2026-07-15 14:23:55", "level": "ERROR",
                     "message": "db connection timeout host=db-01"}
    - There are three levels: INFO / WARN / ERROR
    - Lines that do not match the format (a stack-trace continuation, an empty
      line, etc.) return **None**. Never throw an exception and stop the whole
      run. Real logs always contain odd lines.
    - The whitespace between level and message is not always one space (it can
      be two, as in "INFO  request..."). Strip the whitespace around the
      message before returning it.

    Hint: re.match from the standard library re works. Write the pattern as a
    raw string, r"...".
    """
    raise NotImplementedError("parse_line を実装しよう（課題3の道しるべ参照） / Implement parse_line (see the Assignment 3 guide)")


def bucket_by_hour(records, level="ERROR"):
    """レコードの一覧から、指定レベルの件数を「時間帯ごと」に数える。

    - records は parse_line が返した辞書の一覧（None は含まれない前提）
    - 時間帯のキーは "2026-07-15 14" のような形（日時の先頭13文字）
    - 指定レベルに一致するレコードだけを数える
    - 戻り値: {"2026-07-15 13": 2, "2026-07-15 14": 44, ...}
      （その時間帯に1件も無ければ、キー自体が無くてよい）

    例: bucket_by_hour([{"time": "2026-07-15 14:23:55", "level": "ERROR", ...}])
        → {"2026-07-15 14": 1}

    From a list of records, count occurrences of the given level per hour.

    - records is a list of dicts returned by parse_line (assume no None inside)
    - The hour key looks like "2026-07-15 14" (the first 13 characters of the
      datetime)
    - Count only the records that match the given level
    - Return value: {"2026-07-15 13": 2, "2026-07-15 14": 44, ...}
      (if an hour has no occurrences, its key may simply be absent)

    Example: bucket_by_hour([{"time": "2026-07-15 14:23:55", "level": "ERROR", ...}])
             → {"2026-07-15 14": 1}
    """
    raise NotImplementedError("bucket_by_hour を実装しよう / Implement bucket_by_hour")


def detect_spike(series, factor=3.0, min_count=10):
    """時系列の件数から「急増」した時間帯を探して、ラベルの一覧を返す。

    - series は時刻順に並んだ (ラベル, 件数) の一覧
      例: [("2026-07-15 12", 2), ("2026-07-15 13", 3), ("2026-07-15 14", 44)]
    - ある時間帯が急増かどうかは、**それより前の全時間帯の平均**（ベースライン）と比べる:
        件数 >= ベースライン × factor  かつ  件数 >= min_count
      の両方を満たしたら急増（境界は「以上」で含める。課題1からの約束ごと）
    - 先頭の時間帯は、比べる相手がいないので急増にはならない
    - 戻り値: 急増と判定したラベルの一覧（上の例なら ["2026-07-15 14"]）

    min_count が無いとどうなるか、考えてみてほしい。深夜にエラーが1件→3件に
    「3倍増」しただけで通知が鳴る。それが毎晩続くと、人は通知を読まなくなる。
    **倍率のワナを絶対数の下限で塞ぐ**——これがアラート疲れへの最初の防波堤だ。

    Search a time series of counts for hours that "spiked", and return their labels.

    - series is a list of (label, count) pairs in chronological order
      e.g. [("2026-07-15 12", 2), ("2026-07-15 13", 3), ("2026-07-15 14", 44)]
    - Whether an hour is a spike is decided against the **average of all
      earlier hours** (the baseline):
        count >= baseline * factor  AND  count >= min_count
      A spike is when both hold (boundaries are inclusive, "or above" — the
      promise carried over from Assignment 1)
    - The first hour has nothing to compare against, so it can never be a spike
    - Return value: the list of labels judged as spikes (["2026-07-15 14"] in
      the example above)

    Think about what happens without min_count. Errors going from 1 to 3 at
    midnight is a "3x increase", so the notification fires. When that happens
    every night, people stop reading notifications.
    **Plug the ratio trap with a minimum absolute count** — this is the first
    seawall against alert fatigue.
    """
    raise NotImplementedError("detect_spike を実装しよう / Implement detect_spike")


# ── 読む・レポート・通知・main（自分で組み上げる。自動採点の対象外）──────
# ── Reading / report / notification / main (build these yourself; not auto-graded) ──
# ヒントは課題3の道しるべ（レッスン proj-14）にある。
# Hints are in the Assignment 3 guide (lesson proj-14).
# ログは1行ずつ読む。レポートはMarkdown。通知は急増があったときだけ。
# Read the log line by line. The report is Markdown. Notify only when there was a spike.

def main(argv=None):
    """CLI 本体。ログを読み、集計し、急増を探し、レポートと終了コードを返す。

    The CLI itself. Read the log, aggregate, look for spikes, and return a
    report and an exit code.
    """
    # ★TODO★ 課題3の道しるべに沿って組み上げる。 / Build it up following the Assignment 3 guide.
    raise NotImplementedError("main を実装しよう / Implement main")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
