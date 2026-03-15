"use client";

import { useEffect, useRef } from "react";
import { CandlestickSeries, createChart, type IChartApi, type Time } from "lightweight-charts";
import type { KlineItem } from "../lib/api";

type Props = {
  items: KlineItem[];
  height?: number;
};

export default function CandlestickChart({ items, height = 360 }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      width: container.clientWidth || 720,
      height,
      layout: {
        background: { color: "#ffffff" },
        textColor: "#1f2937",
      },
      grid: {
        vertLines: { color: "#eef2ff" },
        horzLines: { color: "#eef2ff" },
      },
      rightPriceScale: {
        borderColor: "#d1d5db",
      },
      timeScale: {
        borderColor: "#d1d5db",
      },
    });

    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#16a34a",
      downColor: "#dc2626",
      borderUpColor: "#16a34a",
      borderDownColor: "#dc2626",
      wickUpColor: "#16a34a",
      wickDownColor: "#dc2626",
    });

    series.setData(
      items.map((it) => ({
        time: it.date as Time,
        open: Number(it.open),
        high: Number(it.high),
        low: Number(it.low),
        close: Number(it.close),
      }))
    );

    chart.timeScale().fitContent();

    const resizeObserver = new ResizeObserver(() => {
      chart.applyOptions({ width: container.clientWidth || 720 });
    });
    resizeObserver.observe(container);

    chartRef.current = chart;

    return () => {
      resizeObserver.disconnect();
      chartRef.current?.remove();
      chartRef.current = null;
    };
  }, [items, height]);

  return <div ref={containerRef} style={{ width: "100%", height }} />;
}
