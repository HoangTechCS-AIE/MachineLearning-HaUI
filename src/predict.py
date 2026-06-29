"""Inference trên tập test + chọn Top-N cổ phiếu theo lợi nhuận DỰ ĐOÁN.

Quy trình chọn mã (port get_top10_stocks của DSCT): trong một tháng, lợi nhuận kỳ vọng
của mỗi mã = (giá close dự đoán cuối tháng − giá open đầu tháng) / open đầu tháng.
Xếp hạng giảm dần và lấy Top-N.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import torch

from .config import Config, load_config
from .data.dataset import inverse_target, prepare_dataframes
from .evaluate import load_trained


def predict_test(cfg: Config | None = None, prepared: dict | None = None,
                 model=None, scalers=None, stock2id=None) -> pd.DataFrame:
    """Sinh dự báo close phiên kế tiếp cho từng dòng trong tập test.

    Trả về DataFrame: [timestamp, ticker, open, close_true, close_pred] (giá gốc).
    """
    cfg = cfg or load_config()
    if model is None:
        model, scalers, stock2id, device = load_trained(cfg)
    else:
        device = next(model.parameters()).device
    prepared = prepared or prepare_dataframes(cfg)
    scalers = scalers or prepared["scalers"]
    stock2id = stock2id or prepared["stock2id"]
    id2stock = {v: k for k, v in stock2id.items()}

    feat = list(cfg.features.cols)
    target_col = cfg.features.target_col
    open_idx, close_idx = feat.index("open"), feat.index(target_col)
    W, O = cfg.windowing.input_window, cfg.windowing.output_window

    test = prepared["test"]
    rows = []
    model.eval()
    with torch.no_grad():
        for s_id, g in test.groupby("stock_id", sort=False):
            g = g.reset_index(drop=True)
            vals = g[feat].values.astype(np.float32)
            T = len(vals)
            n = T - W - O + 1
            if n <= 0:
                continue
            ticker = id2stock[int(s_id)]
            sc = scalers[ticker]

            X = np.stack([vals[i:i + W] for i in range(n)])           # [n, W, F]
            tgt_pos = np.arange(W, W + n)                             # vị trí dòng được dự báo

            xb = torch.from_numpy(X).to(device)
            sid = torch.full((n,), int(s_id), dtype=torch.long, device=device)
            pred_s = model(xb, sid).cpu().numpy().reshape(-1)

            close_pred = inverse_target(sc, pred_s, feat, target_col)
            close_true = inverse_target(sc, vals[tgt_pos, close_idx], feat, target_col)
            open_o = inverse_target(sc, vals[tgt_pos, open_idx], feat, "open")
            ts = g["timestamp"].values[tgt_pos]

            rows.append(pd.DataFrame({
                "timestamp": ts, "ticker": ticker, "open": open_o,
                "close_true": close_true, "close_pred": close_pred,
            }))

    if not rows:
        return pd.DataFrame(columns=["timestamp", "ticker", "open", "close_true", "close_pred"])
    out = pd.concat(rows, axis=0).reset_index(drop=True)
    out["timestamp"] = pd.to_datetime(out["timestamp"])
    return out


def load_recent_history(df: pd.DataFrame, ticker: str, n: int = 120,
                        feature_cols: list | None = None) -> pd.DataFrame:
    """Trả về n dòng OHLCV gần nhất của một mã (giá gốc), đã sort theo thời gian.

    Dùng cho biểu đồ lịch sử giá ở frontend. `df` là final_merged.csv đã đọc.
    """
    feature_cols = feature_cols or ["open", "high", "low", "close", "volume"]
    g = df[df["ticker"] == ticker].copy()
    if g.empty:
        return g
    g["timestamp"] = pd.to_datetime(g["timestamp"])
    g = g.dropna(subset=feature_cols).sort_values("timestamp")
    return g.tail(n).reset_index(drop=True)


def predict_next(cfg: Config, ticker: str, model, scalers, stock2id,
                 df: pd.DataFrame) -> dict:
    """Dự báo giá close PHIÊN KẾ TIẾP cho một mã từ `input_window` phiên gần nhất.

    Khác `predict_test` (chạy trên tập test cũ), hàm này phục vụ inference "live":
    lấy cửa sổ cuối cùng của chuỗi, scale bằng scaler của mã đó, forward model,
    rồi inverse-scale về giá gốc.

    Trả về dict: ticker, last_date, last_close, pred_close, change, change_pct,
    direction ('up'/'down'/'flat').
    """
    feat = list(cfg.features.cols)
    target_col = cfg.features.target_col
    W = cfg.windowing.input_window

    if ticker not in scalers or ticker not in stock2id:
        raise KeyError(f"Mã '{ticker}' không có trong model (scalers/stock2id).")

    g = df[df["ticker"] == ticker].copy()
    g["timestamp"] = pd.to_datetime(g["timestamp"])
    g = g.dropna(subset=feat).sort_values("timestamp").reset_index(drop=True)
    if len(g) < W:
        raise ValueError(
            f"Mã '{ticker}' chỉ có {len(g)} phiên hợp lệ, cần tối thiểu {W}."
        )

    device = next(model.parameters()).device
    sc = scalers[ticker]
    window = g[feat].values[-W:].astype(np.float32)        # [W, F] giá gốc
    window_scaled = sc.transform(window)                    # [W, F] đã chuẩn hoá

    xb = torch.from_numpy(window_scaled).unsqueeze(0).to(device)        # [1, W, F]
    sid = torch.tensor([stock2id[ticker]], dtype=torch.long, device=device)
    model.eval()
    with torch.no_grad():
        pred_s = model(xb, sid).cpu().numpy().reshape(-1)[:1]

    pred_close = float(inverse_target(sc, pred_s, feat, target_col)[0])
    last_close = float(g[target_col].iloc[-1])
    last_date = pd.to_datetime(g["timestamp"].iloc[-1]).strftime("%Y-%m-%d")
    change = pred_close - last_close
    change_pct = change / last_close * 100.0 if last_close else 0.0
    direction = "up" if change > 0 else ("down" if change < 0 else "flat")

    return {
        "ticker": ticker,
        "last_date": last_date,
        "last_close": last_close,
        "pred_close": pred_close,
        "change": change,
        "change_pct": change_pct,
        "direction": direction,
    }


def select_top_stocks(pred_df: pd.DataFrame, month: str, top_n: int = 10) -> pd.DataFrame:
    """Top-N mã theo lợi nhuận dự đoán trong tháng 'YYYY-MM'."""
    df = pred_df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    sub = df[df["timestamp"].dt.strftime("%Y-%m") == month]
    if sub.empty:
        print(f"⚠️ Không có dữ liệu test cho tháng {month}. "
              f"Các tháng có sẵn: {sorted(df['timestamp'].dt.strftime('%Y-%m').unique())}")
        return pd.DataFrame(columns=["ticker", "open_first", "pred_close_last", "profit"])

    res = []
    for ticker, g in sub.groupby("ticker"):
        g = g.sort_values("timestamp")
        open_first = g.iloc[0]["open"]
        close_last = g.iloc[-1]["close_pred"]
        res.append((ticker, open_first, close_last,
                    (close_last - open_first) / open_first))
    out = pd.DataFrame(res, columns=["ticker", "open_first", "pred_close_last", "profit"])
    return out.sort_values("profit", ascending=False).head(top_n).reset_index(drop=True)


if __name__ == "__main__":
    df = predict_test()
    months = sorted(df["timestamp"].dt.strftime("%Y-%m").unique()) if not df.empty else []
    if months:
        print(f"Tháng cuối trong tập test: {months[-1]}")
        print(select_top_stocks(df, months[-1]))
