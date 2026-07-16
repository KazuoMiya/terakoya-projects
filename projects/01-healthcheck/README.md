# 課題1: サーバーヘルスチェックCLI

手動の「朝のサーバー点検」を自動化する、コマンドラインツールを作る。
CPU・メモリ・ディスクなどの状態を集めて、**OK / WARNING / CRITICAL** を判定し、
人にも機械にも読める形で出力する。**月曜からそのまま自分の点検に使える**道具だ。

> この README が課題の「正」だ。コース本文（レッスン proj-06〜08）は、この仕様の
> 読み解きと道しるべ。迷ったら、ここに書いてある完了条件へ戻ってくればいい。

## 作るもの

`src/healthcheck.py` を、次のことができる CLI に仕上げる。

1. サーバーの状態を **OSコマンド経由で** 集める（例: `df`・`uptime`・`ps`・`ss`／`netstat`、ログのエラー件数）。最低1項目、できれば「ディスク使用率」と「ロードアベレージ」の2つ以上。
2. 集めた値を **閾値** と比べて判定する（`--warn` と `--crit` の2段）。
3. 結果を **テキスト** と **JSON**（`--json`）の両方で出せる。
4. 全体の状態に応じた **終了コード** で終わる。
5. 途中で1項目が失敗しても、**他の項目は続行**する（部分障害でも全体を止めない）。
6. 何をしたかが **ログ** に残る（`logging`）。

## 状態と終了コード（監視の共通語）

| 状態 | 終了コード | 意味 |
|---|---|---|
| OK | 0 | 正常 |
| WARNING | 1 | 注意（`warn` 以上 `crit` 未満） |
| CRITICAL | 2 | 危険（`crit` 以上） |
| UNKNOWN | 3 | そもそも測れなかった（コマンド失敗など） |

全体の終了コードは、いちばん深刻な状態を採る（**CRITICAL > WARNING > UNKNOWN > OK**）。

> **鉄則**: 「危険（CRITICAL/WARNING）」と「測れない（UNKNOWN）」を絶対に混ぜない。
> ツール自身の故障で本番の異常を騒いだり、逆に握りつぶしたりするのが監視の二大事故だ。
> 「測れなかった」は正直に UNKNOWN と言う。

## 完了条件（これがそろえば課題1は修了）

- [ ] 閾値を引数（`--warn` / `--crit`）で受け取れる
- [ ] OK / WARNING / CRITICAL / UNKNOWN の4状態を区別する（UNKNOWN を CRITICAL に混ぜない）
- [ ] テキスト出力と JSON 出力（`--json`）の両方に対応
- [ ] 全体状態に応じた終了コードで終わる
- [ ] 1項目が失敗しても全体は落ちず、その項目は UNKNOWN になる
- [ ] `logging` で動作の記録が残る
- [ ] **判定ロジックが純関数に分かれていて、テストが緑**（`python -m unittest -v`）
- [ ] README（このファイルの下の「使い方」）を、他人が読んで実行できるように自分の言葉で追記
- [ ] `RETROSPECTIVE.md` を埋めた

## 自動採点が見るところ

自動採点（`tests/test_healthcheck.py`）がテストするのは、`src/healthcheck.py` の
**純関数3つ**だ。まずここを緑にすることが、課題1の背骨になる。

| 関数 | 役割 |
|---|---|
| `judge(value, warn, crit)` | 1つの値を判定して "OK"/"WARNING"/"CRITICAL" を返す |
| `worst_status(statuses)` | 状態のリストから全体の状態（いちばん深刻なもの）を返す |
| `status_to_exit_code(status)` | 状態を終了コード（0/1/2/3）に変換する |

収集・表示・argparse・logging・`main()` は自動採点の対象外（環境で結果が変わるため）。
そこは「使い方」と `expected-output.md` を見本に、自分で組み上げて自己チェックする。

## 進め方（4つのマイルストーン）

一度に全部を作らない。各段で「動くもの」を持ちながら進む。

1. **判定と組み立て** — `judge` / `worst_status` / `status_to_exit_code` を書いて、テストを緑にする。結果を辞書にまとめて JSON で `print` する。
2. **本物の値を集める** — `subprocess.run(...)` で `df` や `uptime` を叩き、必要な数値を取り出す。
3. **例外と終了コード** — 収集失敗を UNKNOWN にして続行。全体状態から終了コードを決める。
4. **道具に仕上げる** — `argparse`（`--warn/--crit/--json`）と `logging` を足し、README を書く。

## テスト

```bash
# この課題のフォルダ（projects/01-healthcheck）の中で
python -m unittest -v
```

## 使い方

<!-- ★ここは、あなたのツールの使い方を自分の言葉で書く。expected-output.md も見本に。 -->

```bash
python src/healthcheck.py --warn 70 --crit 90
python src/healthcheck.py --warn 70 --crit 90 --json
```

## 提出（課題完了の一周）

1. 作業ブランチを切る（例: `git switch -c task1-healthcheck`）
2. 実装して、`python -m unittest -v` が緑になるのを確認
3. push → Pull Request → **自動採点が緑** → セルフマージ
4. `RETROSPECTIVE.md` を埋める

> **壊しても大丈夫。** これはあなた専用のコピーだ。venv とこのフォルダの中だけで完結する。
> 変になったら消して作り直せる。恐る恐る触らなくていい。
