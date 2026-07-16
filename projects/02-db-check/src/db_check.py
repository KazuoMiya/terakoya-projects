#!/usr/bin/env python3
"""課題2: DB日次点検ツール（あなたが実装する）。

自動採点が見るのは、下の「純関数」3つ——DBが無くても判定できる部分だ。
DBに繋いで統計ビューを読む部分は環境で結果が変わるので、
expected-output.md と完了チェックリストで自分で確かめる。

鉄則（README と同じ。実装しながら、守れているか見返すこと）:
  1. 点検ツール自身が障害の原因になってはならない
     → 接続タイムアウトと実行タイムアウトを「両方」設定する。片方だけでは無限に待つ。
     → 読むのは統計ビューだけ。実テーブルを全件スキャンしない。
  2. 読み取り専用・最小権限。「直す」機能を混ぜない
     → checker ロールで接続する。セッションを切る処理などは実装しない。
  3. 点検結果そのものが機密になりうる
     → 接続情報はマスクしてから出す。

状態と終了コードは課題1と同じ:
    "OK"=0  "WARNING"=1  "CRITICAL"=2  "UNKNOWN"=3
"""
import sys

# ── 課題1で自分が書いたもの。ここでは道具として配ってある ──────────────
# （小さな道具を持ち回るのは現場でも普通のことだ。作り直さなくていい。）

_SEVERITY = {"OK": 0, "UNKNOWN": 1, "WARNING": 2, "CRITICAL": 3}


def worst_status(statuses):
    """状態リストから全体の状態（CRITICAL > WARNING > UNKNOWN > OK）。"""
    if not statuses:
        return "UNKNOWN"
    return max(statuses, key=lambda s: _SEVERITY.get(s, 1))


def status_to_exit_code(status):
    """状態 → 終了コード（OK=0/WARNING=1/CRITICAL=2/UNKNOWN=3）。"""
    return {"OK": 0, "WARNING": 1, "CRITICAL": 2, "UNKNOWN": 3}.get(status, 3)


# ── 純関数（★TODO★：ここを実装する。自動採点の対象）─────────────────

def mask_dsn(dsn):
    """接続文字列のパスワードを *** に置き換えて返す（鉄則3）。

    ログや画面にパスワードを出さないための関門。これがあるから、
    「接続先をログに残す」と「秘密を出さない」を同時に満たせる。

    厄介なのは、**接続文字列の書き方が1つではない**ことだ。
    psycopg は次のどちらも受け付ける。関門なのだから、どちらも塞ぐ。

      1. URL形式   "postgresql://checker:s3cret@localhost:5432/terakoya"
                    → "postgresql://checker:***@localhost:5432/terakoya"
      2. キー=値形式 "host=localhost user=checker password=s3cret dbname=terakoya"
                    → "host=localhost user=checker password=*** dbname=terakoya"
         （URLの後ろに "?password=s3cret" と付く書き方もある。これも塞ぐ）

    パスワードが含まれていない接続文字列は、そのまま返す。

    *** 想定外の書き方をされたときに素通しする関門は、関門ではない。***
    片方だけ実装して満足しないこと——それが、この課題でいちばん危ない落とし穴だ。

    ヒント: URL形式は urllib.parse.urlsplit / urlunsplit。
            "password=..." の形は re.sub で最後にまとめて潰すと両方に効く。
    """
    raise NotImplementedError("mask_dsn を実装しよう（課題2の道しるべ参照）")


def judge_ratio(used, total, warn_pct, crit_pct):
    """使用率(%)で判定して "OK"/"WARNING"/"CRITICAL"/"UNKNOWN" を返す。

    - used / total * 100 が crit_pct 以上         → "CRITICAL"
    - warn_pct 以上 crit_pct 未満                 → "WARNING"
    - それ未満                                    → "OK"
    - total が 0 や None（測れない・0除算になる） → "UNKNOWN"
      ここで 0 を返したり例外で落ちたりしないこと。「測れない」は UNKNOWN だ。
    （境界は「以上」で含める。例: warn_pct=70 のとき ちょうど70% は WARNING）
    """
    raise NotImplementedError("judge_ratio を実装しよう")


def diff_snapshot(prev, curr):
    """前回と今回のスナップショット（辞書）を比べ、増減を返す。

    - 戻り値は {キー: curr[キー] - prev[キー]}
    - 両方に在るキーだけを対象にする（片方にしか無ければ比べようがない）
    - prev が空（初回で前日データが無い）なら {} を返す

    例: prev={"db_size": 100, "temp_files": 5}
        curr={"db_size": 150, "temp_files": 5, "new_item": 1}
        → {"db_size": 50, "temp_files": 0}
    """
    raise NotImplementedError("diff_snapshot を実装しよう")


# ── 収集・表示・main（自分で組み上げる。自動採点の対象外）──────────────
# ヒントは課題2の道しるべ（レッスン proj-11）にある。
# 点検SQLは README の「点検する10項目」を見ながら1つずつ足していく。
# 個別チェックの失敗は UNKNOWN にして、他のチェックは続行する。

def main(argv=None):
    """CLI 本体。DB_DSN で接続し、点検して、表示し、終了コードを返す。

    接続情報は .env の DB_DSN にある。ただし .env は魔法のファイルではない——
    docker compose は読んでくれるが、この Python は自動では読まない。
    requirements.txt に python-dotenv を入れてあるので、明示的に読み込むこと:
        from dotenv import load_dotenv
        load_dotenv()
    """
    # ★TODO★ 課題2の道しるべに沿って組み上げる。
    raise NotImplementedError("main を実装しよう")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
