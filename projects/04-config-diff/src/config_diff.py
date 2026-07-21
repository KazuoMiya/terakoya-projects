#!/usr/bin/env python3
"""課題4: 構成情報の収集と差分検知（あなたが実装する）。

「気づいたら設定が変わっていた」をなくす道具だ。サーバーの構成
（パッケージ・サービス・ポート・ユーザー・cron）をJSONに書き出し、
前回のスナップショットと比べて、**変わったところだけ**を報告する。

この課題の心臓は「**差分ゼロが正常**」という考え方だ。
毎日レポートが差分だらけなら、誰も読まなくなる（課題3のアラート疲れと同じ）。
だから「揺れて当然の値」は比較の前に落とす——それが normalize の仕事だ。

自動採点が見るのは、下の純関数4つ。収集（subprocessでOSコマンド）は
環境で結果が変わるので採点しない（サンプルと自己チェックで確かめる）。

状態と終了コードは課題1と同じ:
    差分なし="OK"=0  差分あり="WARNING"=1  スナップショットが読めない="UNKNOWN"=3

Project 4: Configuration collection and drift detection (you implement this).

A tool to eliminate "the config changed and nobody noticed." It writes the
server's configuration (packages, services, ports, users, cron) out to JSON,
compares it with the previous snapshot, and reports **only what changed**.

The heart of this project is the idea that **zero diff is normal**.
If the daily report is full of diffs, nobody reads it anymore (the same
alert fatigue as Project 3). So "naturally-wobbling values" are dropped
before comparing — that is normalize's job.

The auto-grading looks only at the four pure functions below. Collection
(OS commands via subprocess) varies by environment, so it is not graded
(check it yourself with the samples and the self-checks).

Statuses and exit codes are the same as Project 1:
    no diff="OK"=0  diff found="WARNING"=1  snapshot unreadable="UNKNOWN"=3
"""
import sys

# ── 課題1の道具（配ってある。作り直さない）─────────────────────────
# ── Tools from Project 1 (provided — do not rebuild them) ─────────────

_SEVERITY = {"OK": 0, "UNKNOWN": 1, "WARNING": 2, "CRITICAL": 3}


def worst_status(statuses):
    if not statuses:
        return "UNKNOWN"
    return max(statuses, key=lambda s: _SEVERITY.get(s, 1))


def status_to_exit_code(status):
    return {"OK": 0, "WARNING": 1, "CRITICAL": 2, "UNKNOWN": 3}.get(status, 3)


# ── 純関数（★TODO★：ここを実装する。自動採点の対象）─────────────────
# ── Pure functions (★TODO★: implement these — the auto-grading target) ──

# 「揺れて当然」で、差分として報告しても意味が無いキー。
# Keys that naturally wobble — reporting them as a diff would be meaningless.
VOLATILE_KEYS = {"collected_at"}


def normalize(snapshot):
    """スナップショット（辞書）を、比較できる形に整えて**新しい辞書**で返す。

    1. VOLATILE_KEYS にあるキーを取り除く
       （収集した時刻は毎回違って当然。差分に混ぜると毎日「変化あり」になる）
    2. 値がリストのものは、ソートしたコピーにする
       （収集コマンドの出力順は揺れることがある。順序の揺れは差分ではない）
    3. 引数の snapshot 自体は変更しない（呼び出し元を驚かせない）

    例: {"collected_at": "…", "users": ["root", "deploy"]}
        → {"users": ["deploy", "root"]}

    Normalize a snapshot (dict) into a comparable form and return a **new dict**.

    1. Remove the keys listed in VOLATILE_KEYS
       (the collection time naturally differs every run; mixing it into the
       diff makes every day read "changed")
    2. Replace list values with sorted copies
       (the output order of collection commands can wobble; order wobble
       is not a diff)
    3. Do not modify the snapshot argument itself (no surprises for the caller)

    Example: {"collected_at": "…", "users": ["root", "deploy"]}
        → {"users": ["deploy", "root"]}
    """
    raise NotImplementedError(
        "normalize を実装しよう（課題4の道しるべ参照） / Implement normalize (see the Project 4 guide)"
    )


def diff_config(prev, curr):
    """正規化済みのスナップショット同士を比べ、差分を返す。

    戻り値は {"added": {}, "removed": {}, "changed": {}} の形。
    - added:   curr にだけあるキー（値ごと）
    - removed: prev にだけあるキー（値ごと）
    - changed: 両方にあって値が違うキー。ただし——
        * 両方の値がリストなら、丸ごとでなく**中身**を比べて
          {"added": [増えた項目], "removed": [減った項目]} を入れる
          （「packagesが変わった」ではなく「opensslのこの版が増え、この版が減った」
           と言えるのが、使えるレポートだ）
        * リスト以外は {"before": 前の値, "after": 今の値}
    - 差分が無ければ、3つとも空の辞書。

    例: prev={"ports": [22, 80]},  curr={"ports": [22, 8080]}
        → {"added": {}, "removed": {},
           "changed": {"ports": {"added": [8080], "removed": [80]}}}

    Compare two normalized snapshots and return the diff.

    The return value has the shape {"added": {}, "removed": {}, "changed": {}}.
    - added:   keys that exist only in curr (with their values)
    - removed: keys that exist only in prev (with their values)
    - changed: keys in both whose values differ. However —
        * if both values are lists, compare their **contents** rather than the
          whole list, and store {"added": [new items], "removed": [gone items]}
          (a useful report says "this openssl version appeared and that one
           disappeared," not just "packages changed")
        * for non-lists, store {"before": old value, "after": new value}
    - If there is no diff, all three are empty dicts.

    Example: prev={"ports": [22, 80]},  curr={"ports": [22, 8080]}
        → {"added": {}, "removed": {},
           "changed": {"ports": {"added": [8080], "removed": [80]}}}
    """
    raise NotImplementedError("diff_config を実装しよう / Implement diff_config")


def judge_diff(diff):
    """差分から全体の状態を決める。

    - added / removed / changed がすべて空 → "OK"（差分ゼロが正常）
    - 1つでも中身があれば → "WARNING"

    WARNING止まりなのには理由がある。差分は「変わった」という**事実の検知**であって、
    それが正しい変更か事故かは、この関数には分からない。判断するのは人間だ
    （課題2の鉄則「検知と対処を分ける」と同じ思想）。

    Decide the overall status from the diff.

    - added / removed / changed all empty → "OK" (zero diff is normal)
    - anything non-empty in any of them → "WARNING"

    There is a reason it stops at WARNING. A diff is the **detection of the
    fact** that something changed; this function cannot know whether it was a
    legitimate change or an accident. That judgment belongs to a human
    (the same philosophy as Project 2's Iron Rule: separate detection from
    response).
    """
    raise NotImplementedError("judge_diff を実装しよう / Implement judge_diff")


def select_old_files(entries, days, now_epoch):
    """【発展課題用】「消してよい候補」を選ぶ。**選ぶだけで、消さない。**

    entries は (パス, 最終更新エポック秒) のタプルの一覧。
    now_epoch から見て days 日以上前のものの**パスの一覧**を返す
    （ちょうど days 日前も含む＝「以上」）。

    「選ぶ」と「消す」を関数から分けておくのが、dry-run（予行演習）の土台だ。
    選ぶだけなら何度実行しても安全で、テストもできる。

    [For the extension task] Select deletion candidates. **Select only — never delete.**

    entries is a list of (path, last-modified epoch seconds) tuples.
    Return the **list of paths** that are at least days days old as seen from
    now_epoch (exactly days days old is included — "at least").

    Keeping "select" and "delete" in separate functions is the foundation of a
    dry run. Selecting alone is safe to run any number of times, and testable.
    """
    raise NotImplementedError("select_old_files を実装しよう / Implement select_old_files")


# ── 収集・表示・main（自分で組み上げる。自動採点の対象外）──────────────
# ── Collect / display / main (you assemble these; not auto-graded) ─────
# ヒントは課題4の道しるべ（レッスン proj-17）にある。
# Hints are in the Project 4 guide (lesson proj-17).
# 収集は課題1の subprocess の型がそのまま使える。取れない項目は
# 記録に「取れなかった」と残して続行する（部分障害でも止めない）。
# Collection can reuse the subprocess pattern from Project 1. For items you
# cannot collect, record "unavailable" and keep going (do not stop on partial failure).

def main(argv=None):
    """CLI 本体。収集→正規化→保存→前回と比較→レポート、を回す。

    The CLI body. Runs collect → normalize → save → compare with previous → report.
    """
    # ★TODO★ 課題4の道しるべに沿って組み上げる。 / Assemble it following the Project 4 guide.
    raise NotImplementedError("main を実装しよう / Implement main")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
