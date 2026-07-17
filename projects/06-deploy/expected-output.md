# 出力の見本（自己チェック用）

## 常駐の確認

```
$ sudo systemctl status terakoya-api
● terakoya-api.service - Terakoya 点検結果管理API（課題5で作ったもの）
     Loaded: loaded (/etc/systemd/system/terakoya-api.service; enabled; ...)
     Active: active (running) since ...
```

`enabled`（再起動後も立ち上がる）と `active (running)` の2つが見どころ。

## 生き返りの確認

```
$ ps aux | grep uvicorn        # PID を控える
$ sudo kill <PID>
$ sleep 5 && curl -s http://127.0.0.1:8000/health
{"status":"ok"}                # 数秒で生き返っている（Restart=on-failure）
```

## 玄関（Nginx）経由

```
$ curl -s http://localhost/health
{"status":"ok"}
$ curl -sk https://localhost/health     # 守る①のあと。-k は自己署名のため
{"status":"ok"}
```

## リストア演習のログ（例）

```
$ curl -s http://localhost/servers | python3 -m json.tool | grep hostname
        "hostname": "web-01",
$ sudo systemctl stop terakoya-api && rm projects/05-web-api/api.db
$ sudo systemctl start terakoya-api
$ curl -s http://localhost/servers
[]                              # 消えたことを自分の目で見る
$ sudo systemctl stop terakoya-api
$ cp ~/backups/api-<日時>.db projects/05-web-api/api.db
$ sudo systemctl start terakoya-api
$ curl -s http://localhost/servers | python3 -m json.tool | grep hostname
        "hostname": "web-01",   # 戻った。これで初めて「バックアップがある」と言える
```
