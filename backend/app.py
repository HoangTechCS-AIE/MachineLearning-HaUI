"""FastAPI app phục vụ website dự báo cổ phiếu.

Chạy (từ gốc project):
    uvicorn backend.app:app --reload --port 8188

Model + dữ liệu được nạp một lần lúc khởi động (xem backend/inference.py).
Nếu chưa có model, các endpoint trả 503 kèm hướng dẫn — server vẫn chạy.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .inference import engine
from .schemas import (EvalResponse, IndicatorsResponse, PredictResponse,
                      TickersResponse, TopResponse)


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine.load()           # nạp model lúc start (không chặn nếu thiếu file)
    yield


app = FastAPI(title="BTL Học Máy — API dự báo cổ phiếu VN", version="1.0",
              lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    # Cho phép frontend chạy ở bất kỳ cổng localhost nào (3000, 3001, …)
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)


def _guard():
    """503 nếu engine chưa sẵn sàng (chưa có model)."""
    if not engine.ready:
        raise HTTPException(status_code=503, detail=engine.error or "Engine chưa sẵn sàng.")


@app.get("/api/health")
def health():
    return {"ready": engine.ready, "error": engine.error,
            "num_stocks": len(engine.stock2id) if engine.stock2id else 0}


@app.get("/api/tickers", response_model=TickersResponse)
def get_tickers():
    _guard()
    t = engine.tickers()
    return {"count": len(t), "tickers": t}


@app.get("/api/predict/{ticker}", response_model=PredictResponse)
def get_predict(ticker: str, history_points: int = Query(120, ge=30, le=1000)):
    _guard()
    try:
        return engine.predict(ticker.upper(), history_points)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/top", response_model=TopResponse)
def get_top(month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
            top_n: int = Query(10, ge=1, le=100)):
    _guard()
    return engine.top_stocks(month, top_n)


@app.get("/api/indicators/{ticker}", response_model=IndicatorsResponse)
def get_indicators(ticker: str, points: int = Query(180, ge=30, le=2000)):
    _guard()
    try:
        return engine.indicators(ticker.upper(), points)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/evaluate", response_model=EvalResponse)
def get_evaluate(ticker: str | None = Query(None)):
    _guard()
    return engine.evaluate_model(ticker.upper() if ticker else None)


@app.get("/")
def root():
    return {"name": "BTL Học Máy — API dự báo cổ phiếu VN",
            "docs": "/docs", "health": "/api/health"}
