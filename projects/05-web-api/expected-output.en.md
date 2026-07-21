> 日本語版: [expected-output.md](./expected-output.md)

# Sample output (for self-checking)

If the TestClient grading is green, you have met the spec. What follows is a sample
of the "one loop by hand." (Instead of curl, the "Try it out" button in /docs does
the same thing.)

## One loop, by hand

```bash
# liveness check (no auth)
$ curl -s http://127.0.0.1:8000/health
{"status":"ok"}

# register without the key → 401
$ curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8000/servers \
    -H 'Content-Type: application/json' -d '{"hostname":"web-01","role":"web"}'
401

# register with the key → 201
$ curl -s -X POST http://127.0.0.1:8000/servers \
    -H 'Content-Type: application/json' -H 'X-API-Key: dev-secret-key' \
    -d '{"hostname":"web-01","role":"web"}'
{"id":1,"hostname":"web-01","role":"web"}

# the same hostname again → 409
# hostname left empty → 422
# status set to "BROKEN" → 422

# record a check result → 201
$ curl -s -X POST http://127.0.0.1:8000/servers/1/checks \
    -H 'Content-Type: application/json' -H 'X-API-Key: dev-secret-key' \
    -d '{"metric":"disk_usage","value":42.5,"status":"OK"}'
{"id":1,"server_id":1,"metric":"disk_usage","value":42.5,"status":"OK"}

# list (no auth, newest first)
$ curl -s http://127.0.0.1:8000/servers/1/checks
[{"id":1,"server_id":1,"metric":"disk_usage","value":42.5,"status":"OK","created_at":"..."}]

# a server that doesn't exist → 404 (the body must show no SQL or table names)
$ curl -s http://127.0.0.1:8000/servers/9999
{"detail":"server not found"}
```

> Note: the 404 message above is shown in English here; the Japanese original sample
> reads `{"detail":"サーバーが見つかりません"}` ("server not found"). The exact wording
> is your choice — the tests do not assert the message text. What they do assert is
> that the error body leaks no internals (no "sqlite", "traceback", "select ", "sql").

## Self-check points

- [ ] You produced each of 401 (no key / wrong key), 404 (doesn't exist), 409 (duplicate), 422 (invalid shape)
- [ ] GET passes without the key / POST requires the key
- [ ] The checks list comes back newest first, and ?limit= works
- [ ] Error bodies show no internal details
- [ ] /docs shows your own API's manual
