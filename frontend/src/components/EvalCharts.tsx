"use client";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ForecastPoint } from "@/lib/api";

const AXIS = { fontSize: 11, fill: "#8b949e", fontFamily: "var(--font-geist-mono)" };
const GRID = "rgba(48,54,61,0.4)";
const TT = {
  contentStyle: { background: "#1c2128", border: "1px solid #30363d", borderRadius: 8, fontSize: 12 },
  labelStyle: { color: "#8b949e" },
};

export function ActualVsForecast({ data }: { data: ForecastPoint[] }) {
  return (
    <div className="h-[320px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
          <CartesianGrid stroke={GRID} vertical={false} />
          <XAxis dataKey="date" tick={AXIS} minTickGap={56} />
          <YAxis tick={AXIS} width={56} domain={["auto", "auto"]} />
          <Tooltip {...TT} />
          <Line type="monotone" dataKey="actual" name="Thực tế" stroke="#f85149" dot={false} strokeWidth={1.8} connectNulls />
          <Line type="monotone" dataKey="pred" name="Dự báo" stroke="#58a6ff" dot={false} strokeWidth={1.8} connectNulls />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function LossCurve({ train, val }: { train: number[]; val: number[] }) {
  const data = train.map((t, i) => ({ epoch: i + 1, train: t, val: val[i] ?? null }));
  return (
    <div className="h-[260px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
          <CartesianGrid stroke={GRID} vertical={false} />
          <XAxis dataKey="epoch" tick={AXIS} />
          <YAxis tick={AXIS} width={56} />
          <Tooltip {...TT} />
          <Line type="monotone" dataKey="train" name="Train L1" stroke="#58a6ff" dot={false} strokeWidth={1.8} />
          <Line type="monotone" dataKey="val" name="Val L1" stroke="#f0a35e" dot={false} strokeWidth={1.8} connectNulls />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
