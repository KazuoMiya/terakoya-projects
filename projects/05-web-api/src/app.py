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
    """起動時にテーブルを用意する。この関数はおまじないでよい（起動と終了の間で yield）。"""
    db.init_db()
    yield


app = FastAPI(title="Terakoya 点検結果管理API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health():
    """生きているかの確認。課題7で、このAPI自体が監視される側になる。"""
    return {"status": "ok"}


# ── ここから下を実装する ──────────────────────────────────────────────
#
# ★TODO★ README の仕様どおりに、次のエンドポイントを作る。
#
#   GET  /servers                 サーバー一覧
#   POST /servers                 サーバー登録（要APIキー・検証・重複は409）
#   GET  /servers/{server_id}     1件取得（無ければ404）
#   POST /servers/{server_id}/checks   点検結果の記録（要APIキー・検証・404）
#   GET  /servers/{server_id}/checks   点検結果の一覧（新しい順・?limit=）
#
# 入力の形と検証は Pydantic のモデルで書く（課題5の道しるべ参照）:
#   from pydantic import BaseModel, Field
#   from typing import Literal
#
# エラーで返すのは「使う人が直せる情報」だけ。テーブル名やSQLの断片のような
# 内部情報をクライアントに返さないこと（エラーメッセージも設計のうちだ）。
