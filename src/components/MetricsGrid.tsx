// View — grid of metric stat cards.

import type { Metric } from "../model/chad-data";

interface MetricsGridProps {
  metrics: Metric[];
}

export function MetricsGrid({ metrics }: MetricsGridProps) {
  return (
    <div className="metrics-grid">
      {metrics.map((m) => (
        <div className="metric-card" key={m.label}>
          <span>{m.label}</span>
          <strong>{m.value}</strong>
        </div>
      ))}
    </div>
  );
}
