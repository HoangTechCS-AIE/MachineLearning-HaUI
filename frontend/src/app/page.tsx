"use client";
import Link from "next/link";
import { ChartLine, Ranking, Pulse, Gauge, CircleNotch } from "@phosphor-icons/react/dist/ssr";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { fmtPct } from "@/lib/format";
import { TickerCombobox } from "@/components/TickerCombobox";
import { Card, StateBlock, TickerLink } from "@/components/ui";

const FEATURES = [
  { href: "/stock", icon: ChartLine, title: "Dự báo giá theo mã", desc: "Biểu đồ lịch sử + dự báo giá đóng cửa phiên kế tiếp." },
  { href: "/top", icon: Ranking, title: "Top-N cổ phiếu", desc: "Xếp hạng theo lợi nhuận dự đoán trong tháng." },
  { href: "/stock", icon: Pulse, title: "Chỉ báo & tín hiệu", desc: "RSI, MACD, Stochastic + điểm rule-based 16 điều kiện." },
  { href: "/model", icon: Gauge, title: "Đánh giá mô hình", desc: "MAE/RMSE/MAPE, độ chính xác hướng, Actual vs Forecast." },
];

export default function HomePage() {
  const health = useApi(() => api.health(), []);
  const top = useApi(() => api.top(undefined, 5), []);

  return (
    <div className="fade-in flex flex-col gap-10">
      {/* Header + tìm kiếm */}
      <section className="flex flex-col gap-5 pt-2">
        <div>
          <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight">
            Dự báo giá cổ phiếu Việt Nam bằng Transformer
          </h1>
          <p className="mt-2 max-w-2xl text-muted">
            Mô hình deep learning dự báo giá đóng cửa phiên kế tiếp cho cổ phiếu HOSE/HNX/UPCOM,
            kèm phân tích kỹ thuật và xếp hạng cổ phiếu tiềm năng.
          </p>
        </div>
        <div className="max-w-xl">
          <TickerCombobox autoFocus />
        </div>
      </section>

      {/* KPI strip */}
      <section className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <Kpi
          label="Trạng thái mô hình"
          value={health.loading ? "…" : health.data?.ready ? "Sẵn sàng" : "Chưa có model"}
          valueClass={health.data?.ready ? "text-up" : "text-down"}
        />
        <Kpi
          label="Số mã theo dõi"
          value={health.loading ? "…" : String(health.data?.num_stocks ?? 0)}
        />
        <Kpi label="Mô hình" value="StockTransformer" valueClass="text-accent" />
      </section>

      {/* Hai cột: launcher + top movers */}
      <section className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3 grid sm:grid-cols-2 gap-3">
          {FEATURES.map((f) => (
            <Link
              key={f.title}
              href={f.href}
              className="group rounded-xl border border-border bg-surface p-5 transition-colors hover:border-accent"
            >
              <f.icon size={24} weight="duotone" className="text-accent" />
              <h3 className="mt-3 font-medium">{f.title}</h3>
              <p className="mt-1 text-sm text-muted">{f.desc}</p>
            </Link>
          ))}
        </div>

        <Card className="lg:col-span-2 p-5">
          <div className="flex items-center justify-between">
            <h3 className="font-medium">Top tăng giá dự đoán</h3>
            {top.data?.month && <span className="text-xs text-muted tabular">{top.data.month}</span>}
          </div>
          <div className="mt-4">
            {top.loading ? (
              <div className="flex items-center gap-2 py-8 text-muted text-sm justify-center">
                <CircleNotch size={16} className="animate-spin" /> Đang tải…
              </div>
            ) : top.error ? (
              <StateBlock
                kind="error"
                title="Chưa lấy được dữ liệu"
                message={top.status === 503 ? "Backend chưa có model đã train." : top.error}
                onRetry={top.reload}
              />
            ) : !top.data?.items.length ? (
              <StateBlock kind="empty" title="Chưa có dự báo nào" />
            ) : (
              <ul className="divide-y divide-border">
                {top.data.items.map((s, i) => (
                  <li key={s.ticker} className="flex items-center justify-between py-2.5">
                    <span className="flex items-center gap-3">
                      <span className="w-4 text-xs text-muted tabular">{i + 1}</span>
                      <TickerLink ticker={s.ticker} />
                    </span>
                    <span className="tabular text-up">{fmtPct(s.profit * 100)}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </Card>
      </section>
    </div>
  );
}

function Kpi({
  label,
  value,
  valueClass = "",
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <Card className="p-4">
      <div className="text-xs text-muted">{label}</div>
      <div className={`mt-1 text-lg font-semibold tabular ${valueClass}`}>{value}</div>
    </Card>
  );
}
