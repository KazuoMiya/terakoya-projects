"""課題5: 点検結果管理API（あなたが実装する）。

課題1〜4で作ってきた道具は、結果を画面とファイルに出していた。
この課題では、結果を「受け取って・貯めて・見せる」側——Web API——を作る。
課題7（統合監視）では、課題1のCLIがこのAPIに報告を送ることになる。

雛形には /health だけ実装してある。まずこれを動かして「一周」を見てから、
残りのエンドポイントを README の仕様どおりに足していく。

起動（開発用サーバー。venv の中で）:
    uvicorn app:app --reload --app-dir src
ブラウザで http://127.0.0.1:8000/docs を開くと、APIの説明書が自動でできている。

認証: 書き込み系（POST）は、リクエストヘッダ X-API-Key が .env の API_KEY と
一致したときだけ通す。読み取り系（GET）は認証なしでよい。

Project 5: Check-Results API (you implement this).

The tools you built in Projects 1-4 printed their results to the screen and
to files. In this project you build the other side — the Web API that
receives, stores, and serves those results. In Project 7 (integrated
monitoring), the Project 1 CLI will send its reports to this API.

The skeleton implements only /health. Get that running first and see one
full lap, then add the remaining endpoints exactly as the README specifies.

Start (development server, inside the venv):
    uvicorn app:app --reload --app-dir src
Open http://127.0.0.1:8000/docs in a browser — the API documentation is
generated automatically.

Auth: write operations (POST) pass only when the X-API-Key request header
matches API_KEY in .env. Read operations (GET) need no auth.
"""
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

import db

load_dotenv()
API_KEY = os.environ.get("API_KEY", "")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """起動時にテーブルを用意する。この関数はおまじないでよい（起動と終了の間で yield）。

    Prepares the tables at startup. You may treat this function as boilerplate
    (it yields between startup and shutdown).
    """
    db.init_db()
    yield


app = FastAPI(title="Terakoya 点検結果管理API / Check-Results API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health():
    """生きているかの確認。課題7で、このAPI自体が監視される側になる。

    Liveness check. In Project 7, this API itself becomes the monitored side.
    """
    return {"status": "ok"}


# ── ここから下を実装する ── / ── Implement everything below this line ──
#
# ★TODO★ README の仕様どおりに、次のエンドポイントを作る。
#         Build the following endpoints exactly as the README specifies.
#
#   GET  /servers                 サーバー一覧 / list servers
#   POST /servers                 サーバー登録（要APIキー・検証・重複は409）
#                                 / register a server (API key + validation; duplicate → 409)
#   GET  /servers/{server_id}     1件取得（無ければ404） / get one server (404 if missing)
#   POST /servers/{server_id}/checks   点検結果の記録（要APIキー・検証・404）
#                                      / record a check result (API key + validation; 404)
#   GET  /servers/{server_id}/checks   点検結果の一覧（新しい順・?limit=）
#                                      / list check results (newest first; ?limit=)
#
# 入力の形と検証は Pydantic のモデルで書く（課題5の道しるべ参照）:
# Describe input shapes and validation with Pydantic models (see the Project 5 guide):
#   from pydantic import BaseModel, Field
#   from typing import Literal
#
# エラーで返すのは「使う人が直せる情報」だけ。テーブル名やSQLの断片のような
# 内部情報をクライアントに返さないこと（エラーメッセージも設計のうちだ）。
# Error responses carry only information the caller can act on. Never return
# internals like table names or SQL fragments to the client
# (error messages are part of the design, too).
