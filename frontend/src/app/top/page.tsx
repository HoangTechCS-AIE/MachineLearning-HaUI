"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { fmtPrice, fmtPct } from "@/lib/format";
import { Card, SectionTitle, StateBlock, TickerLink, ChartSkeleton } from "@/components/ui";
import { ProfitBar } from "@/components/ProfitBar";

export default function TopPage() {
  const [month, setMonth] = useState<string | undefined>(undefined);
  const [topN, setTopN] = useState(10);
  const top = useApi(() => api.top(month, topN), [month, topN]);

  return (
    <div className="fade-in flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Top-N cổ phiếu tiềm năng</h1>
        <p className="mt-1 text-muted">
          Xếp hạng theo lợi nhuận dự đoán trong tháng: (giá dự báo cuối tháng − giá mở đầu tháng) / giá mở.
        </p>
      </div>

      {/* Bộ lọc */}
      <div className="flex flex-wrap items-end gap-4">
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="text-muted">Tháng</span>
          <select
            value={month ?? top.data?.month ?? ""}
            onChange={(e) => setMonth(e.target.value || undefined)}
            className="rounded-md border border-border bg-surface px-3 py-2 text-sm tabular outline-none focus:border-accent"
          >
            {(top.data?.available_months ?? []).map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="text-muted">Số lượng (N)</span>
          <select
            value={topN}
            onChange={(e) => setTopN(Number(e.target.value))}
            className="rounded-md border border-border bg-surface px-3 py-2 text-sm tabular outline-none focus:border-accent"
          >
            {[5, 10, 15, 20].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>
      </div>

      {top.loading ? (
        <Card>
          <ChartSkeleton height={280} />
        </Card>
      ) : top.error ? (
        <Card>
          <StateBlock
            kind="error"
            title="Chưa lấy được Top-N"
            message={top.status === 503 ? "Backend chưa có model đã train." : top.error ?? undefined}
            onRetry={top.reload}
          />
        </Card>
      ) : !top.data?.items.length ? (
        <Card>
          <StateBlock kind="empty" title="Không có dữ liệu cho tháng này" />
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-5">
          {/* Bảng */}
          <Card className="lg:col-span-3 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="text-muted">
                <tr className="border-b border-border text-left">
                  <th className="px-4 py-3 font-medium">#</th>
                  <th className="px-4 py-3 font-medium">Mã</th>
                  <th className="px-4 py-3 font-medium text-right">Giá mở đầu</th>
                  <th className="px-4 py-3 font-medium text-right">Dự báo cuối</th>
                  <th className="px-4 py-3 font-medium text-right">Lợi nhuận DĐ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {top.data.items.map((s, i) => (
                  <tr key={s.ticker} className="hover:bg-surface-2">
                    <td className="px-4 py-3 text-muted tabular">{i + 1}</td>
                    <td className="px-4 py-3"><TickerLink ticker={s.ticker} /></td>
                    <td className="px-4 py-3 text-right tabular">{fmtPrice(s.open_first)}</td>
                    <td className="px-4 py-3 text-right tabular">{fmtPrice(s.pred_close_last)}</td>
                    <td className={`px-4 py-3 text-right tabular ${s.profit >= 0 ? "text-up" : "text-down"}`}>
                      {fmtPct(s.profit * 100)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          {/* Biểu đồ */}
          <Card className="lg:col-span-2 p-5">
            <SectionTitle title="Lợi nhuận dự đoán" hint={`Tháng ${top.data.month}`} />
            <ProfitBar items={top.data.items} />
          </Card>
        </div>
      )}
    </div>
  );
}
