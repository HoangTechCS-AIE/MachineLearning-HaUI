// Định dạng số/giá/% theo locale Việt Nam.

export function fmtPrice(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return v.toLocaleString("vi-VN", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function fmtPct(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  const s = v.toLocaleString("vi-VN", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
  return `${v > 0 ? "+" : ""}${s}%`;
}

export function fmtSigned(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  const s = fmtPrice(Math.abs(v), digits);
  return `${v > 0 ? "+" : v < 0 ? "-" : ""}${s}`;
}

export function fmtCompact(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return v.toLocaleString("vi-VN", { notation: "compact", maximumFractionDigits: 1 });
}

// Lớp màu theo chiều tăng/giảm
export function dirClass(v: number | null | undefined): string {
  if (v === null || v === undefined || v === 0) return "text-muted";
  return v > 0 ? "text-up" : "text-down";
}
