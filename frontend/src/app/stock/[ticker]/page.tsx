import { API_URL } from "@/lib/api";
import StockDetailClient from "./StockDetailClient";

// Cần thiết cho output: "export" (deploy S3).
// Lấy danh sách mã cổ phiếu từ API lúc build để Next.js tạo trước các trang tĩnh.
export async function generateStaticParams() {
  try {
    const res = await fetch(`${API_URL}/api/tickers`, { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    return (data.tickers as string[]).map((t: string) => ({ ticker: t }));
  } catch {
    return [];
  }
}

export default function StockDetailPage({
  params,
}: {
  params: Promise<{ ticker: string }>;
}) {
  return <StockDetailClient params={params} />;
}
