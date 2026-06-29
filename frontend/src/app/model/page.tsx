"use client";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { fmtPrice } from "@/lib/format";
import { Card, SectionTitle, StateBlock, ChartSkeleton } from "@/components/ui";
import { ActualVsForecast, LossCurve } from "@/components/EvalCharts";

const METRIC_LABELS: Record<string, string> = {
  MAE: "MAE",
  RMSE: "RMSE",
  "MAPE(%)": "MAPE (%)",
  DirectionalAcc: "Độ chính xác hướng",
};

export default function ModelPage() {
  const ev = useApi(() => api.evaluate(), []);

  return (
    <div className="fade-in flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Đánh giá mô hình</h1>
        <p className="mt-1 text-muted">
          Độ đo trên tập test (giá gốc) so với baseline naive (random walk), biểu đồ Actual vs Forecast và
          đường học (loss).
        </p>
      </div>

      {ev.loading ? (
        <Card>
          <ChartSkeleton height={320} />
        </Card>
      ) : ev.error ? (
        <Card>
          <StateBlock
            kind="error"
            title="Chưa lấy được kết quả đánh giá"
            message={ev.status === 503 ? "Backend chưa có model đã train." : ev.error ?? undefined}
            onRetry={ev.reload}
          />
        </Card>
      ) : ev.data ? (
        <>
          {/* Bảng metric: Transformer vs Naive */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {Object.keys(METRIC_LABELS).map((k) => {
              const m = ev.data!.metrics[k];
              const n = ev.data!.naive[k];
              const isDir = k === "DirectionalAcc";
              return (
                <Card key={k} className="p-4">
                  <div className="text-xs text-muted">{METRIC_LABELS[k]}</div>
                  <div className="mt-1 text-2xl font-semibold tabular">
                    {m == null ? "—" : isDir ? `${(m * 100).toFixed(1)}%` : fmtPrice(m, k === "MAPE(%)" ? 2 : 3)}
                  </div>
                  <div className="mt-1 text-xs text-muted tabular">
                    Naive: {n == null ? "N/A" : isDir ? "N/A" : fmtPrice(n, k === "MAPE(%)" ? 2 : 3)}
                  </div>
                </Card>
              );
            })}
          </div>

          <p className="text-xs text-muted -mt-2">
            Naive = dự đoán &quot;giá mai = giá nay&quot;. Dự báo 1 phiên thường khó vượt naive về MAE/RMSE;
            giá trị nằm ở độ chính xác hướng và xếp hạng cổ phiếu.
          </p>

          {/* Actual vs Forecast */}
          <Card className="p-5">
            <SectionTitle
              title="Actual vs Forecast"
              hint={ev.data.ticker ? `Mã ${ev.data.ticker} (mã có nhiều mẫu test nhất)` : undefined}
            />
            {ev.data.actual_vs_forecast.length ? (
              <ActualVsForecast data={ev.data.actual_vs_forecast} />
            ) : (
              <StateBlock kind="empty" title="Chưa có dữ liệu test" />
            )}
          </Card>

          {/* Loss curve */}
          <Card className="p-5">
            <SectionTitle title="Đường học (L1 loss)" hint="Train vs Validation theo epoch" />
            {ev.data.history.train_loss.length ? (
              <LossCurve train={ev.data.history.train_loss} val={ev.data.history.val_loss} />
            ) : (
              <StateBlock kind="empty" title="Không có lịch sử huấn luyện" />
            )}
          </Card>
        </>
      ) : null}
    </div>
  );
}
