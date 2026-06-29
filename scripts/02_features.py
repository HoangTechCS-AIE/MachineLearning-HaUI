"""Bước 2: Thêm chỉ báo kỹ thuật + gộp -> data/processed/final_merged.csv"""
import _bootstrap  # noqa: F401

from src.config import load_config
from src.data.indicators import build_features

if __name__ == "__main__":
    build_features(load_config())
