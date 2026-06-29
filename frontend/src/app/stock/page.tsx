"use client";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { TickerCombobox } from "@/components/TickerCombobox";
import { StateBlock, TickerLink } from "@/components/ui";

export default function StockIndexPage() {
  const tickers = useApi(() => api.tickers(), []);

  return (
    <div className="fade-in flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Chọn mã cổ phiếu</h1>
        <p className="mt-1 text-muted">Tìm mã để xem dự báo giá phiên kế tiếp và chỉ báo kỹ thuật.</p>
      </div>
      <div className="max-w-xl">
        <TickerCombobox autoFocus tickers={tickers.data?.tickers} />
      </div>

      {tickers.error ? (
        <StateBlock
          kind="error"
          title="Chưa lấy được danh sách mã"
          message={tickers.status === 503 ? "Backend chưa có model đã train." : tickers.error}
          onRetry={tickers.reload}
        />
      ) : (
        <div>
          <div className="mb-2 text-sm text-muted">
            {tickers.loading ? "Đang tải danh sách…" : `${tickers.data?.count ?? 0} mã có sẵn`}
          </div>
          <div className="flex flex-wrap gap-2">
            {(tickers.data?.tickers ?? []).map((t) => (
              <span
                key={t}
                className="rounded-md border border-border bg-surface px-3 py-1.5 text-sm tabular"
              >
                <TickerLink ticker={t} />
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
