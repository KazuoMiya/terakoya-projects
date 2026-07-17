# 課題6: デプロイ — 動かす・守る

課題5のAPIは、いま `uvicorn` を**手で**起動している。ターミナルを閉じれば死ぬ。
この課題では、それを**常駐するサービス**に変える。サーバーが再起動しても勝手に立ち上がり、
落ちても勝手に生き返り、玄関（Nginx）の後ろで行儀よく動く形だ。
そして動かすだけでなく**守る**。バックアップは、リストアに成功して初めてバックアップだ。

> この README が課題の「正」だ。コース本文（レッスン proj-23〜26）は、この仕様の
> 読み解きと道しるべ。**この課題に自動採点は無い**。環境の中で起きることは機械が
> 覗けないからだ。修了の証になるのは、完了チェックリストと、あなたの手順書だ。

## 実機の用意 — systemd が動く Ubuntu が1台要る

この課題の相手は systemd（Linuxの常駐サービスの元締め）だ。

- **Windows（WSL2）の人**: いまの Ubuntu がそのまま使える可能性が高い。確認は:
  ```bash
  systemctl list-units --type=service | head -5   # 一覧が出ればsystemdは動いている
  ```
  「System has not been booted with systemd」と出たら、`/etc/wsl.conf` に
  ```ini
  [boot]
  systemd=true
  ```
  を追記し、PowerShell で `wsl --shutdown` してから Ubuntu を開き直す。
- **Mac の人**: Mac に systemd は無い。**Multipass**（Ubuntu の開発元 Canonical 公式の
  無料ツール）で、使い捨ての Ubuntu 仮想マシンを1台立てる。
  ```bash
  multipass launch --name deploy-practice -m 2G -d 10G   # Ubuntu VM を1台（メモリとディスクは余裕を持って）
  multipass shell deploy-practice                        # その中に入る（以後の作業は全部この中）
  ```
  インストールは **canonical.com/multipass（公式サイト）のインストーラ**から（macOS 14以降・Intel/Apple Siliconどちらも対応・無料）。
  壊れたら `multipass delete --purge deploy-practice` で消して作り直せる——
  Docker と同じ、使い捨ての安全網だ。

> **この課題の作業場は「自分のPCの中のLinux」だけ。** 本物のVPSやクラウドは使わない
> （費用と公開リスクの管理はこのコースの外の話だ）。インターネットに公開もしない。

実機の中に、課題のリポジトリと課題5のAPIを用意する。**素のUbuntuには venv も sqlite3 も
入っていない**ので、先に道具を入れる。WSL2の人は課題0で入れた環境がそのまま使えるが、
sqlite3 だけは今回新たに要る:

```bash
sudo apt update && sudo apt install -y python3-venv sqlite3   # venv用とバックアップ用
git clone <あなたのコピーのURL> terakoya-projects              # ★この名前で clone する
cd terakoya-projects                                          #（ユニットファイルのパスがこの名前を前提にしている）
python3 -m venv .venv && source .venv/bin/activate
pip install -r projects/05-web-api/requirements.txt
cp projects/05-web-api/.env.example projects/05-web-api/.env   # ★忘れると起動に失敗する
cd projects/05-web-api && python -m unittest && cd ../..       # 課題5が緑であること
```

`.env` のコピーを忘れると、後でサービスが「Failed to load environment files」で
起動に失敗する（採点テストは .env 無しでも緑になるので、ここで気づきにくい）。

## 動かす① — systemd で常駐させる

`deploy/terakoya-api.service` が穴埋めテンプレートだ。`<あなたのユーザー名>` を
置き換えて `/etc/systemd/system/` に置き、有効化する（手順はテンプレの冒頭コメント）。

押さえるポイントは3つ。

1. **パスは全部絶対パス**。systemd の世界には、あなたの venv も cd も無い
   （課題3の cron で踏んだ罠と同じ構図だ）。
2. **`--host 127.0.0.1` でローカルにだけ待ち受ける**。外への玄関は Nginx に任せる。
3. **秘密は `EnvironmentFile` で .env から**。ユニットファイルに直書きしない。

```bash
sudo systemctl status terakoya-api     # active (running) になっているか
journalctl -u terakoya-api -n 20       # ログは journald が受けている
curl http://127.0.0.1:8000/health      # {"status":"ok"}
```

**常駐の証明を2つ**: ①プロセスを**異常死**させても数秒で生き返る:

```bash
sudo systemctl kill -s SIGKILL terakoya-api   # 強制終了＝異常死を起こす
sleep 5 && curl -s http://127.0.0.1:8000/health   # もう生き返っている
```

`Restart=on-failure` が反応するのは**異常終了だけ**だ。素の `kill`（SIGTERM）は
「行儀よく止まれ」の合図で、systemd はそれをクリーン終了とみなし、再起動しない。
試して違いを見ると、on-failure の意味が体に入る。
②実機を再起動（Multipass なら `multipass restart`）しても、ログインしたらもう動いている
（`enable` の効果）。

## 動かす② — Nginx を玄関に立てる

```bash
sudo apt update && sudo apt install -y nginx
```

`deploy/nginx-terakoya-api.conf` を配置して有効化する（手順はファイル冒頭のコメント）。
**反映の前に必ず `sudo nginx -t`** を実行する。文法ミスのまま reload して玄関を壊さないためだ。

```bash
curl http://localhost/health           # 80番 → Nginx → 127.0.0.1:8000 → API
```

80番で受けて 8000 へ取り次ぐ「リバースプロキシ」ができた。APIを直接外に出さないのは、
TLS・ログ・複数アプリの同居を玄関一か所で面倒みるためだ。

## 守る① — TLS・ログ・バックアップ

**TLS（自己署名で仕組みを知る）**: `deploy/nginx-terakoya-api.conf` の下半分の
コメントを外し、鍵と証明書を作る。そして **`sudo nginx -t` を通してから
`sudo systemctl reload nginx`**（設定を変えたら毎回この2つだ）。次に `https://localhost/health` を叩く
（`curl -k` の `-k` が要る）。ブラウザなら警告が出る。**「暗号化はされているが、
発行者を誰も保証していない」**という意味だ。本物のサイトは Let's Encrypt などの
認証局に署名してもらう。ドメインが要るので、このコースでは仕組みを知るまで。

**ログ**: 新しく作る前に、もう在るものを確認する。
```bash
journalctl -u terakoya-api --since today   # アプリのログ（journald が自動で回収）
ls /var/log/nginx/                          # Nginx のログ
cat /etc/logrotate.d/nginx                  # ローテーション設定は最初から居る
journalctl --disk-usage                     # journald も自分で容量を管理している
```
「ログが際限なく太る」問題は、実は最初から手当てされている。**確認できること**が今回の学びだ。

**バックアップ → リストア演習（この課題の山場）**:
```bash
bash deploy/backup.sh projects/05-web-api/api.db ~/backups
```
そして**本当に壊して、本当に戻す**:

1. curl でデータを2〜3件登録して、一覧が返るのを確認
2. `sudo systemctl stop terakoya-api` → `rm projects/05-web-api/api.db`（**本当に消す**）
3. start して一覧を叩く——データが消えている（空）ことを自分の目で見る
4. stop → バックアップから戻す（`cp ~/backups/api-<日時>.db projects/05-web-api/api.db`）
5. start → 一覧が**元通り**返ることを確認

> 消すのが怖いと感じたら、それが正しい感覚だ。だからこそ、**壊してよい環境のうちに**
> 「戻せること」を体に入れる。リストアをやったことがない人のバックアップは、願掛けと変わらない。

## 守る② — 手順書（リリースとロールバック）

`RUNBOOK.md` を自分の環境の実際のコマンドで埋める。**ロールバックから先に書く**。
戻せないリリースはリリースではない。埋めたら、**手順書だけを見て**もう一周
（コードを1行変えて→リリース手順→ロールバック手順）できるか試す。それが手順書のテストだ。

## 完了チェック（これがそろえば課題6は修了）

- [ ] `systemctl status terakoya-api` が active (running)
- [ ] プロセスを kill しても生き返る／実機を再起動しても勝手に立ち上がる
- [ ] `curl http://localhost/health` が Nginx 経由で通る（`nginx -t` を通してから反映した）
- [ ] `https://localhost/health` が自己署名TLSで通り、警告の意味を自分の言葉で言える
- [ ] journalctl でアプリのログが追える／nginx の logrotate 設定を確認した
- [ ] **リストア演習をやった**——本当に消して、本当に戻した
- [ ] RUNBOOK.md が実コマンドで埋まり、手順書だけ見て一周できた
- [ ] ユニットファイルに秘密が直書きされていない（EnvironmentFile 経由）
- [ ] `RETROSPECTIVE.md` を埋めた

提出はいつもの一周（ブランチ→PR→セルフマージ）。自動採点は無いが、
埋めた RUNBOOK.md と RETROSPECTIVE.md がこの課題の成果物だ。

## 困ったら（逆引き）

| 症状 | 対処 |
|---|---|
| `status` が activating / failed を繰り返す | `journalctl -u terakoya-api -n 50` を読む。だいたい ExecStart のパス間違い（絶対パスか？venv の uvicorn か？） |
| `203/EXEC` エラー | ExecStart のコマンドが存在しない。パスをコピペで確認 |
| ユニットを直したのに変わらない | `sudo systemctl daemon-reload` を忘れている |
| Nginx で 502 Bad Gateway | 玄関は生きているが奥（API）が死んでいる。`systemctl status terakoya-api` へ |
| `nginx -t` でエラー | 出た行番号の前後を見る。セミコロン忘れが定番 |
| WSL2 で systemd が無いと言われる | 上の「実機の用意」の wsl.conf 手順へ |
| Multipass の VM が変になった | `multipass delete --purge deploy-practice` → launch からやり直し（使い捨てだ） |

> **壊しても大丈夫。** 相手は自分のPCの中の Linux だけ。WSL2 もVMも、最悪
> 作り直せる。本物のサーバーには一切触れない。恐る恐る触らなくていい。
