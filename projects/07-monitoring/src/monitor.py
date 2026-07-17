#!/usr/bin/env python3
"""最終課題: 統合監視システム（あなたが実装する）。

新しく学ぶ技術は「定期実行のループ」だけだ。残りは全部、これまでの再結線になる。
  - 判定の考え方と4状態     → 課題1
  - 設定と秘密の分離(.env)  → 課題2
  - アラート疲れを防ぐ設計  → 課題3
  - 結果の送り先(API)       → 課題5
  - 常駐の土台              → 課題6

構成: config.json に監視対象を書く。interval_seconds ごとに全対象をチェックし、
結果を課題5のAPIへ POST する。異常の履歴はAPIのDBに貯まる。

自動採点が見るのは、下の純関数3つ。ループ・HTTP・記録は環境に依存するので、
デモシナリオ（README参照）で自分で確かめる。

状態と終了コードは課題1と同じ:
    "OK"=0  "WARNING"=1  "CRITICAL"=2  "UNKNOWN"=3
"""
import sys

# ── 課題1の道具（配ってある。作り直さない）─────────────────────────

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

def parse_config(config):
    """設定（辞書）を検証して (interval_seconds, 監視対象のリスト) を返す。

    監視は無人で回り続けるものだ。設定ミスは、起動した「あと」ではなく
    「起動する前」に、分かりやすい言葉で止める。それがこの関数の仕事だ。

    検証ルール:
      - config["interval_seconds"] は 0 より大きい数。違えば ValueError
      - config["targets"] は 1件以上のリスト。空や欠落は ValueError
      - 各対象は辞書で、共通の必須キーは name（空でない文字列）と
        type（"http" か "disk" のどちらか）
      - type が "http" なら url が必須（"http://" か "https://" で始まること）
      - type が "disk" なら path が必須
      - しきい値は省略できる。省略時は次の既定値で埋めて返す:
          http: warn_ms=500, crit_ms=2000（応答時間ミリ秒）
          disk: warn=70, crit=90（使用率%）

    ValueError のメッセージには「どの対象の・何が・どうおかしいか」を日本語で
    入れること（例: "対象 web-gate: type が不正です（http か disk）"）。
    設定ファイルを書くのは、未来の自分だ。未来の自分に分かる言葉で止める。
    """
    raise NotImplementedError("parse_config を実装しよう（最終課題の道しるべ参照）")


def judge_http(status_code, elapsed_ms, warn_ms, crit_ms):
    """HTTPチェックの判定。

    - status_code が None（接続できなかった）→ "CRITICAL"（対象が死んでいる）
    - status_code が 200 以外 → "CRITICAL"（生きているが正常応答ではない）
    - 200 でも、応答時間 elapsed_ms が crit_ms 以上 → "CRITICAL"
    - warn_ms 以上 crit_ms 未満 → "WARNING"
    - それ未満 → "OK"
    （境界は「以上」で含める。課題1の judge と同じ流儀だ）
    """
    raise NotImplementedError("judge_http を実装しよう")


def should_alert(prev_status, curr_status):
    """「声を上げるべきか」を決める。True なら警告ログを出す。

    記録（APIへのPOST）は毎回行う。だが警告の声は別だ。CRITICALのまま
    5分ごとに叫び続けるツールは、課題3で見た「アラート疲れ」を自分で作る。

    ルール:
      - 前回と状態が変わった → True（悪化も、回復も。回復を知らせるのは
        「直った」を確認する人のためだ）
      - 前回と同じ → False（言い続けない）
      - 初回（prev_status が None）→ curr_status が "OK" なら False、
        それ以外なら True（最初から異常なら黙っていてはいけない）
    """
    raise NotImplementedError("should_alert を実装しよう")


# ── チェック・記録・ループ（自分で組み上げる。自動採点の対象外）─────────
# ヒントは最終課題の道しるべ（レッスン proj-29）にある。
# - HTTPチェック: requests.get(url, timeout=5) で応答コードと時間を測る。
#   接続エラーは except で受けて status_code=None として judge_http へ
# - ディスクチェック: shutil.disk_usage(path)（課題2で使った）
# - 記録: 課題5のAPIへ POST（X-API-Key は .env から。課題1のCLIが
#   やっていた「画面に出す」が「APIに送る」に変わっただけだ）
# - 記録に失敗しても監視は止めない。ログに残して次の周回へ
#   （対象の障害と、監視自身の障害を混ぜない）
# - ループ: while True + time.sleep(interval)。--once で1周だけ実行できる
#   ようにしておくと、テストとデモが楽になる

def main(argv=None):
    """config.json を読み、監視ループを回す。"""
    # ★TODO★ 最終課題の道しるべに沿って組み上げる。
    raise NotImplementedError("main を実装しよう")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
