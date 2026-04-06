// View — bar chart visualization for topic statistics.

import type { Bar } from "../model/chad-data";

interface BarChartProps {
  bars: Bar[];
  title?: string;
}

export function BarChart({ bars, title }: BarChartProps) {
  return (
    <div className="bar-chart-container">
      {title && <h3>{title}</h3>}
      <div className="bar-chart">
        {bars.map((bar) => (
          <div className="bar-row" key={bar.label}>
            <div className="bar-row-labels">
              <span>{bar.label}</span>
              <strong>{bar.value}%</strong>
            </div>
            <div className="bar-track">
              <div className={`bar-fill ${bar.tone}`} style={{ width: `${bar.value}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
