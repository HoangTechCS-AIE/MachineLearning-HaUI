"use client";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TopStock } from "@/lib/api";

export function ProfitBar({ items }: { items: TopStock[] }) {
  const data = items.map((s) => ({ ticker: s.ticker, profit: +(s.profit * 100).toFixed(2) }));
  return (
    <div className="h-[280px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
          <CartesianGrid stroke="rgba(48,54,61,0.4)" vertical={false} />
          <XAxis dataKey="ticker" tick={{ fontSize: 11, fill: "#8b949e", fontFamily: "var(--font-geist-mono)" }} />
          <YAxis tick={{ fontSize: 11, fill: "#8b949e", fontFamily: "var(--font-geist-mono)" }} unit="%" width={48} />
          <Tooltip
            cursor={{ fill: "rgba(88,166,255,0.06)" }}
            contentStyle={{ background: "#1c2128", border: "1px solid #30363d", borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: "#8b949e" }}
            formatter={(v) => [`${v}%`, "Lợi nhuận DĐ"]}
          />
          <Bar dataKey="profit" radius={[3, 3, 0, 0]}>
            {data.map((d) => (
              <Cell key={d.ticker} fill={d.profit >= 0 ? "#3fb950" : "#f85149"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
