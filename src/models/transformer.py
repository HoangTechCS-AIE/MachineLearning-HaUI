"""Kiến trúc Transformer dự báo giá cổ phiếu (port & dọn lại từ DSCT).

Ý tưởng: mỗi mã có một embedding riêng (nn.Embedding) ghép vào chuỗi đặc trưng
[open,high,low,close,volume] của 30 phiên gần nhất, đưa qua TransformerEncoder,
lấy biểu diễn ở bước cuối để dự báo giá close phiên kế tiếp.
"""
from __future__ import annotations

import math

import torch
import torch.nn as nn


class PositionalEncoding(nn.Module):
    """Positional encoding sin/cos cố định (không học)."""

    def __init__(self, d_model: int, max_len: int = 5000):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))  # [1, max_len, d_model]

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, T, D]
        return x + self.pe[:, : x.size(1)]


class StockTransformer(nn.Module):
    def __init__(self, num_stocks: int, feature_dim: int, emb_dim: int,
                 hidden_dim: int, n_heads: int, n_layers: int,
                 output_window: int, dropout: float = 0.1):
        super().__init__()
        self.stock_emb = nn.Embedding(num_stocks, emb_dim)
        self.input_proj = nn.Linear(feature_dim + emb_dim, hidden_dim)
        self.pos_enc = PositionalEncoding(hidden_dim)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim, nhead=n_heads, dim_feedforward=hidden_dim * 4,
            dropout=dropout, batch_first=True, activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.dropout = nn.Dropout(dropout)
        self.head = nn.Linear(hidden_dim, output_window)

    def forward(self, x: torch.Tensor, stock_ids: torch.Tensor) -> torch.Tensor:
        # x: [B, T, F]; stock_ids: [B]
        B, T, _ = x.shape
        s_emb = self.stock_emb(stock_ids).unsqueeze(1).expand(B, T, -1)  # [B, T, E]
        h = torch.cat([x, s_emb], dim=-1)        # [B, T, F+E]
        h = self.input_proj(h)                   # [B, T, H]
        h = self.pos_enc(h)
        h = self.encoder(h)                      # [B, T, H]
        h_last = h[:, -1, :]                     # [B, H] — biểu diễn bước cuối
        return self.head(self.dropout(h_last))   # [B, output_window]


def build_model(cfg, num_stocks: int, feature_dim: int) -> StockTransformer:
    """Khởi tạo model từ Config."""
    return StockTransformer(
        num_stocks=num_stocks,
        feature_dim=feature_dim,
        emb_dim=cfg.model.emb_dim,
        hidden_dim=cfg.model.hidden_dim,
        n_heads=cfg.model.n_heads,
        n_layers=cfg.model.n_layers,
        output_window=cfg.windowing.output_window,
        dropout=cfg.model.dropout,
    )
