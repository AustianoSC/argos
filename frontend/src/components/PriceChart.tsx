import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { PriceRecordResponse, ProductSourceResponse } from "../api/backend";

interface Props {
  priceHistory: PriceRecordResponse[];
  sources: ProductSourceResponse[];
}

const COLORS = [
  "#2563eb",
  "#dc2626",
  "#16a34a",
  "#ca8a04",
  "#9333ea",
  "#0891b2",
];

export default function PriceChart({ priceHistory, sources }: Props) {
  if (priceHistory.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        No price data yet. Waiting for the pipeline to complete...
      </div>
    );
  }

  // Group prices by source and build chart data
  const sourceMap = new Map(sources.map((s) => [s.id, s.domain]));
  const uniqueSources = [...new Set(priceHistory.map((p) => p.source_id))];

  // Build data points: each point has a date and a price per source
  const dataByDate = new Map<string, Record<string, number | string>>();
  for (const record of priceHistory) {
    const date = new Date(record.extracted_at).toLocaleDateString();
    if (!dataByDate.has(date)) {
      dataByDate.set(date, { date });
    }
    const entry = dataByDate.get(date)!;
    const domain = sourceMap.get(record.source_id) ?? "Unknown";
    entry[domain] = parseFloat(record.price);
  }

  const chartData = Array.from(dataByDate.values());
  const domains = uniqueSources.map(
    (id) => sourceMap.get(id) ?? "Unknown"
  );

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" fontSize={12} />
        <YAxis
          fontSize={12}
          tickFormatter={(v: number) => `$${v}`}
        />
        <Tooltip formatter={(value) => [`$${value}`, ""]} />
        <Legend />
        {domains.map((domain, i) => (
          <Line
            key={domain}
            type="monotone"
            dataKey={domain}
            stroke={COLORS[i % COLORS.length]}
            strokeWidth={2}
            dot={{ r: 3 }}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
