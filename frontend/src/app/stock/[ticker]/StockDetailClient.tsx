"use client";
import { use } from "react";
import Link from "next/link";
import { ArrowLeft } from "@phosphor-icons/react/dist/ssr";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { fmtPrice, fmtPct, fmtSigned, dirClass } from "@/lib/format";
import { Card, SectionTitle, ChartSkeleton, StateBlock, DirectionBadge } from "@/components/ui";
import { TickerCombobox } from "@/components/TickerCombobox";
import { PriceChart } from "@/components/PriceChart";
import { IndicatorCharts } from "@/components/IndicatorCharts";

export default function StockDetailClient({
  params,
}: {
  params: Promise<{ ticker: string }>;
}) {
  const { ticker: raw } = use(params);
  const ticker = decodeURIComponent(raw).toUpperCase();

  const pred = useApi(() => api.predict(ticker, 180), [ticker]);
  const ind = useApi(() => api.indicators(ticker, 180), [ticker]);

  return (
    <div className="fade-in flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link href="/stock" className="text-muted hover:text-text" aria-label="Quay lại">
            <ArrowLeft size={20} />
          </Link>
          <h1 className="text-3xl font-semibold tracking-tight tabular">{ticker}</h1>
        </div>
        <div className="w-full sm:w-72">
          <TickerCombobox placeholder="Đổi mã…" />
        </div>
      </div>

      {/* Card dự báo + biểu đồ giá (chức năng 1) */}
      <Card className="overflow-hidden">
        {pred.loading ? (
          <ChartSkeleton height={440} />
        ) : pred.error ? (
          <StateBlock
            kind="error"
            title={`Không lấy được dự báo cho ${ticker}`}
            message={
              pred.status === 503
                ? "Backend chưa có model đã train."
                : pred.status === 404
                  ? `Mã ${ticker} không có trong mô hình, hoặc chưa đủ dữ liệu.`
                  : pred.error ?? undefined
            }
            onRetry={pred.reload}
          />
        ) : pred.data ? (
          <div>
            {/* Thanh số liệu dự báo */}
            <div className="grid grid-cols-2 sm:grid-cols-4 divide-x divide-border border-b border-border">
              <Metric label="Giá đóng cửa gần nhất" value={fmtPrice(pred.data.last_close)} sub={pred.data.last_date} />
              <Metric
                label="Dự báo phiên kế"
                value={fmtPrice(pred.data.pred_close)}
                valueClass={dirClass(pred.data.change)}
              />
              <Metric
                label="Thay đổi"
                value={fmtSigned(pred.data.change)}
                valueClass={dirClass(pred.data.change)}
              />
              <Metric
                label="Biên độ"
                value={fmtPct(pred.data.change_pct)}
                valueClass={dirClass(pred.data.change)}
                badge={
                  <DirectionBadge
                    direction={pred.data.direction}
                    text={pred.data.direction === "up" ? "Tăng" : pred.data.direction === "down" ? "Giảm" : "Đi ngang"}
                  />
                }
              />
            </div>
            <div className="p-2 sm:p-4">
              <PriceChart
                history={pred.data.history}
                lastDate={pred.data.last_date}
                lastClose={pred.data.last_close}
                predClose={pred.data.pred_close}
                direction={pred.data.direction}
                height={380}
              />
              <p className="px-2 pb-1 text-xs text-muted">
                Đường liền (xanh) là giá đóng cửa lịch sử; đoạn nét đứt là dự báo của mô hình cho phiên kế tiếp.
              </p>
            </div>
          </div>
        ) : null}
      </Card>

      {/* Chỉ báo kỹ thuật + tín hiệu (chức năng 3) */}
      <Card className="p-5">
        <SectionTitle
          title="Chỉ báo kỹ thuật & tín hiệu"
          hint="Phân tích kỹ thuật và điểm rule-based 16 điều kiện (baseline phi-ML)."
          right={
            ind.data ? (
              <div className="flex items-center gap-3">
                <span className="text-sm text-muted">Điểm:</span>
                <span className="tabular font-semibold">{ind.data.latest_score ?? "—"}</span>
                <DirectionBadge
                  direction={(ind.data.latest_score ?? 0) > 0 ? "up" : (ind.data.latest_score ?? 0) < 0 ? "down" : "flat"}
                  text={ind.data.signal}
                />
              </div>
            ) : null
          }
        />
        {ind.loading ? (
          <ChartSkeleton height={150} />
        ) : ind.error ? (
          <StateBlock
            kind="error"
            title="Không lấy được chỉ báo"
            message={ind.status === 404 ? `Mã ${ticker} không có dữ liệu.` : ind.error ?? undefined}
            onRetry={ind.reload}
          />
        ) : ind.data ? (
          <IndicatorCharts points={ind.data.points} />
        ) : null}
      </Card>
    </div>
  );
}

function Metric({
  label,
  value,
  sub,
  valueClass = "",
  badge,
}: {
  label: string;
  value: string;
  sub?: string;
  valueClass?: string;
  badge?: React.ReactNode;
}) {
  return (
    <div className="p-4">
      <div className="text-xs text-muted">{label}</div>
      <div className={`mt-1 text-xl font-semibold tabular ${valueClass}`}>{value}</div>
      {sub && <div className="mt-0.5 text-xs text-muted tabular">{sub}</div>}
      {badge && <div className="mt-1.5">{badge}</div>}
    </div>
  );
}
