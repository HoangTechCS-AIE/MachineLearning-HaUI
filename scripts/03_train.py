"""Bước 3: Huấn luyện StockTransformer -> models/"""
import _bootstrap  # noqa: F401

from src.config import load_config
from src.train import train

if __name__ == "__main__":
    train(load_config())
