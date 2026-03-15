"use client";

import { useEffect, useMemo, useState } from "react";
import { Line, LineChart, Tooltip, XAxis, YAxis } from "recharts";
import { fetchKline, fetchSearch, fetchSymbols, KlineItem, SearchResult } from "../lib/api";

function toNormSeries(items: KlineItem[]) {
  if (!items.length) return [];
  const base = items[0].close || 1;
  return items.map((it, idx) => ({
    idx,
    date: it.date,
    close: it.close,
    norm: it.close / base,
  }));
}

export default function HomePage() {
  const [symbols, setSymbols] = useState<string[]>([]);
  const [symbol, setSymbol] = useState("AAPL");
  const [interval, setInterval] = useState<"1d" | "1w">("1d");
  const [start, setStart] = useState("2024-01-01");
  const [end, setEnd] = useState("2024-12-31");
  const [kline, setKline] = useState<KlineItem[]>([]);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchSymbols()
      .then((list) => {
        setSymbols(list);
        if (list.length > 0) {
          setSymbol(list[0]);
        }
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  const norm = useMemo(() => toNormSeries(kline), [kline]);
  const chartWidth = useMemo(() => Math.max(720, norm.length * 4), [norm.length]);

  async function handleLoadKline() {
    setLoading(true);
    setError("");
    try {
      const data = await fetchKline({ symbol, interval, start, end });
      setKline(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch() {
    setLoading(true);
    setError("");
    try {
      const data = await fetchSearch({ symbol, interval, start, end, top_n: 10 });
      setResults(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="container">
      <h1>Kline Retriever 前端</h1>
      <p>先加载目标股票 K 线，再按比例变化检索最相似 Top10。</p>

      <section className="card">
        <div className="row">
          <div>
            <label>股票代码</label>
            <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
              {symbols.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>周期</label>
            <select value={interval} onChange={(e) => setInterval(e.target.value as "1d" | "1w")}>
              <option value="1d">日K</option>
              <option value="1w">周K</option>
            </select>
          </div>
          <div>
            <label>开始日期</label>
            <input value={start} type="date" onChange={(e) => setStart(e.target.value)} />
          </div>
          <div>
            <label>结束日期</label>
            <input value={end} type="date" onChange={(e) => setEnd(e.target.value)} />
          </div>
        </div>
        <div style={{ display: "flex", gap: 12, marginTop: 12 }}>
          <button onClick={handleLoadKline} disabled={loading}>
            {loading ? "处理中..." : "查看目标K线"}
          </button>
          <button className="secondary" onClick={handleSearch} disabled={loading}>
            {loading ? "处理中..." : "检索相似 Top10"}
          </button>
        </div>
        {error && <p style={{ color: "#dc2626" }}>{error}</p>}
      </section>

      <section className="card">
        <h3>目标股票归一化走势</h3>
        {norm.length === 0 ? (
          <p>暂无数据，请先点击“查看目标K线”。</p>
        ) : (
          <div style={{ width: "100%", overflowX: "auto" }}>
            <LineChart width={chartWidth} height={320} data={norm}>
              <XAxis dataKey="idx" minTickGap={24} />
              <YAxis domain={["auto", "auto"]} />
              <Tooltip />
              <Line type="monotone" dataKey="norm" stroke="#2563eb" dot={false} />
            </LineChart>
          </div>
        )}
      </section>

      <section className="card">
        <h3>检索结果 Top10</h3>
        {results.length === 0 ? (
          <p>暂无结果，请先点击“检索相似 Top10”。</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>排名</th>
                <th>代码</th>
                <th>相似度</th>
                <th>窗口</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, idx) => (
                <tr key={`${r.symbol}-${idx}`}>
                  <td>{idx + 1}</td>
                  <td>{r.symbol}</td>
                  <td>{r.score.toFixed(6)}</td>
                  <td>
                    {r.start_date} ~ {r.end_date}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </main>
  );
}
