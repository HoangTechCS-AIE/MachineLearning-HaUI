"""Hệ thống chấm điểm kỹ thuật theo bộ điều kiện (rule-based) — port từ DSCT.

ĐÂY KHÔNG PHẢI mô hình học máy. Dùng để:
  (a) làm baseline phi-ML đối chiếu với Transformer trong báo cáo,
  (b) minh hoạ ý nghĩa từng chỉ báo (notebooks/01_eda.ipynb).

Mỗi điều kiện cộng/trừ một số điểm; tổng `score` càng cao càng "tích cực" ngắn hạn.
Cài đặt vectorized theo từng mã (nhanh hơn vòng lặp từng dòng của DSCT).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Cột chỉ báo cần có (sinh bởi indicators.add_indicators)
REQUIRED = ["sma20", "sma50", "rsi14", "macd", "macd_signal",
            "bb_high", "bb_low", "atr14", "stoch_k", "stoch_d", "obv", "vma20"]


def score_single(df: pd.DataFrame) -> pd.DataFrame:
    """Chấm điểm cho MỘT mã (đã sort theo thời gian, đã có chỉ báo)."""
    df = df.copy()
    close, vol = df["close"], df["volume"]
    score = pd.Series(0.0, index=df.index)

    # 1. Giá trên/dưới cả SMA20 & SMA50
    score += np.where((close > df["sma20"]) & (close > df["sma50"]), 1.0, 0.0)
    score += np.where((close < df["sma20"]) & (close < df["sma50"]), -0.5, 0.0)

    # 2-3. Golden / Death Cross (SMA20 vs SMA50)
    prev20, prev50 = df["sma20"].shift(1), df["sma50"].shift(1)
    score += np.where((prev20 <= prev50) & (df["sma20"] > df["sma50"]), 1.5, 0.0)   # golden
    score += np.where((prev20 >= prev50) & (df["sma20"] < df["sma50"]), -1.5, 0.0)  # death

    # 4. Volume so với VMA20
    score += np.where(vol > df["vma20"], 1.0, -0.5)

    # 5-7. RSI vùng
    score += np.where((df["rsi14"] >= 40) & (df["rsi14"] <= 70), 0.5, 0.0)
    score += np.where(df["rsi14"] > 70, -1.0, 0.0)
    score += np.where(df["rsi14"] < 30, -1.0, 0.0)

    # 8. MACD vs Signal
    score += np.where(df["macd"] > df["macd_signal"], 1.0, -1.0)

    # 9-10. Breakout Bollinger
    score += np.where((close > df["bb_high"]) & (vol > df["vma20"]), 1.5, 0.0)
    score += np.where(close < df["bb_low"], -1.5, 0.0)

    # 11-12. Volume đột biến
    score += np.where(vol > 1.5 * df["vma20"], 1.0, 0.0)
    score += np.where(vol < 0.5 * df["vma20"], -1.0, 0.0)

    # 13-14. Stochastic cross ở vùng quá bán/quá mua
    pk, pd_ = df["stoch_k"].shift(1), df["stoch_d"].shift(1)
    cross_up = (pk <= pd_) & (df["stoch_k"] > df["stoch_d"]) & (df["stoch_k"] < 20)
    cross_down = (pk >= pd_) & (df["stoch_k"] < df["stoch_d"]) & (df["stoch_k"] > 80)
    score += np.where(cross_up, 1.0, 0.0)
    score += np.where(cross_down, -1.0, 0.0)

    # 15. ATR spike (biến động bất thường) -> rủi ro
    atr20 = df["atr14"].rolling(20).mean()
    score += np.where(df["atr14"] > 1.5 * atr20, -1.0, 0.0)

    # 16. OBV xác nhận / phân kỳ với giá
    obv_up = df["obv"] > df["obv"].shift(1)
    close_up = close > close.shift(1)
    score += np.where(obv_up & close_up, 0.5, 0.0)
    score += np.where(close_up & ~obv_up, -1.0, 0.0)

    df["score"] = score
    return df


def compute_scores(df: pd.DataFrame, ticker_col: str = "ticker",
                   time_col: str = "timestamp") -> pd.DataFrame:
    """Chấm điểm cho DataFrame nhiều mã."""
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Thiếu cột chỉ báo {missing}. Chạy add_indicators trước.")
    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col])
    df = df.sort_values([ticker_col, time_col]).reset_index(drop=True)
    parts = [score_single(g) for _, g in df.groupby(ticker_col, sort=False)]
    return pd.concat(parts, axis=0).reset_index(drop=True)


def top_n_by_month(scored: pd.DataFrame, month: str, top_n: int = 10,
                   ticker_col: str = "ticker", time_col: str = "timestamp") -> pd.DataFrame:
    """Top-N mã theo điểm trung bình trong tháng (format month = 'YYYY-MM')."""
    scored = scored.copy()
    scored[time_col] = pd.to_datetime(scored[time_col])
    mask = scored[time_col].dt.strftime("%Y-%m") == month
    sub = scored[mask]
    if sub.empty:
        print(f"⚠️ Không có dữ liệu cho tháng {month}")
        return pd.DataFrame(columns=[ticker_col, "score"])
    avg = (sub.groupby(ticker_col)["score"].mean()
           .reset_index().sort_values("score", ascending=False))
    return avg.head(top_n).reset_index(drop=True)
