# Dữ liệu

Thư mục này chứa dữ liệu của pipeline. **Không commit dữ liệu** (đã bị `.gitignore`).

## Cấu trúc

```
data/
├── raw/         # CSV crawl thô từ FiinQuantX theo sàn: HOSE_all.csv, HNX_all.csv, ...
└── processed/   # Đã thêm chỉ báo kỹ thuật + file gộp
    ├── HOSE_with_TA.csv
    └── final_merged.csv   # file dùng để train (gộp các sàn)
```

## Cách lấy dữ liệu

1. Sao chép `.env.example` → `.env`, điền tài khoản FiinQuant hợp lệ.
2. Cài thư viện crawl:
   ```bash
   pip install --extra-index-url https://fiinquant.github.io/fiinquantx/simple fiinquantx
   ```
3. Chạy:
   ```bash
   python scripts/01_crawl.py        # -> data/raw/*.csv
   python scripts/02_features.py     # -> data/processed/*.csv + final_merged.csv
   ```

## Cấu trúc cột (sau crawl)

| Cột | Ý nghĩa |
|-----|---------|
| `timestamp` | ngày giao dịch |
| `ticker` | mã cổ phiếu |
| `open/high/low/close` | giá (đã điều chỉnh) |
| `volume` | khối lượng khớp |
| `bu/sd` | khối lượng mua/bán chủ động |
| `fn/fs/fb` | giao dịch khối ngoại (net/sell/buy) |

Sau bước `02_features.py` có thêm các cột chỉ báo: `sma20/50/200`, `ema20`, `rsi14`,
`macd*`, `bb_high/low`, `atr14`, `obv`, `stoch_k/d`, `adx*`.

> Nếu không có tài khoản FiinQuant, anh có thể tự đặt file CSV đúng định dạng trên vào
> `data/raw/` rồi chạy từ bước `02_features.py`.
