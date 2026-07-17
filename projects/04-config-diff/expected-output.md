# 出力の見本（自己チェック用）

## サンプル2枚での差分レポート（形式は自由。内容がこの6行に一致すること）

```
# 構成差分レポート

+ packages: openssl 3.0.15-0ubuntu1
- packages: openssl 3.0.13-0ubuntu3
- services_running: nginx
+ listen_ports: 8080
+ users: tempuser
+ cron_entries: @reboot /tmp/.cache/update.sh
```

終了コード: `1`（WARNING）。**`collected_at` がどこにも出ていないこと。**

## 自分のマシンで（Ubuntu / WSL2）

```
$ python src/config_diff.py
初回実行: ベースラインを保存した。次回から差分が出る。
$ echo $?
0

$ python src/config_diff.py
# 構成差分レポート

差分なし（前回と同じ構成）。
$ echo $?
0
```

2回目が「差分なし」にならない場合、揺れる値が normalize で落ちていない。
差分に出ているものをよく見ること——それが「落とすべき値」のリストだ。

## わざと変化を作ったとき（例: パッケージを1つ入れる）

```
$ sudo apt install -y sl
$ python src/config_diff.py
# 構成差分レポート

+ packages: sl 5.02-1
$ echo $?
1
```

## 発展 cleanup の dry-run（既定）

```
$ python src/cleanup.py /tmp/cleanup-practice --days 30
[dry-run] 消す候補 2件（実際には消していない）:
  /tmp/cleanup-practice/old1.log
  /tmp/cleanup-practice/old2.log
本当に消すには --execute を付ける。
$ echo $?
0
```

## 自己チェックの観点

- [ ] サンプル2枚で、5つの変化がすべて出た／collected_at は出ない
- [ ] 初回=保存のみでOK終了、2回連続実行で「差分なし」
- [ ] わざと作った変化を検知できた（確認後は元に戻した）
- [ ] 収集できない項目で落ちない（「取れなかった」の記録が出る）
- [ ] （発展）cleanup は既定で何も消さず、--execute でだけ消え、2回目は「消すものなし」
