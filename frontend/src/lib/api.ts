// Client gọi backend FastAPI. Đổi địa chỉ bằng NEXT_PUBLIC_API_URL (.env.local).
export const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

// ---- Kiểu dữ liệu khớp backend/schemas.py ----
export interface PricePoint {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
}

export interface PredictResponse {
  ticker: string;
  last_date: string;
  last_close: number;
  pred_close: number;
  change: number;
  change_pct: number;
  direction: "up" | "down" | "flat";
  history: PricePoint[];
}

export interface TopStock {
  ticker: string;
  open_first: number;
  pred_close_last: number;
  profit: number;
}
export interface TopResponse {
  month: string;
  available_months: string[];
  top_n: number;
  items: TopStock[];
}

export interface IndicatorPoint {
  date: string;
  close: number | null;
  sma20: number | null;
  sma50: number | null;
  bb_high: number | null;
  bb_low: number | null;
  rsi14: number | null;
  macd: number | null;
  macd_signal: number | null;
  macd_diff: number | null;
  stoch_k: number | null;
  stoch_d: number | null;
}
export interface IndicatorsResponse {
  ticker: string;
  latest_score: number | null;
  signal: string;
  points: IndicatorPoint[];
}

export interface ForecastPoint {
  date: string;
  actual: number | null;
  pred: number | null;
}
export interface EvalResponse {
  ticker: string;
  metrics: Record<string, number | null>;
  naive: Record<string, number | null>;
  history: { train_loss: number[]; val_loss: number[] };
  actual_vs_forecast: ForecastPoint[];
}

export interface HealthResponse {
  ready: boolean;
  error: string | null;
  num_stocks: number;
}

// Lỗi mang theo HTTP status để UI phân biệt 503 (chưa có model) vs 404.
export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function getJSON<T>(path: string): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  } catch {
    throw new ApiError(0, `Không kết nối được backend (${API_URL}). Đã chạy uvicorn chưa?`);
  }
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j?.detail) detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => getJSON<HealthResponse>("/api/health"),
  tickers: () => getJSON<{ count: number; tickers: string[] }>("/api/tickers"),
  predict: (ticker: string, points = 180) =>
    getJSON<PredictResponse>(`/api/predict/${encodeURIComponent(ticker)}?history_points=${points}`),
  top: (month?: string, topN = 10) =>
    getJSON<TopResponse>(`/api/top?top_n=${topN}${month ? `&month=${month}` : ""}`),
  indicators: (ticker: string, points = 180) =>
    getJSON<IndicatorsResponse>(`/api/indicators/${encodeURIComponent(ticker)}?points=${points}`),
  evaluate: (ticker?: string) =>
    getJSON<EvalResponse>(`/api/evaluate${ticker ? `?ticker=${encodeURIComponent(ticker)}` : ""}`),
};
