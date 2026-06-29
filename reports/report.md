# BÁO CÁO BÀI TẬP LỚN MÔN HỌC MÁY

## Ứng dụng thuật toán học máy dự đoán xu hướng giá cổ phiếu trên thị trường chứng khoán Việt Nam

> **Sinh viên:** _(điền tên / MSSV)_
> **Lớp / Nhóm:** _(điền)_
> **Giảng viên hướng dẫn:** _(điền)_
> **Trường:** Đại học Công nghiệp Hà Nội (HaUI)

---

## 1. Đặt vấn đề

- **Bối cảnh:** Thị trường chứng khoán Việt Nam (HOSE/HNX/UPCOM) biến động mạnh; dự báo
  giá cổ phiếu là bài toán giá trị nhưng nhiều thách thức (nhiễu, phi tuyến, phụ thuộc thời gian).
- **Mục tiêu:** Xây dựng pipeline học máy dự báo **giá đóng cửa (`close`) phiên kế tiếp**
  cho từng mã, từ đó suy ra **xu hướng tăng/giảm** và chọn **Top-N cổ phiếu tiềm năng**.
- **Phạm vi:** Dữ liệu daily từ `{from_date}` (cấu hình trong `config/config.yaml`),
  mô hình **Transformer** (deep learning).
- **Tham khảo:** kế thừa & tái cấu trúc từ [PhanDaiCuong/DSCT](https://github.com/PhanDaiCuong/DSCT).

## 2. Dữ liệu & Khám phá (EDA)

- **Nguồn:** thư viện **FiinQuantX** (HOSE = VNINDEX, HNX = HNXINDEX, UPCOM = UPCOMINDEX).
- **Trường dữ liệu:** `open, high, low, close, volume, bu, sd, fn, fs, fb` (giá điều chỉnh).
- **Quy mô:** _(điền số mã, số dòng, khoảng thời gian — lấy từ notebook 01_eda)_
- **Đặc trưng kỹ thuật (feature engineering):** SMA20/50/200, EMA20, RSI14, MACD
  (+signal, +diff), Bollinger Bands, ATR14, OBV, Stochastic (%K, %D), ADX.
- _(Chèn hình từ `01_eda.ipynb`: giá & SMA, RSI/MACD.)_

## 3. Phương pháp

### 3.1. Tiền xử lý
- Chia **theo thời gian từng mã** (train/val/test = 70/15/15), **không** xáo trộn xuyên thời gian.
- Chuẩn hoá **MinMax theo từng mã**, **fit scaler chỉ trên tập train** (tránh rò rỉ dữ liệu —
  điểm cải tiến so với DSCT).
- Tạo **cửa sổ trượt**: dùng `input_window = 30` phiên để dự báo 1 phiên kế tiếp.

### 3.2. Mô hình Transformer (`StockTransformer`)
- Mỗi mã có **embedding riêng** (`nn.Embedding`) ghép với chuỗi đặc trưng.
- `Linear` chiếu lên không gian ẩn → **Positional Encoding** → **TransformerEncoder**
  (`n_layers` lớp, `n_heads` head, GELU) → lấy biểu diễn bước cuối → `Linear` dự báo close.
- Siêu tham số (mặc định): `hidden=128, heads=8, layers=3, emb=16, dropout=0.1`.

### 3.3. Huấn luyện
- Optimizer **AdamW** (lr=1e-4, wd=1e-4), scheduler **CosineAnnealingLR**, loss **L1 (MAE)**,
  gradient clipping = 1.0, lưu checkpoint tốt nhất theo val loss.

## 4. Thực nghiệm & Kết quả

### 4.1. Cấu hình thí nghiệm
- _(điền: số epoch, batch size, thiết bị GPU/CPU, thời gian train)_

### 4.2. Độ đo trên tập test (giá gốc)

| Metric | Transformer | Baseline Naive |
|--------|-------------|----------------|
| MAE    | _điền_ | _điền_ |
| RMSE   | _điền_ | _điền_ |
| MAPE (%) | _điền_ | _điền_ |
| Directional Accuracy | _điền_ | N/A (naive dự báo không đổi) |

> **Baseline Naive** = dự đoán "giá ngày mai = giá hôm nay" (random walk). So sánh với
> baseline này là **bắt buộc** để đánh giá khách quan — dự báo giá ngày kế thường rất khó
> vượt naive về MAE/RMSE; giá trị thực nằm ở **directional accuracy** và xếp hạng cổ phiếu.

### 4.3. Biểu đồ Actual vs Forecast
- _(Chèn `reports/figures/actual_vs_forecast.png`)_

![Actual vs Forecast](figures/actual_vs_forecast.png)

### 4.4. Chọn Top-N cổ phiếu
- _(Chèn bảng Top-N từ `scripts/05_select_stocks.py` cho 1 tháng tiêu biểu.)_

## 5. Thảo luận

- Nhận xét: model học được xu hướng đến đâu? Mã nào dự báo tốt/kém?
- Hạn chế: chỉ dùng dữ liệu giá/khối lượng; chưa dùng tin tức, yếu tố vĩ mô; dự báo 1 bước;
  giả định không có chi phí giao dịch khi xếp hạng lợi nhuận.

## 6. Kết luận & Hướng phát triển

- **Kết luận:** _(tóm tắt kết quả chính)_
- **Hướng phát triển:** dự báo nhiều bước; thêm đặc trưng cơ bản (PE/PB/ROE/EPS) & dòng tiền
  khối ngoại; so sánh thêm LSTM/GRU; backtest chiến lược giao dịch có chi phí.

## 7. Cách tái lập (Reproduce)

```bash
pip install -r requirements.txt
pip install --extra-index-url https://fiinquant.github.io/fiinquantx/simple fiinquantx
cp .env.example .env   # điền tài khoản FiinQuant
python scripts/01_crawl.py
python scripts/02_features.py
python scripts/03_train.py
python scripts/04_evaluate.py
python scripts/05_select_stocks.py --month 2024-03
```

## 8. Tài liệu tham khảo

1. PhanDaiCuong, *DSCT — Stock Forecasting Pipeline*, GitHub.
2. Vaswani et al., *Attention Is All You Need*, 2017.
3. Tài liệu thư viện FiinQuantX.
