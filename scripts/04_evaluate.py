"""Bước 4: Đánh giá trên tập test + vẽ biểu đồ -> reports/figures/"""
import _bootstrap  # noqa: F401

from src.config import load_config
from src.evaluate import evaluate

if __name__ == "__main__":
    evaluate(load_config())
