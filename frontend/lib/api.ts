export type KlineItem = {
  symbol: string;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number | null;
};

export type SearchResult = {
  symbol: string;
  score: number;
  start_date: string;
  end_date: string;
};

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function fetchSymbols(): Promise<string[]> {
  const resp = await fetch(`${apiBase}/symbols`, { cache: "no-store" });
  if (!resp.ok) {
    throw new Error("无法加载股票池");
  }
  const data = (await resp.json()) as { symbols: string[] };
  return data.symbols;
}

export async function fetchKline(params: {
  symbol: string;
  interval: "1d" | "1w";
  start: string;
  end: string;
}): Promise<KlineItem[]> {
  const query = new URLSearchParams(params);
  const resp = await fetch(`${apiBase}/kline?${query.toString()}`, { cache: "no-store" });
  if (!resp.ok) {
    throw new Error("K线查询失败");
  }
  const data = (await resp.json()) as { items: KlineItem[] };
  return data.items;
}

export async function fetchSearch(params: {
  symbol: string;
  interval: "1d" | "1w";
  start: string;
  end: string;
  top_n: number;
}): Promise<SearchResult[]> {
  const resp = await fetch(`${apiBase}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!resp.ok) {
    throw new Error("相似检索失败");
  }
  const data = (await resp.json()) as { results: SearchResult[] };
  return data.results;
}
