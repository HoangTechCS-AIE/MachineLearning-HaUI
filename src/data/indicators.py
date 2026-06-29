"""Tính chỉ báo phân tích kỹ thuật bằng pandas thuần.

DSCT dùng `client.FiinIndicator()` (gắn với tài khoản FiinQuant). Ở đây ta cài đặt
lại các chỉ báo bằng công thức chuẩn để pipeline CHẠY OFFLINE được (không cần
client) và minh bạch phần feature engineering cho báo cáo. Bộ chỉ báo & tên cột
giữ tương đương DSCT: SMA/EMA/RSI/MACD/Bollinger/ATR/OBV/Stochastic/ADX.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

from ..config import Config, load_config
from ..utils import ensure_dir


# ---------------------------------------------------------------
# Từng chỉ báo (đầu vào là Series/giá của MỘT mã, đã sort theo thời gian)
# ---------------------------------------------------------------
def sma(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window).mean()


def ema(s: pd.Series, window: int) -> pd.Series:
    return s.ewm(span=window, adjust=False).mean()


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """RSI theo phương pháp Wilder."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    avg_loss = loss.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line, macd_line - signal_line


def bollinger(close: pd.Series, window: int = 20, n_std: float = 2.0):
    mid = close.rolling(window).mean()
    std = close.rolling(window).std(ddof=0)
    return mid + n_std * std, mid - n_std * std


def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    return tr.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = np.sign(close.diff()).fillna(0)
    return (direction * volume).cumsum()


def stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
               window: int = 14, smooth_d: int = 3):
    lowest = low.rolling(window).min()
    highest = high.rolling(window).max()
    k = 100 * (close - lowest) / (highest - lowest).replace(0, np.nan)
    d = k.rolling(smooth_d).mean()
    return k, d


def adx(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14):
    """Trả về (adx, +DI, -DI) theo Wilder."""
    up = high.diff()
    down = -low.diff()
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    plus_dm = pd.Series(plus_dm, index=high.index)
    minus_dm = pd.Series(minus_dm, index=high.index)

    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)

    atr_w = tr.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1 / window, adjust=False, min_periods=window).mean() / atr_w
    minus_di = 100 * minus_dm.ewm(alpha=1 / window, adjust=False, min_periods=window).mean() / atr_w
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx_line = dx.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    return adx_line, plus_di, minus_di


# ---------------------------------------------------------------
# Lắp ráp cho 1 mã / cho cả DataFrame nhiều mã
# ---------------------------------------------------------------
def add_indicators_single(df: pd.DataFrame) -> pd.DataFrame:
    """Thêm chỉ báo cho DataFrame của MỘT mã (đã sort theo timestamp)."""
    df = df.copy()
    c, h, l, v = df["close"], df["high"], df["low"], df["volume"]

    df["sma20"], df["sma50"], df["sma200"] = sma(c, 20), sma(c, 50), sma(c, 200)
    df["ema20"] = ema(c, 20)
    df["rsi14"] = rsi(c, 14)
    df["macd"], df["macd_signal"], df["macd_diff"] = macd(c)
    df["bb_high"], df["bb_low"] = bollinger(c, 20, 2.0)
    df["atr14"] = atr(h, l, c, 14)
    df["obv"] = obv(c, v)
    df["stoch_k"], df["stoch_d"] = stochastic(h, l, c, 14, 3)
    df["adx"], df["adx_pos"], df["adx_neg"] = adx(h, l, c, 14)
    df["vma20"] = v.rolling(20).mean()  # phục vụ scoring
    return df


def add_indicators(df: pd.DataFrame, ticker_col: str = "ticker",
                   time_col: str = "timestamp") -> pd.DataFrame:
    """Thêm chỉ báo cho DataFrame nhiều mã (group theo ticker)."""
    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col])
    df = df.sort_values([ticker_col, time_col]).reset_index(drop=True)
    parts = [add_indicators_single(g) for _, g in df.groupby(ticker_col, sort=False)]
    return pd.concat(parts, axis=0).reset_index(drop=True)


def build_features(cfg: Config | None = None) -> str:
    """Đọc mọi CSV trong raw_dir, thêm chỉ báo, lưu *_with_TA.csv, gộp final_merged.csv.

    Trả về đường dẫn file merge.
    """
    cfg = cfg or load_config()
    raw_dir = Path(cfg.abs_path(cfg.paths.raw_dir))
    proc_dir = Path(ensure_dir(cfg.abs_path(cfg.paths.processed_dir)))

    # Đọc đệ quy: hỗ trợ CSV trong thư mục con. Bỏ qua file output của chính build_features
    # (nằm trong processed_dir) để không đọc lại; KHÔNG lọc theo "_with_TA" vì data DSCT
    # đặt tên file là *_with_TA.csv.
    proc_resolved = proc_dir.resolve()
    raw_files = sorted(
        p for p in raw_dir.rglob("*.csv") if proc_resolved not in p.resolve().parents
    )
    if not raw_files:
        raise FileNotFoundError(
            f"Không thấy CSV nào trong {raw_dir} (đã tìm cả thư mục con). "
            f"Chạy scripts/01_crawl.py, hoặc trỏ raw_dir vào folder dữ liệu có sẵn."
        )

    merged_parts = []
    for f in raw_files:
        df = pd.read_csv(f)
        df = add_indicators(df)
        out = proc_dir / f"{f.stem}_with_TA.csv"
        df.to_csv(out, index=False)
        print(f"[features] {f.name} -> {out.name} {df.shape}")
        merged_parts.append(df)

    merged = pd.concat(merged_parts, axis=0).reset_index(drop=True)
    merged_path = cfg.abs_path(cfg.paths.merged_file)
    ensure_dir(Path(merged_path).parent)
    merged.to_csv(merged_path, index=False)
    print(f"[features] ✅ merge -> {merged_path} {merged.shape}")
    return merged_path


if __name__ == "__main__":
    build_features()
