import Link from "next/link";
import { ArrowClockwise, WarningCircle, TrendUp, TrendDown } from "@phosphor-icons/react/dist/ssr";

export function Card({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded-xl border border-border bg-surface ${className}`}>{children}</div>
  );
}

export function SectionTitle({
  title,
  hint,
  right,
}: {
  title: string;
  hint?: string;
  right?: React.ReactNode;
}) {
  return (
    <div className="flex items-end justify-between gap-4 mb-4">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
        {hint && <p className="text-sm text-muted mt-0.5">{hint}</p>}
      </div>
      {right}
    </div>
  );
}

/** Skeleton khớp hình dạng nội dung (thay cho spinner tròn chung chung). */
export function Skeleton({
  className = "",
  style,
}: {
  className?: string;
  style?: React.CSSProperties;
}) {
  return <div className={`animate-pulse rounded-md bg-surface-2 ${className}`} style={style} />;
}

export function ChartSkeleton({ height = 320 }: { height?: number }) {
  return (
    <div className="p-4">
      <Skeleton className="w-full" style={{ height }} />
    </div>
  );
}

/** Khối thông báo dùng chung cho loading/empty/error. */
export function StateBlock({
  kind,
  title,
  message,
  onRetry,
}: {
  kind: "error" | "empty";
  title: string;
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center text-center gap-3 py-14 px-4">
      {kind === "error" && <WarningCircle size={32} className="text-down" weight="duotone" />}
      <div>
        <p className="font-medium">{title}</p>
        {message && <p className="text-sm text-muted mt-1 max-w-md">{message}</p>}
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface-2 px-3 py-1.5 text-sm hover:border-accent transition-colors active:scale-[0.98]"
        >
          <ArrowClockwise size={15} /> Thử lại
        </button>
      )}
    </div>
  );
}

/** Badge hướng tăng/giảm. */
export function DirectionBadge({
  direction,
  text,
}: {
  direction: "up" | "down" | "flat";
  text: string;
}) {
  const map = {
    up: "text-up border-up/30 bg-up/10",
    down: "text-down border-down/30 bg-down/10",
    flat: "text-muted border-border bg-surface-2",
  };
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-sm font-medium tabular ${map[direction]}`}
    >
      {direction === "up" ? <TrendUp size={15} /> : direction === "down" ? <TrendDown size={15} /> : null}
      {text}
    </span>
  );
}

export function TickerLink({ ticker, className = "" }: { ticker: string; className?: string }) {
  return (
    <Link
      href={`/stock/${ticker}`}
      className={`font-semibold tracking-tight hover:text-accent transition-colors ${className}`}
    >
      {ticker}
    </Link>
  );
}
