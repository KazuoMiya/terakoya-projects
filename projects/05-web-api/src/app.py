"""課題5: 点検結果管理API — 参考実装（solutions ブランチ）。

これは「答え」だ。詰まったときの安全網として置いてある。
まず自分で書いてみて、どうしても進めないところだけ覗くのがおすすめ。
"""
import os
from contextlib import asynccontextmanager
from typing import Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

import db

load_dotenv()
API_KEY = os.environ.get("API_KEY", "")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Terakoya 点検結果管理API", version="1.0.0", lifespan=lifespan)


# ── 入力の形（Pydantic モデル）。型を書くと検証がついてくる ──────────────

class ServerIn(BaseModel):
    hostname: str = Field(min_length=1, max_length=64)
    role: str = Field(min_length=1, max_length=32)


class CheckIn(BaseModel):
    metric: str = Field(min_length=1, max_length=64)
    value: float
    # 状態は課題1から使ってきた4値だけ。それ以外は入口で弾く（422）。
    status: Literal["OK", "WARNING", "CRITICAL", "UNKNOWN"]


# ── 認証。書き込み系だけ、X-API-Key を検める ───────────────────────────

def require_api_key(x_api_key):
    """鍵が違えば 401。メッセージには理由以上のことを書かない。"""
    if not API_KEY or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="APIキーが必要です")


# ── エンドポイント ───────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/servers")
def list_servers():
    return db.list_servers()


@app.post("/servers", status_code=201)
def create_server(body: ServerIn, x_api_key: Optional[str] = Header(default=None)):
    require_api_key(x_api_key)
    # 重複は「入力ミス」ではなく「状態の衝突」なので 422 ではなく 409。
    if db.get_server_by_hostname(body.hostname) is not None:
        raise HTTPException(status_code=409, detail="その hostname は登録済みです")
    new_id = db.insert_server(body.hostname, body.role)
    return {"id": new_id, "hostname": body.hostname, "role": body.role}


@app.get("/servers/{server_id}")
def get_server(server_id: int):
    server = db.get_server(server_id)
    if server is None:
        # 内部情報（テーブル名・SQL）は出さない。使う人が直せる情報だけ。
        raise HTTPException(status_code=404, detail="サーバーが見つかりません")
    return server


@app.post("/servers/{server_id}/checks", status_code=201)
def record_check(server_id: int, body: CheckIn, x_api_key: Optional[str] = Header(default=None)):
    require_api_key(x_api_key)
    if db.get_server(server_id) is None:
        raise HTTPException(status_code=404, detail="サーバーが見つかりません")
    new_id = db.insert_check(server_id, body.metric, body.value, body.status)
    return {"id": new_id, "server_id": server_id, "metric": body.metric,
            "value": body.value, "status": body.status}


@app.get("/servers/{server_id}/checks")
def list_checks(server_id: int, limit: int = Query(default=20, ge=1, le=100)):
    if db.get_server(server_id) is None:
        raise HTTPException(status_code=404, detail="サーバーが見つかりません")
    return db.list_checks(server_id, limit=limit)
