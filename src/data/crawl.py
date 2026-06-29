"""Crawl dữ liệu giao dịch cổ phiếu VN qua thư viện FiinQuantX.

Đăng nhập bằng credentials trong biến môi trường (file .env) — KHÔNG hardcode như DSCT.

Cài thư viện:
    pip install --extra-index-url https://fiinquant.github.io/fiinquantx/simple fiinquantx

Dùng:
    from src.config import load_config
    from src.data.crawl import crawl_all
    crawl_all(load_config())
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

import pandas as pd

from ..config import Config, load_config
from ..utils import ensure_dir


def login_client(username: Optional[str] = None, password: Optional[str] = None):
    """Đăng nhập FiinQuant. Đọc credentials từ env nếu không truyền trực tiếp."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    username = username or os.getenv("FIINQUANT_USERNAME")
    password = password or os.getenv("FIINQUANT_PASSWORD")
    if not username or not password:
        raise RuntimeError(
            "Thiếu FIINQUANT_USERNAME / FIINQUANT_PASSWORD. "
            "Hãy tạo file .env từ .env.example và điền tài khoản FiinQuant."
        )

    try:
        from FiinQuantX import FiinSession
    except ImportError as e:
        raise ImportError(
            "Chưa cài fiinquantx. Cài bằng:\n"
            "  pip install --extra-index-url "
            "https://fiinquant.github.io/fiinquantx/simple fiinquantx"
        ) from e

    return FiinSession(username=username, password=password).login()


def crawl_exchange(
    client,
    index_code: str,
    fields: List[str],
    from_date: str,
    adjusted: bool = True,
    by: str = "1d",
    max_tickers: Optional[int] = None,
) -> pd.DataFrame:
    """Crawl toàn bộ mã thuộc một index (VD VNINDEX = toàn HOSE)."""
    tickers = client.TickerList(ticker=index_code)
    if max_tickers is not None:
        tickers = tickers[:max_tickers]
    print(f"[crawl] {index_code}: {len(tickers)} mã (from {from_date})")

    data = client.Fetch_Trading_Data(
        realtime=False,
        tickers=tickers,
        fields=fields,
        adjusted=adjusted,
        by=by,
        from_date=from_date,
    ).get_data()
    return data


def crawl_all(cfg: Config | None = None, client=None) -> dict:
    """Crawl tất cả sàn cấu hình trong cfg.data.exchanges, lưu CSV vào raw_dir.

    Trả về dict {exchange_name: csv_path}.
    """
    cfg = cfg or load_config()
    client = client or login_client()
    raw_dir = ensure_dir(cfg.abs_path(cfg.paths.raw_dir))

    out = {}
    for name, index_code in cfg.data.exchanges.items():
        df = crawl_exchange(
            client,
            index_code=index_code,
            fields=cfg.data.fields,
            from_date=cfg.data.from_date,
            adjusted=cfg.data.adjusted,
            by=cfg.data.by,
            max_tickers=cfg.data.max_tickers,
        )
        path = str(Path(raw_dir) / f"{name}_all.csv")
        df.to_csv(path, index=False)
        print(f"[crawl] ✅ {name}: {df.shape} -> {path}")
        out[name] = path
    return out


if __name__ == "__main__":
    crawl_all()
