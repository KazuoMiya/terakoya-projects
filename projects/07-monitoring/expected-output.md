# 出力の見本（自己チェック用）

数値は環境で違って当然。見るのは「同じ種類のログが、同じタイミングで出るか」だ。

## ふだんの周回（全部OKのとき）

```
2026-07-17 09:00:00 INFO 監視開始: 2対象 / 60秒間隔 / 記録先 http://127.0.0.1:8000
（以後、状態が変わらない限り、警告は出ない。沈黙が正常の合図だ）
```

## デモシナリオ中のログ（実測例）

```
# sudo systemctl stop nginx の直後の周回:
2026-07-17 09:05:00 WARNING web-gate が CRITICAL になった (http_health=0)

# その後、CRITICAL のままの周回では何も出ない（言い続けない）

# sudo systemctl start nginx の直後の周回:
2026-07-17 09:12:00 WARNING web-gate が OK になった (http_health=8.3)
```

## APIに残る履歴（記録は毎回）

```
$ curl -s "http://127.0.0.1:8000/servers/1/checks?limit=5"
[
  {"id": 12, "metric": "http_health", "status": "OK",       ...},   ← 回復後
  {"id": 11, "metric": "http_health", "status": "CRITICAL", ...},   ← 停止中
  {"id": 10, "metric": "http_health", "status": "CRITICAL", ...},   ← 停止中
  {"id":  9, "metric": "http_health", "status": "OK",       ...},   ← 停止前
  ...
]
```

## 記録先を止めたとき（おまけの実験）

```
2026-07-17 09:20:05 ERROR web-gate の結果を記録できなかった（監視は続ける）: ...
2026-07-17 09:20:05 ERROR this-server-disk の結果を記録できなかった（監視は続ける）: ...
（監視プロセスは落ちない。APIを戻すと、次の周回から記録が再開する）
```

## 設定を壊したとき（起動前に止まる）

```
$ python src/monitor.py --config config.json    # type を "ping" にしてみた
2026-07-17 09:30:00 ERROR 設定が読めない: 対象 web-gate: type が不正です（http か disk）
$ echo $?
3
```

## 自己チェックの観点

- [ ] 正常時は警告が出ない（INFOの開始ログだけ）
- [ ] 悪化・回復のときだけ、警告が**1回ずつ**出る
- [ ] 履歴には毎周回の記録が残っている（警告の回数と履歴の行数は別物）
- [ ] 記録先が死んでいても監視は続く／設定ミスは起動前に止まる
