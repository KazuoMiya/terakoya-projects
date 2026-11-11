# 出力の見本（自己チェック用）

あなたのツールの出力が、**項目と形式**でこの見本とだいたい合っていれば良い。
数値やサーバー名は環境ごとに違って当然なので、**完全一致は求めない**。
見るのは「同じ種類の情報が、読める形で出ているか」だ。

## テキスト出力（`--warn 70 --crit 90`）

```
[WARNING]  disk_usage   74%   (warn=70 crit=90)
[OK]       load_average 1.85  (warn=70 crit=90)
[UNKNOWN]  log_errors   -     (収集に失敗: ログファイルが読めない)

全体: WARNING
```

終了コード: `1`（WARNING）。確認する場合はコマンドの直後に:

```bash
echo $?
```

## JSON出力（`--json` を付けたとき）

```json
{
  "overall": "WARNING",
  "exit_code": 1,
  "checks": [
    { "name": "disk_usage",   "status": "WARNING", "value": 74 },
    { "name": "load_average", "status": "OK",      "value": 1.85 },
    { "name": "log_errors",   "status": "UNKNOWN",  "value": null, "error": "ログファイルが読めない" }
  ]
}
```

> **ロードアベレージが 1.85 で OK なのはなぜか。** この見本は `--warn 70 --crit 90` という
> 1組の閾値を、全項目にそのまま当てている。ディスク使用率（%）にはちょうど合う。
> だがロードアベレージは % ではなく「CPUの行列の長さ」なので、70 に届くことはまず無い。
> つまりこのままだと、ロードアベレージは事実上いつも OK になる。
> 課題1の完了条件はこの形で満たせる。**項目ごとに閾値を分ける**（`--load-warn` /
> `--load-crit` を足す、CPUの個数で割って % にそろえる、など）のは、仕上げたあとの良い改良だ。

## 自己チェックの観点

- [ ] 各項目に状態（OK/WARNING/CRITICAL/UNKNOWN）が付いている
- [ ] 測れなかった項目が UNKNOWN になっている（0 や CRITICAL に化けていない）
- [ ] 全体の状態が、いちばん深刻な項目に一致している
- [ ] 終了コードが全体の状態と一致している（OK=0/WARNING=1/CRITICAL=2/UNKNOWN=3）
- [ ] `--json` の出力が、そのまま別のツールに渡せる正しい JSON になっている
