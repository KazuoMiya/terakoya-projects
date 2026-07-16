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
"""
import sys

# ── 課題1で自分が書いたもの。ここでは道具として配ってある ──────────────

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
    """
    raise NotImplementedError("parse_line を実装しよう（課題3の道しるべ参照）")


def bucket_by_hour(records, level="ERROR"):
    """レコードの一覧から、指定レベルの件数を「時間帯ごと」に数える。

    - records は parse_line が返した辞書の一覧（None は含まれない前提）
    - 時間帯のキーは "2026-07-15 14" のような形（日時の先頭13文字）
    - 指定レベルに一致するレコードだけを数える
    - 戻り値: {"2026-07-15 13": 2, "2026-07-15 14": 44, ...}
      （その時間帯に1件も無ければ、キー自体が無くてよい）

    例: bucket_by_hour([{"time": "2026-07-15 14:23:55", "level": "ERROR", ...}])
        → {"2026-07-15 14": 1}
    """
    raise NotImplementedError("bucket_by_hour を実装しよう")


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
    """
    raise NotImplementedError("detect_spike を実装しよう")


# ── 読む・レポート・通知・main（自分で組み上げる。自動採点の対象外）──────
# ヒントは課題3の道しるべ（レッスン proj-14）にある。
# ログは1行ずつ読む。レポートはMarkdown。通知は急増があったときだけ。

def main(argv=None):
    """CLI 本体。ログを読み、集計し、急増を探し、レポートと終了コードを返す。"""
    # ★TODO★ 課題3の道しるべに沿って組み上げる。
    raise NotImplementedError("main を実装しよう")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
