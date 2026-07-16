# 出力の見本（自己チェック用）

あなたのツールの出力が、**項目と形式**でこの見本とだいたい合っていれば良い。
数値は環境ごとに違って当然なので、**完全一致は求めない**。

## テキスト出力

```
[OK       ] connectivity         2.1ms
[OK       ] uptime               3.5hours
[OK       ] recovery_state       primary
[OK       ] db_size              9.42MB  [前日比 +0.15]
[OK       ] disk_usage           41.0%
[OK       ] connections          2/100
[OK       ] long_queries         0
[WARNING  ] idle_in_transaction  1
[OK       ] lock_waits           0
[OK       ] temp_files           0
[WARNING  ] dead_tuples          342

全体: WARNING
```

終了コード: `1`（WARNING）。`echo $?` で確認できる。

## ログ（パスワードが出ていないこと）

```
2026-07-16 09:00:00 INFO 点検開始: postgresql://checker:***@localhost:5432/terakoya
2026-07-16 09:00:00 INFO 点検終了: WARNING
```

**ここに生のパスワードが出ていたら、鉄則3を破っている。** 最優先で直すこと。

## JSON出力（`--json`）

```json
{
  "overall": "WARNING",
  "exit_code": 1,
  "checks": [
    { "name": "connectivity", "status": "OK", "value": 2.1, "unit": "ms" },
    { "name": "idle_in_transaction", "status": "WARNING", "value": 1 },
    { "name": "dead_tuples", "status": "WARNING", "value": 342, "table": "health_checks" }
  ],
  "deltas": { "db_size": 0.15 }
}
```

## 自己チェックの観点

- [ ] 10項目すべてが出ている
- [ ] ログの接続先が `***` でマスクされている（鉄則3）
- [ ] 測れなかった項目が UNKNOWN（0 や CRITICAL に化けていない）
- [ ] 全体の状態が、いちばん深刻な項目に一致している／終了コードも一致
- [ ] 2回目の実行で `deltas`（前日差分）が出る
- [ ] **わざと idle in transaction を作ったら、項目8が拾えた**

> `dead_tuples` が初回から WARNING（約342行）なのは想定どおり。サンプルデータが
> わざと残骸を残しているからで、壊れているのではない。
