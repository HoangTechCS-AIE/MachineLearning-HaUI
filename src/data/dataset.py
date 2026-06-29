"""Tiền xử lý: chia theo thời gian, chuẩn hoá theo từng mã, tạo cửa sổ trượt.

Khác biệt quan trọng so với DSCT:
  - DSCT fit MinMaxScaler trên TOÀN BỘ chuỗi rồi mới chia tập -> rò rỉ dữ liệu
    (data leakage). Ở đây **scaler chỉ fit trên phần train**, val/test dùng lại
    scaler đó. Cửa sổ trượt được tạo TRONG từng tập nên không vắt qua ranh giới
    train/val/test.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import Dataset

from ..config import Config, load_config


# ---------------------------------------------------------------
# Mapping mã <-> id (ổn định trên toàn bộ dữ liệu, dùng cho Embedding)
# ---------------------------------------------------------------
def build_stock2id(df: pd.DataFrame, ticker_col: str = "ticker") -> Dict[str, int]:
    stocks = df[ticker_col].unique().tolist()
    return {s: i for i, s in enumerate(stocks)}


# ---------------------------------------------------------------
# Chia theo thời gian từng mã (KHÔNG shuffle xuyên thời gian)
# ---------------------------------------------------------------
def split_per_stock(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    ticker_col: str = "ticker",
    time_col: str = "timestamp",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Mỗi mã: sắp theo thời gian rồi cắt train/val/test theo tỉ lệ."""
    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col])
    df = df.sort_values([ticker_col, time_col]).reset_index(drop=True)

    train_parts, val_parts, test_parts = [], [], []
    for _, g in df.groupby(ticker_col, sort=False):
        n = len(g)
        i_tr = int(n * train_ratio)
        i_va = int(n * (train_ratio + val_ratio))
        train_parts.append(g.iloc[:i_tr])
        val_parts.append(g.iloc[i_tr:i_va])
        test_parts.append(g.iloc[i_va:])

    cat = lambda parts: pd.concat(parts, axis=0).reset_index(drop=True)
    return cat(train_parts), cat(val_parts), cat(test_parts)


# ---------------------------------------------------------------
# Chuẩn hoá MinMax theo từng mã — FIT TRÊN TRAIN
# ---------------------------------------------------------------
def fit_scalers(train_df: pd.DataFrame, feature_cols: List[str],
                ticker_col: str = "ticker") -> Dict[str, MinMaxScaler]:
    scalers: Dict[str, MinMaxScaler] = {}
    for s, g in train_df.groupby(ticker_col, sort=False):
        if len(g) == 0:
            continue
        sc = MinMaxScaler()
        sc.fit(g[feature_cols].values)
        scalers[s] = sc
    return scalers


def apply_scalers(df: pd.DataFrame, scalers: Dict[str, MinMaxScaler],
                  feature_cols: List[str], stock2id: Dict[str, int],
                  ticker_col: str = "ticker") -> pd.DataFrame:
    """Transform df bằng scaler đã fit; bỏ mã không có scaler. Thêm cột stock_id."""
    parts = []
    for s, g in df.groupby(ticker_col, sort=False):
        if s not in scalers:
            continue
        g = g.copy()
        g[feature_cols] = scalers[s].transform(g[feature_cols].values)
        g["stock_id"] = stock2id[s]
        parts.append(g)
    if not parts:
        return df.iloc[0:0].assign(stock_id=pd.Series(dtype=int))
    return pd.concat(parts, axis=0).reset_index(drop=True)


def inverse_target(scaler: MinMaxScaler, scaled_vals: np.ndarray,
                   feature_cols: List[str], target_col: str) -> np.ndarray:
    """Đảo scale RIÊNG cột target từ giá trị đã chuẩn hoá về giá gốc."""
    j = feature_cols.index(target_col)
    scaled_vals = np.asarray(scaled_vals).reshape(-1)
    return (scaled_vals - scaler.min_[j]) / scaler.scale_[j]


# ---------------------------------------------------------------
# Dataset cửa sổ trượt đa mã
# ---------------------------------------------------------------
class MultiStockDataset(Dataset):
    """Tạo mẫu (x_window, y, stock_id) cho từng mã trong df đã chuẩn hoá."""

    def __init__(self, df: pd.DataFrame, feature_cols: List[str], target_col: str,
                 input_window: int, output_window: int,
                 ticker_col: str = "ticker"):
        import torch  # local import để module nhẹ khi chỉ dùng hàm tiền xử lý

        self.torch = torch
        self.feature_cols = feature_cols
        self.samples: List[Tuple[np.ndarray, np.ndarray, int]] = []
        target_idx = feature_cols.index(target_col)

        for _, g in df.groupby("stock_id", sort=False):
            values = g[feature_cols].values.astype(np.float32)  # [T, F]
            sid = int(g["stock_id"].iloc[0])
            T = len(values)
            for i in range(T - input_window - output_window + 1):
                x = values[i:i + input_window]
                y = values[i + input_window:i + input_window + output_window, target_idx]
                self.samples.append((x, y.astype(np.float32), sid))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        x, y, sid = self.samples[idx]
        return (self.torch.from_numpy(x),
                self.torch.from_numpy(y),
                self.torch.tensor(sid, dtype=self.torch.long))


# ---------------------------------------------------------------
# Orchestration: từ file merged -> các df đã scale + scalers + mapping
# ---------------------------------------------------------------
def prepare_dataframes(cfg: Config | None = None, df: pd.DataFrame | None = None) -> dict:
    """Đọc final_merged.csv (hoặc nhận df), chia tập, fit scaler trên train, transform.

    Trả về dict: train/val/test (đã scale), scalers, stock2id, feature_cols, target_col.
    """
    cfg = cfg or load_config()
    feature_cols = list(cfg.features.cols)
    target_col = cfg.features.target_col

    if df is None:
        df = pd.read_csv(cfg.abs_path(cfg.paths.merged_file))
    df = df.dropna(subset=feature_cols).copy()

    stock2id = build_stock2id(df)
    train_df, val_df, test_df = split_per_stock(
        df, cfg.split.train_ratio, cfg.split.val_ratio
    )
    scalers = fit_scalers(train_df, feature_cols)

    return {
        "train": apply_scalers(train_df, scalers, feature_cols, stock2id),
        "val": apply_scalers(val_df, scalers, feature_cols, stock2id),
        "test": apply_scalers(test_df, scalers, feature_cols, stock2id),
        "scalers": scalers,
        "stock2id": stock2id,
        "feature_cols": feature_cols,
        "target_col": target_col,
    }


def make_dataset(df_scaled: pd.DataFrame, cfg: Config) -> MultiStockDataset:
    return MultiStockDataset(
        df_scaled, list(cfg.features.cols), cfg.features.target_col,
        cfg.windowing.input_window, cfg.windowing.output_window,
    )
