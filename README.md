# Terakoya プロジェクト集 — 実装の一周

学習サイト **[Terakoya](https://terakoya.miya-dca.workers.dev)** のコース
**「実装の一周 — 7つの課題でつくる運用ツール」** の課題リポジトリだ。
サーバー点検・DB点検・ログ解析・構成差分・Web API・デプロイ・統合監視。
この7つの課題を、自分の手で動くツールとして作り上げる。

> **このコースは PC が必須。** ブラウザの中ではなく、自分のPCにPython環境を作って進める。
> まだの人は、コースの **課題0（ローカルでPythonを動かす）** から始めよう。

## 最初に一度だけ

1. 右上の緑の **「Use this template」→「Create a new repository」** で、**自分のコピー**を作る（Public / Private どちらでもよい）。
2. できたリポジトリを、自分のPCに `clone` する。
3. 課題0の `projects/00-setup/check_setup.py` を実行して、環境が整っているか確かめる。

> **壊しても大丈夫。** これはあなた専用のコピーだ。venv とこのフォルダの中だけで
> 全部が起きる。変になったら消して、テンプレートからもう一度作り直せばいい。

## 課題の進め方（共通の一周）

どの課題も、卒業演習と同じ小さな一周で進める。

1. 作業ブランチを切る（例: `git switch -c task1-healthcheck`）
2. その課題のフォルダで実装する
3. `python -m unittest -v` で答え合わせ（**自動採点がある課題**）
4. push → **Pull Request** → 自動採点が **緑 ✓** → セルフマージ
5. `RETROSPECTIVE.md`（振り返り）を埋める

**自動採点が無い課題**もある（DB点検・デプロイなど、環境に依存するもの）。
その課題は、各フォルダの `README.md` の完了チェックリストと `expected-output.md` を
見本に、自分で確認する。修了の証になるのは、緑のチェックとあなたの振り返りだ。

## 課題の一覧

| # | フォルダ | 課題 | 自動採点 | 状態 |
|---|---|---|---|---|
| 0 | `projects/00-setup/` | ローカルでPythonを動かす | 環境チェック | 公開中 |
| 1 | `projects/01-healthcheck/` | サーバーヘルスチェックCLI | あり | 公開中 |
| 2 | `projects/02-db-check/` | DB日次点検（PostgreSQL主線/Oracle選択） | 一部 | 公開中 |
| 3 | `projects/03-log-analysis/` | ログ解析と通知 | あり | 公開中 |
| 4 | `projects/04-config-diff/` | 構成差分と変更系ツール | あり | 公開中 |
| 5 | `projects/05-web-api/` | 点検結果管理API（FastAPI） | あり | 公開中 |
| 6 | `projects/06-deploy/` | デプロイ（動かす・守る） | なし | 公開中 |
| 7 | `projects/07-monitoring/` | 統合監視システム | 一部 | 公開中 |

これで全課題が公開されている。

## 前提

Terakoya の3コース（システムとコードの基礎／インフラ基礎／開発の現場）を修了していること。
特に「開発の現場」の **Git（モジュール3）と卒業演習** は必須だ。

## 困ったら（逆引き）

| 症状 | 対処 |
|---|---|
| `python` と打つと Store が開く／見つからない | 常に `python3` と打つ。課題0の Windows/Mac 編へ |
| パッケージが「入れたのに無い」と言われる | venv を activate し忘れ。`source .venv/bin/activate` |
| `ModuleNotFoundError: No module named 'healthcheck'` | 各課題のフォルダ（例: `projects/01-healthcheck`）の中で `python -m unittest` を実行 |
| `python: command not found` | venv を activate し忘れ。`python` は venv の中にだけ居る（外は `python3`） |
| （課題2）`docker compose up` が動かない | Docker Desktop が起動しているか確認。会社PCなら利用条件を情シスに確認 |
| （課題2）コンテナは動いてるのに接続できない | `docker compose ps` で STATUS が `healthy` か見る。起動直後は数十秒待つ |
| （課題2）`password authentication failed` | `.env` を作ったか（`cp .env.example .env`）。作り直すなら `docker compose down -v` から |
| （課題2）DBが変な状態になった | `docker compose down -v && docker compose up -d` でまっさらに戻る |
| Checks（自動採点）が赤い | 赤いジョブを開き、落ちたテストの出力を読む。そこが直す場所 |
| Checks がそもそも出ない | リポジトリの「Actions」タブでワークフローを有効化 |
| ぐちゃぐちゃになった | このコピーを消して、テンプレートから作り直してよい |

## このリポジトリについて

- 学習用のテンプレートだ。**個別のサポートやレビューは保証しない**。
  質問は Issue ではなく、[Terakoya のコース本文](https://terakoya.miya-dca.workers.dev/) に戻って読み返してほしい。
- コードは **MIT ライセンス**（`LICENSE` 参照）。自由に使ってよい。

---

Made for **[Terakoya](https://terakoya.miya-dca.workers.dev)** ・ 運営: 宮 / [NexusCode](https://www.nexuscode-devs.asia/ja)
