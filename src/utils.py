"""Tiện ích dùng chung: seed, metrics, I/O."""
from __future__ import annotations

import json
import os
import pickle
import random
from pathlib import Path
from typing import Dict

import numpy as np


# ---------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------
def set_seed(seed: int = 42) -> None:
    """Cố định seed cho random / numpy / torch để tái lập kết quả."""
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def get_device(use_cuda: bool = True):
    """Trả về torch.device phù hợp (cuda nếu có và được phép)."""
    import torch

    return torch.device("cuda" if (use_cuda and torch.cuda.is_available()) else "cpu")


# ---------------------------------------------------------------
# Metrics (numpy) — tính trên GIÁ GỐC sau khi inverse-scale
# ---------------------------------------------------------------
def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mape(y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1e-6) -> float:
    """Mean Absolute Percentage Error (%)."""
    return float(np.mean(np.abs((y_true - y_pred) / (np.abs(y_true) + eps))) * 100.0)


def directional_accuracy(y_true: np.ndarray, y_pred: np.ndarray,
                         last_close: np.ndarray) -> float:
    """Tỉ lệ dự đoán ĐÚNG hướng (tăng/giảm) so với giá close gần nhất.

    Cầu nối giữa bài toán regression và "dự đoán xu hướng" trong đề bài.
    Tất cả tham số là mảng 1 chiều cùng độ dài (giá gốc).
    """
    true_dir = np.sign(y_true - last_close)
    pred_dir = np.sign(y_pred - last_close)
    return float(np.mean(true_dir == pred_dir))


def regression_report(y_true: np.ndarray, y_pred: np.ndarray,
                      last_close: np.ndarray | None = None) -> Dict[str, float]:
    """Gói các metric chính lại thành dict."""
    y_true = np.asarray(y_true).reshape(-1)
    y_pred = np.asarray(y_pred).reshape(-1)
    out = {
        "MAE": mae(y_true, y_pred),
        "RMSE": rmse(y_true, y_pred),
        "MAPE(%)": mape(y_true, y_pred),
    }
    if last_close is not None:
        out["DirectionalAcc"] = directional_accuracy(
            y_true, y_pred, np.asarray(last_close).reshape(-1)
        )
    return out


# ---------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------
def ensure_dir(path: str | os.PathLike) -> str:
    """Tạo thư mục nếu chưa có, trả về đường dẫn."""
    Path(path).mkdir(parents=True, exist_ok=True)
    return str(path)


def save_json(obj, path: str | os.PathLike) -> None:
    ensure_dir(Path(path).parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def load_json(path: str | os.PathLike):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_pickle(obj, path: str | os.PathLike) -> None:
    ensure_dir(Path(path).parent)
    with open(path, "wb") as f:
        pickle.dump(obj, f)


def load_pickle(path: str | os.PathLike):
    with open(path, "rb") as f:
        return pickle.load(f)
