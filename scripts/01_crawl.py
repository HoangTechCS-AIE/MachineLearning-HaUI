"""Bước 1: Crawl dữ liệu giao dịch từ FiinQuantX -> data/raw/*.csv

Yêu cầu: file .env có FIINQUANT_USERNAME / FIINQUANT_PASSWORD và đã cài fiinquantx.
"""
import _bootstrap  # noqa: F401

from src.config import load_config
from src.data.crawl import crawl_all

if __name__ == "__main__":
    crawl_all(load_config())
