# ============================================================
# Stage 1: Cài đặt thư viện Python (builder)
# ============================================================
FROM python:3.10-slim AS builder

WORKDIR /install

COPY requirements.prod.txt .

# Cài PyTorch CPU-only trước (nhẹ ~200MB thay vì 2GB bản CUDA),
# sau đó cài phần còn lại. Tất cả được đặt vào /install/packages
RUN pip install --no-cache-dir --prefix=/install/packages \
        torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir --prefix=/install/packages \
        -r requirements.prod.txt

# ============================================================
# Stage 2: Image chạy thực tế (runtime) — nhẹ và sạch
# ============================================================
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Chỉ copy thư viện đã cài từ stage builder, không có cache/build tools
COPY --from=builder /install/packages /usr/local

# Copy dữ liệu và model
COPY data/ data/
COPY models/ models/

# Copy mã nguồn backend
COPY backend/ backend/
COPY src/ src/
COPY config/ config/

EXPOSE 8188

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8188"]
