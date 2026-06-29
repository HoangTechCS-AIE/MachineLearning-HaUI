"use client";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  LineChart,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { IndicatorPoint } from "@/lib/api";

const AXIS = { stroke: "#8b949e", fontSize: 11, fontFamily: "var(--font-geist-mono)" };
const GRID = "rgba(48,54,61,0.4)";

function tooltipStyle() {
  return {
    contentStyle: {
      background: "#1c2128",
      border: "1px solid #30363d",
      borderRadius: 8,
      fontSize: 12,
    },
    labelStyle: { color: "#8b949e" },
    itemStyle: { color: "#e6edf3" },
  };
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-1.5 text-xs font-medium text-muted">{title}</div>
      <div className="h-[150px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          {children as React.ReactElement}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function IndicatorCharts({ points }: { points: IndicatorPoint[] }) {
  const tt = tooltipStyle();
  return (
    <div className="grid gap-5">
      {/* RSI 14 */}
      <Panel title="RSI (14) — vùng quá mua > 70, quá bán < 30">
        <LineChart data={points} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid stroke={GRID} vertical={false} />
          <XAxis dataKey="date" tick={AXIS} minTickGap={48} />
          <YAxis domain={[0, 100]} ticks={[0, 30, 70, 100]} tick={AXIS} width={40} />
          <ReferenceArea y1={30} y2={70} fill="#58a6ff" fillOpacity={0.05} />
          <ReferenceLine y={70} stroke="#f85149" strokeDasharray="3 3" strokeOpacity={0.5} />
          <ReferenceLine y={30} stroke="#3fb950" strokeDasharray="3 3" strokeOpacity={0.5} />
          <Tooltip {...tt} />
          <Line type="monotone" dataKey="rsi14" name="RSI" stroke="#58a6ff" dot={false} strokeWidth={1.6} connectNulls />
        </LineChart>
      </Panel>

      {/* MACD */}
      <Panel title="MACD (12, 26, 9)">
        <ComposedChart data={points} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid stroke={GRID} vertical={false} />
          <XAxis dataKey="date" tick={AXIS} minTickGap={48} />
          <YAxis tick={AXIS} width={40} />
          <ReferenceLine y={0} stroke="#30363d" />
          <Tooltip {...tt} />
          <Bar dataKey="macd_diff" name="Histogram" fill="#8b949e" fillOpacity={0.45} />
          <Line type="monotone" dataKey="macd" name="MACD" stroke="#58a6ff" dot={false} strokeWidth={1.6} connectNulls />
          <Line type="monotone" dataKey="macd_signal" name="Signal" stroke="#f0a35e" dot={false} strokeWidth={1.6} connectNulls />
        </ComposedChart>
      </Panel>

      {/* Stochastic */}
      <Panel title="Stochastic (%K, %D)">
        <LineChart data={points} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid stroke={GRID} vertical={false} />
          <XAxis dataKey="date" tick={AXIS} minTickGap={48} />
          <YAxis domain={[0, 100]} ticks={[0, 20, 80, 100]} tick={AXIS} width={40} />
          <ReferenceLine y={80} stroke="#f85149" strokeDasharray="3 3" strokeOpacity={0.5} />
          <ReferenceLine y={20} stroke="#3fb950" strokeDasharray="3 3" strokeOpacity={0.5} />
          <Tooltip {...tt} />
          <Line type="monotone" dataKey="stoch_k" name="%K" stroke="#58a6ff" dot={false} strokeWidth={1.6} connectNulls />
          <Line type="monotone" dataKey="stoch_d" name="%D" stroke="#f0a35e" dot={false} strokeWidth={1.6} connectNulls />
        </LineChart>
      </Panel>
    </div>
  );
}
