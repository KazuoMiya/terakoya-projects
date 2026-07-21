> 日本語版: [expected-output.md](./expected-output.md)

# Sample output (for self-checking)

## Checking that it keeps running

```
$ sudo systemctl status terakoya-api
● terakoya-api.service - Terakoya 点検結果管理API（課題5で作ったもの）
     Loaded: loaded (/etc/systemd/system/terakoya-api.service; enabled; ...)
     Active: active (running) since ...
```

> The Description line comes from the unit-file template, which is written in Japanese:
> "Terakoya Check-Results API (the one you built in Project 5)." If you edited the
> Description yourself, your wording will appear instead.

The two things to look at are `enabled` (it comes up after a reboot) and `active (running)`.

## Checking that it comes back to life

```
$ ps aux | grep uvicorn        # note the PID
$ sudo kill <PID>
$ sleep 5 && curl -s http://127.0.0.1:8000/health
{"status":"ok"}                # revived within seconds (Restart=on-failure)
```

## Via the front door (Nginx)

```
$ curl -s http://localhost/health
{"status":"ok"}
$ curl -sk https://localhost/health     # after Guard It (1). -k is for the self-signed cert
{"status":"ok"}
```

## A log of the restore drill (example)

```
$ curl -s http://localhost/servers | python3 -m json.tool | grep hostname
        "hostname": "web-01",
$ sudo systemctl stop terakoya-api && rm projects/05-web-api/api.db
$ sudo systemctl start terakoya-api
$ curl -s http://localhost/servers
[]                              # see with your own eyes that it's gone
$ sudo systemctl stop terakoya-api
$ cp ~/backups/api-<timestamp>.db projects/05-web-api/api.db
$ sudo systemctl start terakoya-api
$ curl -s http://localhost/servers | python3 -m json.tool | grep hostname
        "hostname": "web-01",   # it's back. Only now can you say "we have a backup"
```
