# MachineLearning-HaUI — Dự báo giá cổ phiếu TTCK Việt Nam bằng Transformer

> Bài tập lớn (BTL) môn **Học Máy** — *Ứng dụng thuật toán học máy dự đoán xu hướng giá
> cổ phiếu trên thị trường chứng khoán Việt Nam.*

Dự án xây dựng pipeline dự báo **giá đóng cửa (`close`) phiên kế tiếp** cho cổ phiếu VN
(HOSE/HNX/UPCOM) bằng mô hình **Transformer (PyTorch)**, kèm phân tích kỹ thuật và
chọn Top-N cổ phiếu tiềm năng. Tham khảo cách làm từ
[PhanDaiCuong/DSCT](https://github.com/PhanDaiCuong/DSCT), được tái cấu trúc thành
một dự án Python gọn gàng, tái lập được.

## Pipeline

```
crawl (FiinQuantX)  ->  chỉ báo kỹ thuật  ->  tiền xử lý/window  ->  Transformer
        |                     |                      |                    |
   data/raw/*.csv     data/processed/*.csv      sliding window      models/model.pt
                                                                          |
                                          đánh giá (MAE/RMSE/MAPE) + chọn Top-N cổ phiếu
```

## Cài đặt

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Thư viện crawl (cần tài khoản FiinQuant):
pip install --extra-index-url https://fiinquant.github.io/fiinquantx/simple fiinquantx
cp .env.example .env   # điền FIINQUANT_USERNAME / FIINQUANT_PASSWORD
```

## Chạy

```bash
python scripts/01_crawl.py          # crawl -> data/raw/
python scripts/02_features.py       # thêm chỉ báo + gộp -> data/processed/final_merged.csv
python scripts/03_train.py          # train Transformer -> models/
python scripts/04_evaluate.py       # metrics + biểu đồ -> reports/figures/
python scripts/05_select_stocks.py --month 2024-03   # Top-N cổ phiếu
```

> Khuyến nghị train trên **GPU** (Google Colab free GPU) với dữ liệu để trên Google Drive.
> Xem `notebooks/02_demo.ipynb` (mount Drive → train → đóng gói artifacts để tải về).
> Có thể giảm phạm vi mã bằng `data.max_tickers` trong `config/config.yaml` để chạy thử nhanh khi local.

## Website (FastAPI + Next.js)

Sau khi train xong, đặt `models/*` và `data/processed/final_merged.csv` vào repo rồi chạy:

```bash
# 1) Backend API (cổng 8000) — từ thư mục gốc repo
uvicorn backend.app:app --reload --port 8000

# 2) Frontend (cổng 3000) — terminal khác
cd frontend
npm install                 # lần đầu
npm run dev                 # http://localhost:3000
```

Backend nạp model một lần lúc khởi động; nếu chưa có model, API trả 503 và web hiện hướng dẫn
(server vẫn chạy). Đổi địa chỉ backend cho frontend qua `frontend/.env.local`
(`NEXT_PUBLIC_API_URL`).

**4 chức năng:** dự báo giá theo mã · Top-N cổ phiếu · chỉ báo + tín hiệu rule-based · đánh giá mô hình.

**Endpoint chính:** `/api/tickers`, `/api/predict/{ticker}`, `/api/top`, `/api/indicators/{ticker}`,
`/api/evaluate` (docs tự sinh tại `/docs`).

## Cấu trúc thư mục

| Đường dẫn | Vai trò |
|-----------|---------|
| `config/config.yaml` / `config.colab.yaml` | hyperparam & đường dẫn (local / Colab-Drive) |
| `src/data/` | crawl, chỉ báo, scoring, dataset |
| `src/models/transformer.py` | kiến trúc `StockTransformer` |
| `src/train.py` / `evaluate.py` / `predict.py` | train / đánh giá / dự báo & chọn cổ phiếu |
| `backend/` | API FastAPI phục vụ website (`app.py`, `inference.py`, `schemas.py`) |
| `frontend/` | Web Next.js + TypeScript + Tailwind (4 trang) |
| `scripts/` | CLI mỏng chạy tuần tự |
| `notebooks/` | EDA & demo Colab/Drive |
| `reports/` | hình + báo cáo BTL (`report.md`) |

## Lưu ý

- Tài khoản FiinQuant trong tài liệu gốc là tài khoản nhóm và **có thể đã hết hạn** —
  cần điền tài khoản hợp lệ của riêng anh vào `.env`.
- Các bước sau crawl đều chạy **offline** từ CSV trong `data/`.
