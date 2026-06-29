"""Pydantic response models cho API (FastAPI tự sinh docs + validate JSON)."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


# ---- /api/tickers ----
class TickersResponse(BaseModel):
    count: int
    tickers: List[str]


# ---- /api/predict/{ticker} ----
class PricePoint(BaseModel):
    date: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None


class PredictResponse(BaseModel):
    ticker: str
    last_date: str
    last_close: float
    pred_close: float
    change: float
    change_pct: float
    direction: str                 # 'up' | 'down' | 'flat'
    history: List[PricePoint]       # lịch sử giá để vẽ chart


# ---- /api/top ----
class TopStock(BaseModel):
    ticker: str
    open_first: float
    pred_close_last: float
    profit: float                   # lợi nhuận dự đoán (tỉ lệ)


class TopResponse(BaseModel):
    month: str
    available_months: List[str]
    top_n: int
    items: List[TopStock]


# ---- /api/indicators/{ticker} ----
class IndicatorPoint(BaseModel):
    date: str
    close: Optional[float] = None
    sma20: Optional[float] = None
    sma50: Optional[float] = None
    bb_high: Optional[float] = None
    bb_low: Optional[float] = None
    rsi14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_diff: Optional[float] = None
    stoch_k: Optional[float] = None
    stoch_d: Optional[float] = None


class IndicatorsResponse(BaseModel):
    ticker: str
    latest_score: Optional[float] = None
    signal: str                     # nhãn diễn giải điểm rule-based
    points: List[IndicatorPoint]


# ---- /api/evaluate ----
class ForecastPoint(BaseModel):
    date: str
    actual: Optional[float] = None
    pred: Optional[float] = None


class LossCurve(BaseModel):
    train_loss: List[float]
    val_loss: List[float]


class EvalResponse(BaseModel):
    ticker: str
    metrics: dict                   # {MAE, RMSE, MAPE(%), DirectionalAcc}
    naive: dict                     # baseline naive (không có DirectionalAcc)
    history: LossCurve
    actual_vs_forecast: List[ForecastPoint]
