"""Engine inference cho backend: nạp model + artifacts + dữ liệu MỘT LẦN rồi cache.

Tái dùng tối đa code trong src/:
  - load_trained (dựng lại model + scalers + stock2id từ models/)
  - predict_next / load_recent_history / predict_test / select_top_stocks
  - evaluate (metrics), compute_scores (điểm rule-based)

Giả định quan trọng: data/processed/final_merged.csv là ĐÚNG dữ liệu đã train (tải
về cùng model từ Drive). Khi đó prepare_dataframes tái tạo y hệt split/scaler/stock2id,
nên Top-N & evaluate trên tập test khớp với model.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# Đảm bảo import được src/ khi chạy uvicorn từ gốc project
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import (Config, FeaturesConfig, ModelConfig, WindowingConfig,
                        _section, load_config)
from src.data.scoring import REQUIRED, score_single
from src.evaluate import evaluate, load_trained
from src.predict import (load_recent_history, predict_next, predict_test,
                         select_top_stocks)
from src.utils import load_json


def _f(v):
    """Chuyển 1 giá trị -> float hoặc None (NaN không hợp lệ trong JSON)."""
    return None if pd.isna(v) else float(v)


def _series(df: pd.DataFrame, col: str):
    return [_f(v) for v in df[col]] if col in df.columns else [None] * len(df)


def signal_label(score: float | None) -> str:
    """Diễn giải điểm rule-based thành nhãn tiếng Việt."""
    if score is None or pd.isna(score):
        return "Không đủ dữ liệu"
    if score >= 3:
        return "Tích cực mạnh"
    if score >= 1:
        return "Tích cực"
    if score > -1:
        return "Trung lập"
    if score > -3:
        return "Tiêu cực"
    return "Tiêu cực mạnh"


class Engine:
    """Singleton giữ model + dữ liệu trong RAM để phục vụ các request."""

    def __init__(self):
        self.ready = False
        self.error: str | None = None
        self.cfg: Config | None = None
        self.model = None
        self.scalers = None
        self.stock2id = None
        self.df: pd.DataFrame | None = None
        self.pred_df: pd.DataFrame | None = None
        self._eval_cache: dict | None = None
        self.history: dict = {"train_loss": [], "val_loss": []}

    # -------------------------------------------------------------
    def load(self):
        """Nạp toàn bộ artifacts. Nếu thiếu file -> đánh dấu chưa sẵn sàng."""
        try:
            cfg = load_config()                       # paths LOCAL (config.yaml)
            model_dir = Path(cfg.abs_path(cfg.paths.model_dir))

            # Khớp kiến trúc model với lúc train (đọc từ models/config.json),
            # nhưng GIỮ paths local để tìm đúng file trên máy này.
            cfg_json = model_dir / "config.json"
            if cfg_json.exists():
                saved = load_json(cfg_json)
                cfg.model = _section(ModelConfig, saved.get("model", {}))
                cfg.windowing = _section(WindowingConfig, saved.get("windowing", {}))
                cfg.features = _section(FeaturesConfig, saved.get("features", {}))

            self.cfg = cfg
            self.model, self.scalers, self.stock2id, _ = load_trained(cfg)

            self.df = pd.read_csv(cfg.abs_path(cfg.paths.merged_file))
            self.df["timestamp"] = pd.to_datetime(self.df["timestamp"])

            hist_path = model_dir / "history.json"
            if hist_path.exists():
                self.history = load_json(hist_path)

            # Cache dự báo trên tập test (cho Top-N & evaluate) — chạy 1 lần.
            self.pred_df = predict_test(cfg, model=self.model,
                                        scalers=self.scalers, stock2id=self.stock2id)
            self.ready = True
            self.error = None
            print(f"[engine] ✅ sẵn sàng: {len(self.stock2id)} mã, "
                  f"{len(self.df)} dòng, {len(self.pred_df)} dự báo test.")
        except FileNotFoundError as e:
            self.error = (f"Chưa có model/dữ liệu: {e}. Hãy train (Colab) rồi đặt "
                          f"models/* và data/processed/final_merged.csv vào repo.")
            print(f"[engine] ⚠️ {self.error}")
        except Exception as e:  # noqa: BLE001
            self.error = f"Lỗi nạp engine: {type(e).__name__}: {e}"
            print(f"[engine] ❌ {self.error}")

    def _check(self):
        if not self.ready:
            raise RuntimeError(self.error or "Engine chưa sẵn sàng.")

    # -------------------------------------------------------------
    def tickers(self) -> list[str]:
        self._check()
        return sorted(self.stock2id.keys())

    # ---- Chức năng 1: dự báo giá theo mã ----
    def predict(self, ticker: str, history_points: int = 120) -> dict:
        self._check()
        res = predict_next(self.cfg, ticker, self.model, self.scalers,
                           self.stock2id, self.df)
        hist = load_recent_history(self.df, ticker, history_points,
                                   list(self.cfg.features.cols))
        res["history"] = [
            {
                "date": pd.to_datetime(r["timestamp"]).strftime("%Y-%m-%d"),
                "open": _f(r.get("open")), "high": _f(r.get("high")),
                "low": _f(r.get("low")), "close": _f(r.get("close")),
                "volume": _f(r.get("volume")),
            }
            for _, r in hist.iterrows()
        ]
        return res

    # ---- Chức năng 2: Top-N cổ phiếu ----
    def available_months(self) -> list[str]:
        self._check()
        if self.pred_df.empty:
            return []
        return sorted(self.pred_df["timestamp"].dt.strftime("%Y-%m").unique())

    def top_stocks(self, month: str | None, top_n: int) -> dict:
        self._check()
        months = self.available_months()
        if not months:
            return {"month": "", "available_months": [], "top_n": top_n, "items": []}
        month = month or months[-1]
        tbl = select_top_stocks(self.pred_df, month, top_n)
        items = [
            {"ticker": r["ticker"], "open_first": _f(r["open_first"]),
             "pred_close_last": _f(r["pred_close_last"]), "profit": _f(r["profit"])}
            for _, r in tbl.iterrows()
        ]
        return {"month": month, "available_months": months,
                "top_n": top_n, "items": items}

    # ---- Chức năng 3: chỉ báo + tín hiệu ----
    def indicators(self, ticker: str, points: int = 180) -> dict:
        self._check()
        g = self.df[self.df["ticker"] == ticker].copy()
        if g.empty:
            raise KeyError(f"Mã '{ticker}' không có trong dữ liệu.")
        g = g.sort_values("timestamp")

        latest_score = None
        if all(c in g.columns for c in REQUIRED):
            scored = score_single(g)
            latest_score = _f(scored["score"].iloc[-1])

        sub = g.tail(points).reset_index(drop=True)
        cols = ["close", "sma20", "sma50", "bb_high", "bb_low", "rsi14",
                "macd", "macd_signal", "macd_diff", "stoch_k", "stoch_d"]
        series = {c: _series(sub, c) for c in cols}
        dates = [pd.to_datetime(t).strftime("%Y-%m-%d") for t in sub["timestamp"]]
        pts = [
            {"date": dates[i], **{c: series[c][i] for c in cols}}
            for i in range(len(sub))
        ]
        return {"ticker": ticker, "latest_score": latest_score,
                "signal": signal_label(latest_score), "points": pts}

    # ---- Chức năng 4: đánh giá model ----
    def _eval(self) -> dict:
        if self._eval_cache is None:
            self._eval_cache = evaluate(
                self.cfg, model=self.model, scalers=self.scalers,
                stock2id=self.stock2id, plot=False,
            )
        return self._eval_cache

    def evaluate_model(self, ticker: str | None) -> dict:
        self._check()
        ev = self._eval()

        # Chuỗi Actual vs Forecast cho 1 mã (mặc định: mã nhiều mẫu nhất)
        avf_df = self.pred_df
        if ticker is None and not avf_df.empty:
            ticker = avf_df["ticker"].value_counts().idxmax()
        sub = avf_df[avf_df["ticker"] == ticker].sort_values("timestamp") \
            if ticker else avf_df.iloc[0:0]
        avf = [
            {"date": pd.to_datetime(r["timestamp"]).strftime("%Y-%m-%d"),
             "actual": _f(r["close_true"]), "pred": _f(r["close_pred"])}
            for _, r in sub.iterrows()
        ]
        return {
            "ticker": ticker or "",
            "metrics": {k: _f(v) for k, v in ev["metrics"].items()},
            "naive": {k: _f(v) for k, v in ev["naive"].items()},
            "history": {
                "train_loss": [float(x) for x in self.history.get("train_loss", [])],
                "val_loss": [float(x) for x in self.history.get("val_loss", [])],
            },
            "actual_vs_forecast": avf,
        }


# Singleton dùng chung cho app
engine = Engine()
