"""Bước 5: Chọn Top-N cổ phiếu theo lợi nhuận dự đoán trong một tháng.

Ví dụ:
    python scripts/05_select_stocks.py --month 2024-03 --top-n 10
Bỏ --month thì tự lấy tháng cuối cùng có trong tập test.
"""
import argparse

import _bootstrap  # noqa: F401

from src.config import load_config
from src.predict import predict_test, select_top_stocks

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", default=None, help="Tháng dạng YYYY-MM")
    ap.add_argument("--top-n", type=int, default=None)
    args = ap.parse_args()

    cfg = load_config()
    top_n = args.top_n or cfg.select.top_n

    pred_df = predict_test(cfg)
    if pred_df.empty:
        raise SystemExit("Không có dự báo nào — kiểm tra model/dữ liệu test.")

    months = sorted(pred_df["timestamp"].dt.strftime("%Y-%m").unique())
    month = args.month or months[-1]
    print(f"Tháng phân tích: {month} (sẵn có: {months})\n")
    print(select_top_stocks(pred_df, month, top_n).to_string(index=False))
