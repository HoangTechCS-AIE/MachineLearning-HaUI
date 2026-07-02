"""Đánh giá model trên tập test (giá gốc): MAE/RMSE/MAPE + directional accuracy,
so với baseline naive (giá ngày mai = giá hôm nay), và vẽ Actual vs Forecast.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import torch
from torch.utils.data import DataLoader

from .config import Config, load_config
from .data.dataset import inverse_target, make_dataset, prepare_dataframes
from .models.transformer import build_model
from .utils import (ensure_dir, get_device, load_json, load_pickle,
                    regression_report)


def load_trained(cfg: Config, device=None):
    """Tải checkpoint + scalers + stock2id và dựng lại model.
    Hỗ trợ linh hoạt cả checkpoints chứa dict metadata hoặc chỉ chứa raw state_dict.
    """
    device = device or get_device(cfg.train.use_cuda)
    model_dir = Path(cfg.abs_path(cfg.paths.model_dir))
    
    # Tải stock2id trước để đếm số lượng cổ phiếu (num_stocks) phòng hờ checkpoint cũ thiếu thông tin
    stock2id = load_json(model_dir / "stock2id.json")
    stock2id = {k: int(v) for k, v in stock2id.items()}
    num_stocks = len(stock2id)
    feature_dim = len(cfg.features.cols)
    
    ckpt = torch.load(model_dir / "model.pt", map_location=device)
    
    # Hỗ trợ cả 2 định dạng checkpoint
    if isinstance(ckpt, dict) and "model_state_dict" in ckpt:
        state_dict = ckpt["model_state_dict"]
        num_stocks = ckpt.get("num_stocks", num_stocks)
        feature_dim = ckpt.get("feature_dim", feature_dim)
    else:
        state_dict = ckpt
        
    model = build_model(cfg, num_stocks, feature_dim).to(device)
    model.load_state_dict(state_dict)
    model.eval()
    
    scalers = load_pickle(model_dir / "scalers.pkl")
    return model, scalers, stock2id, device


def _collect_predictions(model, loader, device, target_idx) -> Tuple[np.ndarray, ...]:
    """Chạy inference, trả về (pred_scaled, true_scaled, last_close_scaled, stock_id)."""
    preds, trues, lasts, sids = [], [], [], []
    with torch.no_grad():
        for xb, yb, sid in loader:
            xb_d, sid_d = xb.to(device), sid.to(device)
            p = model(xb_d, sid_d).cpu().numpy().reshape(-1)
            preds.append(p)
            trues.append(yb.numpy().reshape(-1))
            lasts.append(xb[:, -1, target_idx].numpy().reshape(-1))  # close cuối cửa sổ
            sids.append(sid.numpy().reshape(-1))
    return (np.concatenate(preds), np.concatenate(trues),
            np.concatenate(lasts), np.concatenate(sids))


def evaluate(cfg: Config | None = None, prepared: dict | None = None,
             model=None, scalers=None, stock2id=None, plot: bool = True) -> dict:
    cfg = cfg or load_config()
    device = get_device(cfg.train.use_cuda)

    if model is None:
        model, scalers, stock2id, device = load_trained(cfg, device)
    prepared = prepared or prepare_dataframes(cfg)
    scalers = scalers or prepared["scalers"]
    stock2id = stock2id or prepared["stock2id"]

    feature_cols = list(cfg.features.cols)
    target_col = cfg.features.target_col
    target_idx = feature_cols.index(target_col)
    id2stock = {v: k for k, v in stock2id.items()}

    test_ds = make_dataset(prepared["test"], cfg)
    if len(test_ds) == 0:
        raise RuntimeError("Tập test rỗng.")
    loader = DataLoader(test_ds, batch_size=cfg.train.batch_size, shuffle=False)

    pred_s, true_s, last_s, sid = _collect_predictions(model, loader, device, target_idx)

    # Đảo scale về GIÁ GỐC theo từng mã
    pred_o = np.empty_like(pred_s)
    true_o = np.empty_like(true_s)
    last_o = np.empty_like(last_s)
    for s_id in np.unique(sid):
        mask = sid == s_id
        sc = scalers[id2stock[int(s_id)]]
        pred_o[mask] = inverse_target(sc, pred_s[mask], feature_cols, target_col)
        true_o[mask] = inverse_target(sc, true_s[mask], feature_cols, target_col)
        last_o[mask] = inverse_target(sc, last_s[mask], feature_cols, target_col)

    metrics = regression_report(true_o, pred_o, last_close=last_o)
    # Naive = dự đoán "giá mai = giá nay". Không tính DirectionalAcc vì naive dự báo
    # không đổi -> hướng = 0, so sánh directional không có ý nghĩa (hiển thị N/A).
    naive = regression_report(true_o, last_o)

    print("\n===== KẾT QUẢ TRÊN TẬP TEST (giá gốc) =====")
    print(f"{'Metric':<16}{'Transformer':>14}{'Naive':>14}")
    for k in metrics:
        nv = naive.get(k)
        nv_str = f"{nv:>14.4f}" if nv is not None else f"{'N/A':>14}"
        print(f"{k:<16}{metrics[k]:>14.4f}{nv_str}")

    fig_path = None
    if plot:
        fig_path = _plot_actual_vs_forecast(cfg, sid, true_o, pred_o, id2stock)

    return {"metrics": metrics, "naive": naive,
            "y_true": true_o, "y_pred": pred_o, "stock_id": sid,
            "figure": fig_path}


def _plot_actual_vs_forecast(cfg, sid, true_o, pred_o, id2stock,
                             last_points: int = 300) -> str:
    """Vẽ Actual vs Forecast cho mã có nhiều mẫu nhất (cho dễ nhìn)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    counts: Dict[int, int] = defaultdict(int)
    for s in sid:
        counts[int(s)] += 1
    top_sid = max(counts, key=counts.get)
    mask = sid == top_sid
    t, p = true_o[mask][-last_points:], pred_o[mask][-last_points:]

    plt.figure(figsize=(12, 6))
    plt.plot(t, color="red", label="Actual")
    plt.plot(p, color="blue", label="Forecast")
    plt.title(f"Actual vs Forecast — {id2stock.get(top_sid, top_sid)} "
              f"({len(t)} điểm cuối tập test)")
    plt.xlabel("Time Steps")
    plt.ylabel("Close Price")
    plt.legend()
    plt.tight_layout()

    out = Path(ensure_dir(cfg.abs_path(cfg.paths.figures_dir))) / "actual_vs_forecast.png"
    plt.savefig(out, dpi=120)
    plt.close()
    print(f"[evaluate] biểu đồ -> {out}")
    return str(out)


if __name__ == "__main__":
    evaluate()
