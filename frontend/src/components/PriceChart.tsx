"use client";
import { useEffect, useRef } from "react";
import {
  ColorType,
  createChart,
  LineStyle,
  type IChartApi,
  type Time,
} from "lightweight-charts";
import type { PricePoint } from "@/lib/api";

/** Cộng 1 ngày làm việc (bỏ qua T7/CN) cho điểm dự báo. */
function nextBusinessDay(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + 1);
  const dow = d.getUTCDay();
  if (dow === 6) d.setUTCDate(d.getUTCDate() + 2);
  else if (dow === 0) d.setUTCDate(d.getUTCDate() + 1);
  return d.toISOString().slice(0, 10);
}

export function PriceChart({
  history,
  lastDate,
  lastClose,
  predClose,
  direction,
  height = 360,
}: {
  history: PricePoint[];
  lastDate: string;
  lastClose: number;
  predClose: number;
  direction: "up" | "down" | "flat";
  height?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const fcColor = direction === "down" ? "#f85149" : direction === "up" ? "#3fb950" : "#8b949e";

    const chart: IChartApi = createChart(el, {
      width: el.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#8b949e",
        fontFamily: "var(--font-geist-mono), monospace",
      },
      grid: {
        vertLines: { color: "rgba(48,54,61,0.4)" },
        horzLines: { color: "rgba(48,54,61,0.4)" },
      },
      rightPriceScale: { borderColor: "#30363d" },
      timeScale: { borderColor: "#30363d", fixLeftEdge: true, fixRightEdge: true },
      crosshair: { mode: 0 },
    });

    const area = chart.addAreaSeries({
      lineColor: "#58a6ff",
      topColor: "rgba(88,166,255,0.28)",
      bottomColor: "rgba(88,166,255,0.02)",
      lineWidth: 2,
      priceLineVisible: false,
    });
    area.setData(
      history
        .filter((p) => p.close !== null)
        .map((p) => ({ time: p.date as Time, value: p.close as number }))
    );

    // Nhánh dự báo: nối close cuối -> giá dự báo phiên kế (nét đứt, màu theo hướng)
    const nextDate = nextBusinessDay(lastDate);
    const fc = chart.addLineSeries({
      color: fcColor,
      lineWidth: 2,
      lineStyle: LineStyle.Dashed,
      priceLineVisible: false,
      lastValueVisible: true,
    });
    fc.setData([
      { time: lastDate as Time, value: lastClose },
      { time: nextDate as Time, value: predClose },
    ]);
    fc.setMarkers([
      {
        time: nextDate as Time,
        position: direction === "down" ? "belowBar" : "aboveBar",
        color: fcColor,
        shape: direction === "down" ? "arrowDown" : "arrowUp",
        text: "Dự báo",
      },
    ]);

    chart.timeScale().fitContent();

    const ro = new ResizeObserver(() => chart.applyOptions({ width: el.clientWidth }));
    ro.observe(el);
    return () => {
      ro.disconnect();
      chart.remove();
    };
  }, [history, lastDate, lastClose, predClose, direction, height]);

  return <div ref={ref} className="w-full" style={{ height }} />;
}
