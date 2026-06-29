"""Huấn luyện StockTransformer.

Lưu lại: models/model.pt (kèm num_stocks, feature_dim), config.json, stock2id.json,
scalers.pkl — đủ để evaluate / predict tái dựng model và đảo scale.
"""
from __future__ import annotations

import time
from dataclasses import asdict
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from .config import Config, load_config
from .data.dataset import make_dataset, prepare_dataframes
from .models.transformer import build_model
from .utils import ensure_dir, get_device, save_json, save_pickle, set_seed


def train(cfg: Config | None = None, prepared: dict | None = None) -> dict:
    cfg = cfg or load_config()
    set_seed(cfg.train.seed)
    device = get_device(cfg.train.use_cuda)
    print(f"[train] device = {device}")

    # ---- Dữ liệu ----
    prepared = prepared or prepare_dataframes(cfg)
    train_ds = make_dataset(prepared["train"], cfg)
    val_ds = make_dataset(prepared["val"], cfg)
    print(f"[train] train samples = {len(train_ds)} | val samples = {len(val_ds)}")
    if len(train_ds) == 0:
        raise RuntimeError("Tập train rỗng — kiểm tra dữ liệu / input_window / số mã.")

    train_loader = DataLoader(train_ds, batch_size=cfg.train.batch_size,
                              shuffle=True, drop_last=True)
    val_loader = DataLoader(val_ds, batch_size=cfg.train.batch_size,
                            shuffle=False, drop_last=False)

    # ---- Model ----
    num_stocks = len(prepared["stock2id"])
    feature_dim = len(prepared["feature_cols"])
    model = build_model(cfg, num_stocks, feature_dim).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.train.lr,
                                  weight_decay=cfg.train.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=cfg.train.num_epochs
    )
    criterion = nn.L1Loss()

    # ---- Thư mục lưu ----
    model_dir = Path(ensure_dir(cfg.abs_path(cfg.paths.model_dir)))
    best_path = model_dir / "model.pt"
    best_val = float("inf")
    history = {"train_loss": [], "val_loss": []}

    for epoch in range(1, cfg.train.num_epochs + 1):
        t0 = time.time()

        model.train()
        tr_losses = []
        for xb, yb, sid in train_loader:
            xb, yb, sid = xb.to(device), yb.to(device), sid.to(device)
            optimizer.zero_grad()
            loss = criterion(model(xb, sid), yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.train.grad_clip)
            optimizer.step()
            tr_losses.append(loss.item())
        scheduler.step()

        model.eval()
        va_losses = []
        with torch.no_grad():
            for xb, yb, sid in val_loader:
                xb, yb, sid = xb.to(device), yb.to(device), sid.to(device)
                va_losses.append(criterion(model(xb, sid), yb).item())

        tr = sum(tr_losses) / max(len(tr_losses), 1)
        va = sum(va_losses) / max(len(va_losses), 1) if va_losses else float("nan")
        history["train_loss"].append(tr)
        history["val_loss"].append(va)

        if va_losses and va < best_val:
            best_val = va
            torch.save(
                {"model_state_dict": model.state_dict(),
                 "num_stocks": num_stocks, "feature_dim": feature_dim},
                best_path,
            )

        print(f"[train] epoch {epoch:3d}/{cfg.train.num_epochs} "
              f"| train L1 {tr:.5f} | val L1 {va:.5f} | {time.time()-t0:.1f}s")

    # Nếu không có val (best chưa lưu), vẫn lưu model cuối
    if not best_path.exists():
        torch.save(
            {"model_state_dict": model.state_dict(),
             "num_stocks": num_stocks, "feature_dim": feature_dim},
            best_path,
        )

    # ---- Artifacts ----
    save_json(asdict(cfg), model_dir / "config.json")
    save_json(prepared["stock2id"], model_dir / "stock2id.json")
    save_pickle(prepared["scalers"], model_dir / "scalers.pkl")
    save_json(history, model_dir / "history.json")
    print(f"[train] ✅ best val L1 = {best_val:.5f} | artifacts -> {model_dir}")

    return {"model": model, "history": history, "best_val": best_val,
            "model_path": str(best_path), "prepared": prepared}


if __name__ == "__main__":
    train()
