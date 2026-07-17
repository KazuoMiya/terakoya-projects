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
"""
import sys

# ── 課題1の道具（配ってある。作り直さない）─────────────────────────

_SEVERITY = {"OK": 0, "UNKNOWN": 1, "WARNING": 2, "CRITICAL": 3}


def worst_status(statuses):
    if not statuses:
        return "UNKNOWN"
    return max(statuses, key=lambda s: _SEVERITY.get(s, 1))


def status_to_exit_code(status):
    return {"OK": 0, "WARNING": 1, "CRITICAL": 2, "UNKNOWN": 3}.get(status, 3)


# ── 純関数（★TODO★：ここを実装する。自動採点の対象）─────────────────

# 「揺れて当然」で、差分として報告しても意味が無いキー。
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
    """
    raise NotImplementedError("normalize を実装しよう（課題4の道しるべ参照）")


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
    """
    raise NotImplementedError("diff_config を実装しよう")


def judge_diff(diff):
    """差分から全体の状態を決める。

    - added / removed / changed がすべて空 → "OK"（差分ゼロが正常）
    - 1つでも中身があれば → "WARNING"

    WARNING止まりなのには理由がある。差分は「変わった」という**事実の検知**であって、
    それが正しい変更か事故かは、この関数には分からない。判断するのは人間だ
    （課題2の鉄則「検知と対処を分ける」と同じ思想）。
    """
    raise NotImplementedError("judge_diff を実装しよう")


def select_old_files(entries, days, now_epoch):
    """【発展課題用】「消してよい候補」を選ぶ。**選ぶだけで、消さない。**

    entries は (パス, 最終更新エポック秒) のタプルの一覧。
    now_epoch から見て days 日以上前のものの**パスの一覧**を返す
    （ちょうど days 日前も含む＝「以上」）。

    「選ぶ」と「消す」を関数から分けておくのが、dry-run（予行演習）の土台だ。
    選ぶだけなら何度実行しても安全で、テストもできる。
    """
    raise NotImplementedError("select_old_files を実装しよう")


# ── 収集・表示・main（自分で組み上げる。自動採点の対象外）──────────────
# ヒントは課題4の道しるべ（レッスン proj-17）にある。
# 収集は課題1の subprocess の型がそのまま使える。取れない項目は
# 記録に「取れなかった」と残して続行する（部分障害でも止めない）。

def main(argv=None):
    """CLI 本体。収集→正規化→保存→前回と比較→レポート、を回す。"""
    # ★TODO★ 課題4の道しるべに沿って組み上げる。
    raise NotImplementedError("main を実装しよう")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
