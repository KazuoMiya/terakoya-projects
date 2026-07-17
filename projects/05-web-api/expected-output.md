# 出力の見本（自己チェック用）

TestClient の採点が緑なら仕様は満たしている。ここでは「手で一周」の見本を示す。
（curl の代わりに /docs の「Try it out」ボタンでも同じことができる。）

## 手で確かめる一周

```bash
# 生存確認（認証不要）
$ curl -s http://127.0.0.1:8000/health
{"status":"ok"}

# 鍵なしで登録 → 401
$ curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8000/servers \
    -H 'Content-Type: application/json' -d '{"hostname":"web-01","role":"web"}'
401

# 鍵ありで登録 → 201
$ curl -s -X POST http://127.0.0.1:8000/servers \
    -H 'Content-Type: application/json' -H 'X-API-Key: dev-secret-key' \
    -d '{"hostname":"web-01","role":"web"}'
{"id":1,"hostname":"web-01","role":"web"}

# 同じ hostname をもう一度 → 409
# hostname を空にして → 422
# status を "BROKEN" にして → 422

# 点検結果を記録 → 201
$ curl -s -X POST http://127.0.0.1:8000/servers/1/checks \
    -H 'Content-Type: application/json' -H 'X-API-Key: dev-secret-key' \
    -d '{"metric":"disk_usage","value":42.5,"status":"OK"}'
{"id":1,"server_id":1,"metric":"disk_usage","value":42.5,"status":"OK"}

# 一覧（認証不要・新しい順）
$ curl -s http://127.0.0.1:8000/servers/1/checks
[{"id":1,"server_id":1,"metric":"disk_usage","value":42.5,"status":"OK","created_at":"..."}]

# 居ないサーバー → 404（本文に SQL やテーブル名が出ていないこと）
$ curl -s http://127.0.0.1:8000/servers/9999
{"detail":"サーバーが見つかりません"}
```

## 自己チェックの観点

- [ ] 401（鍵なし/違う鍵）・404（居ない）・409（重複）・422（形が不正）を打ち分けた
- [ ] GET は鍵なしで通る／POST は鍵が要る
- [ ] checks の一覧が新しい順で、?limit= が効く
- [ ] エラー本文に内部情報が無い
- [ ] /docs で自分のAPIの説明書が見える
