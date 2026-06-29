# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

University ML coursework (BTL — bài tập lớn) at HaUI: **predict next-day `close` price of Vietnamese
stocks (HOSE/HNX/UPCOM) with a PyTorch Transformer**, then rank Top-N stocks. It is a clean
restructuring of the reference notebooks at [PhanDaiCuong/D	SCT](https://github.com/PhanDaiCuong/DSCT)
into a Python package. **All comments, docstrings, README, and `reports/report.md` are written in
Vietnamese** — keep new code/docs in Vietnamese to match.

This is regression (predict a price), bridged to the assignment's "xu hướng" (trend) wording via a
**directional-accuracy** metric reported alongside MAE/RMSE/MAPE.

## Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install --extra-index-url https://fiinquant.github.io/fiinquantx/simple fiinquantx  # only for crawl
cp .env.example .env   # fill FIINQUANT_USERNAME / FIINQUANT_PASSWORD

# Pipeline (run in order; each consumes the previous step's output)
python scripts/01_crawl.py          # FiinQuantX -> data/raw/*.csv         (needs .env creds)
python scripts/02_features.py       # technical indicators -> data/processed/final_merged.csv
python scripts/03_train.py          # train Transformer -> models/
python scripts/04_evaluate.py       # metrics + plot -> reports/figures/
python scripts/05_select_stocks.py --month 2024-03 --top-n 10

# Inspect resolved config (defaults merged over config.yaml)
python src/config.py

# Run a src module directly (relative imports require -m from project root)
python -m src.train

# Website: backend (port 8000) + frontend (port 3000)
uvicorn backend.app:app --reload --port 8000     # from repo root; loads models/* once at startup
cd frontend && npm install && npm run dev         # NEXT_PUBLIC_API_URL in frontend/.env.local
```

There is **no automated test suite**. Verification is an end-to-end smoke run: set `data.max_tickers`
small and `train.num_epochs` low in `config/config.yaml`, or feed synthetic OHLCV into
`prepare_dataframes(cfg, df)` → `train(cfg, prepared)` → `evaluate(...)` and confirm train loss drops.

## Architecture

**Config-driven.** Everything (paths, hyperparams, exchanges, split ratios) lives in
`config/config.yaml`. `src/config.py` loads it into nested dataclasses (`Config.paths/data/features/ windowing/split/model/train/select`). Missing keys fall back to dataclass defaults via `_section()`.
Don't hardcode paths or hyperparams — add a field and read it from `cfg`.

**Path resolution.** All config paths are relative to `PROJECT_ROOT` (= `src/config.py`'s parent's
parent). Always resolve with `cfg.abs_path(cfg.paths.x)` before touching the filesystem, so code works
regardless of CWD.

**Script entry points.** `scripts/0*.py` are thin CLI wrappers. Each starts with `import _bootstrap`
(see `scripts/_bootstrap.py`) which injects `PROJECT_ROOT` into `sys.path` so `import src...` works when
the script is invoked directly. New scripts must do the same.

**Pipeline data flow** (`src/`):

- `data/crawl.py` — FiinQuantX login from `.env` (never hardcode creds), fetch per-exchange → `data/raw/{HOSE}_all.csv`.
- `data/indicators.py` — TA (SMA/EMA/RSI/MACD/Bollinger/ATR/OBV/Stochastic/ADX) reimplemented in
  **pure pandas** (not `client.FiinIndicator`) so feature/train/eval run **fully offline** — only
  `01_crawl` needs a FiinQuant account. `build_features(cfg)` → `data/processed/final_merged.csv`.
- `data/scoring.py` — 16-condition rule-based score; this is a **non-ML baseline for EDA/report**, not part of training.
- `data/dataset.py` — the preprocessing core (see invariants below).
- `models/transformer.py` — `StockTransformer`: per-stock `nn.Embedding` + Linear projection +
  sinusoidal `PositionalEncoding` + `TransformerEncoder` (GELU) + Linear head. `build_model(cfg, num_stocks, feature_dim)`.
- `train.py` / `evaluate.py` / `predict.py` — train (AdamW + CosineAnnealingLR + L1Loss + grad clip,
  save best-by-val), evaluate (inverse to real prices, metrics vs naive baseline, plot), and Top-N selection.

**Model artifacts** (written to `models/` by `train.py`, all required to reconstruct for eval/predict):
`model.pt` (holds `model_state_dict` + `num_stocks` + `feature_dim`), `stock2id.json`, `scalers.pkl`,
`config.json`, `history.json`. `load_trained(cfg)` in `evaluate.py` rebuilds from these.

**Website (`backend/` + `frontend/`).** The web layer only *serves* the trained artifacts — all ML logic
stays in `src/`.
- `backend/` — FastAPI. `inference.py` holds an `Engine` singleton that loads model + `final_merged.csv`
  **once at startup** and caches `predict_test()` for the Top-N/evaluate endpoints. It rebuilds the
  architecture from `models/config.json` (NOT `config.yaml`) so it matches the trained checkpoint, but
  keeps **local** paths from `config.yaml` (the saved config.json may carry Colab/Drive paths). If model
  files are missing the server still starts and every data endpoint returns **503** (web shows guidance).
- `src/predict.py:predict_next` is the live-inference function the API adds on top of the training code:
  takes the last `input_window` rows for a ticker, scales with that ticker's scaler, predicts next-day close.
- `frontend/` — Next.js 16 (App Router, **params/searchParams are Promises** — unwrap with `use()` in
  client components), Tailwind v4, dark-locked theme. Charts: `lightweight-charts` **v4** API
  (`addAreaSeries`/`addLineSeries`, not the v5 `addSeries`) for price, `recharts` for indicators/eval.
  Talks to backend via `NEXT_PUBLIC_API_URL`.

**Colab/Drive training.** `config/config.colab.yaml` is `config.yaml` with **absolute Drive paths**
(`abs_path()` passes absolute paths through unchanged). `notebooks/02_demo.ipynb` mounts Drive, trains on
GPU, and zips `models/` + `final_merged.csv` to download back into the repo for the website.

## Invariants — do not break these

- **No data leakage.** `MinMaxScaler` is fit on **train only** (`fit_scalers`), then applied to val/test.
  This is a deliberate fix over DSCT, which fit on the full series. Per-stock scalers, keyed by ticker.
- **Chronological split.** `split_per_stock` sorts each ticker by time and slices 70/15/15 — never shuffle
  across time. Sliding windows are built *within* each split (`MultiStockDataset`), so no window straddles a boundary.
- **Inverse-transform only the target.** `inverse_target` un-scales just the `close` column using
  `scaler.min_/scale_` at the target index — don't run full `inverse_transform`.
- **Naive baseline directional accuracy is intentionally N/A.** The naive (random-walk) baseline predicts
  "tomorrow = today", so its direction sign is 0 and never matches ±1. `regression_report` is called
  *without* `last_close` for the naive row so DirectionalAcc is omitted (shown as N/A), not a misleading 0.0.

## Notes

- The FiinQuant account in the original DSCT notebooks is a shared account and **may be expired** — the
  user must supply their own valid creds in `.env`. `data/`, `models/`, `.venv/`, `*.csv`, `*.pt` are gitignored.
- Training ~1600 stocks wants a **GPU** (Colab); see `notebooks/02_demo.ipynb` for an end-to-end run.
  A local `.venv` with CPU torch exists for smoke testing only.

