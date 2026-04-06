// View sub-component — renders scikit-learn analysis results as SVG charts.
// Supports line (with optional dashed trend), grouped bar, and scatter chart types.

import type { ChartData, ChartSeries, ScatterPoint } from "../model/chad-data";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const W = 620;
const H = 220;
const ML = 52; // margin-left (y-axis labels)
const MR = 16;
const MT = 12;
const MB = 38; // margin-bottom (x-axis labels)
const PW = W - ML - MR; // plot width
const PH = H - MT - MB; // plot height

function fmtNum(v: number): string {
  const abs = Math.abs(v);
  if (abs >= 100000) return `${(v / 1000).toFixed(0)}k`;
  if (abs >= 10000) return `${(v / 1000).toFixed(0)}k`;
  if (abs >= 1000) return `${(v / 1000).toFixed(1)}k`;
  if (abs >= 100) return v.toFixed(0);
  if (abs >= 10) return v.toFixed(1);
  return v.toFixed(2);
}

function yTicks(min: number, max: number, count = 5): number[] {
  const range = max - min || 1;
  return Array.from({ length: count }, (_, i) => min + (i / (count - 1)) * range);
}

// ---------------------------------------------------------------------------
// Line chart
// ---------------------------------------------------------------------------

function LineChart({ chart }: { chart: ChartData }) {
  const series = chart.series ?? [];
  const labels = chart.labels ?? [];
  if (!series.length || !labels.length) return null;

  const allVals = series.flatMap((s) => s.data.filter(Number.isFinite));
  const minY = Math.min(...allVals);
  const maxY = Math.max(...allVals);
  const rangeY = maxY - minY || 1;

  const xOf = (i: number) => ML + (i / Math.max(labels.length - 1, 1)) * PW;
  const yOf = (v: number) => MT + PH - ((v - minY) / rangeY) * PH;

  const ticks = yTicks(minY, maxY);
  const xStep = Math.ceil(labels.length / 6);

  const toPath = (data: number[]) =>
    data
      .map((v, i) => `${i === 0 ? "M" : "L"}${xOf(i).toFixed(1)},${yOf(v).toFixed(1)}`)
      .join(" ");

  // Legend entries (non-dashed only get dots; dashed = trend)
  const legend = series;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: "auto", display: "block" }} aria-label={chart.title}>
      {/* Horizontal grid */}
      {ticks.map((v, i) => (
        <line key={i} x1={ML} y1={yOf(v)} x2={W - MR} y2={yOf(v)} stroke="#e2e8f0" strokeWidth="1" />
      ))}
      {/* Y-axis labels */}
      {ticks.map((v, i) => (
        <text key={i} x={ML - 6} y={yOf(v) + 4} textAnchor="end" fontSize="10" fill="#64748b">
          {fmtNum(v)}
        </text>
      ))}
      {/* X-axis labels */}
      {labels.map((lbl, i) => {
        if (i > 0 && i < labels.length - 1 && i % xStep !== 0) return null;
        return (
          <text key={i} x={xOf(i)} y={H - MB + 14} textAnchor="middle" fontSize="10" fill="#64748b">
            {lbl}
          </text>
        );
      })}
      {/* Axes */}
      <line x1={ML} y1={MT} x2={ML} y2={H - MB} stroke="#cbd5e1" strokeWidth="1.5" />
      <line x1={ML} y1={H - MB} x2={W - MR} y2={H - MB} stroke="#cbd5e1" strokeWidth="1.5" />
      {/* Series lines */}
      {series.map((s, si) => (
        <path
          key={si}
          d={toPath(s.data)}
          fill="none"
          stroke={s.color}
          strokeWidth={s.dashed ? 1.8 : 2.5}
          strokeDasharray={s.dashed ? "5,4" : undefined}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      ))}
      {/* Legend */}
      {legend.map((s, i) => (
        <g key={i} transform={`translate(${ML + i * 140}, ${H - 6})`}>
          <line x1="0" y1="0" x2="16" y2="0" stroke={s.color} strokeWidth={s.dashed ? 1.8 : 2.5} strokeDasharray={s.dashed ? "4,3" : undefined} />
          <text x="20" y="4" fontSize="10" fill="#64748b">{s.label}</text>
        </g>
      ))}
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Bar chart (grouped)
// ---------------------------------------------------------------------------

function BarChart({ chart }: { chart: ChartData }) {
  const series = chart.series ?? [];
  const labels = chart.labels ?? [];
  if (!series.length || !labels.length) return null;

  const allVals = series.flatMap((s) => s.data.filter(Number.isFinite));
  const minY = 0; // bars always start at 0
  const maxY = Math.max(...allVals);
  const rangeY = maxY - minY || 1;

  const ticks = yTicks(minY, maxY);
  const yOf = (v: number) => MT + PH - ((v - minY) / rangeY) * PH;

  const ns = series.length;
  const groupW = PW / labels.length;
  const gap = groupW * 0.15; // 15% gap between groups
  const barW = (groupW - gap) / ns;

  const xStep = Math.ceil(labels.length / 6);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: "auto", display: "block" }} aria-label={chart.title}>
      {/* Grid */}
      {ticks.map((v, i) => (
        <line key={i} x1={ML} y1={yOf(v)} x2={W - MR} y2={yOf(v)} stroke="#e2e8f0" strokeWidth="1" />
      ))}
      {/* Y-axis labels */}
      {ticks.map((v, i) => (
        <text key={i} x={ML - 6} y={yOf(v) + 4} textAnchor="end" fontSize="10" fill="#64748b">
          {fmtNum(v)}
        </text>
      ))}
      {/* X-axis labels */}
      {labels.map((lbl, i) => {
        if (i > 0 && i < labels.length - 1 && i % xStep !== 0) return null;
        const cx = ML + i * groupW + groupW / 2;
        return (
          <text key={i} x={cx} y={H - MB + 14} textAnchor="middle" fontSize="10" fill="#64748b">
            {lbl}
          </text>
        );
      })}
      {/* Axes */}
      <line x1={ML} y1={MT} x2={ML} y2={H - MB} stroke="#cbd5e1" strokeWidth="1.5" />
      <line x1={ML} y1={H - MB} x2={W - MR} y2={H - MB} stroke="#cbd5e1" strokeWidth="1.5" />
      {/* Bars */}
      {series.map((s, si) =>
        s.data.map((v, li) => {
          const x = ML + li * groupW + gap / 2 + si * barW;
          const barH = ((v - minY) / rangeY) * PH;
          return (
            <rect key={`${si}-${li}`} x={x} y={yOf(v)} width={Math.max(barW - 1, 1)} height={Math.max(barH, 1)} fill={s.color} opacity="0.9" rx="1">
              <title>{`${s.label} ${labels[li]}: ${v}`}</title>
            </rect>
          );
        })
      )}
      {/* Legend */}
      {series.map((s, i) => (
        <g key={i} transform={`translate(${ML + i * 140}, ${H - 6})`}>
          <rect x="0" y="-8" width="14" height="10" fill={s.color} rx="2" />
          <text x="18" y="2" fontSize="10" fill="#64748b">{s.label}</text>
        </g>
      ))}
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Scatter plot
// ---------------------------------------------------------------------------

function ScatterChart({ chart }: { chart: ChartData }) {
  const points = chart.points ?? [];
  const colors = chart.cluster_colors ?? ["#3B82F6"];
  if (!points.length) return null;

  const xs = points.map((p) => p.x);
  const ys = points.map((p) => p.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const rangeX = maxX - minX || 1;
  const rangeY = maxY - minY || 1;

  const xOf = (v: number) => ML + ((v - minX) / rangeX) * PW;
  const yOf = (v: number) => MT + PH - ((v - minY) / rangeY) * PH;

  const xTicks = yTicks(minX, maxX, 5);
  const yTickVals = yTicks(minY, maxY, 5);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: "auto", display: "block" }} aria-label={chart.title}>
      {/* Grid */}
      {yTickVals.map((v, i) => (
        <line key={i} x1={ML} y1={yOf(v)} x2={W - MR} y2={yOf(v)} stroke="#e2e8f0" strokeWidth="1" />
      ))}
      {xTicks.map((v, i) => (
        <line key={i} x1={xOf(v)} y1={MT} x2={xOf(v)} y2={H - MB} stroke="#e2e8f0" strokeWidth="1" />
      ))}
      {/* Axis labels */}
      {yTickVals.map((v, i) => (
        <text key={i} x={ML - 6} y={yOf(v) + 4} textAnchor="end" fontSize="10" fill="#64748b">
          {fmtNum(v)}
        </text>
      ))}
      {xTicks.map((v, i) => (
        <text key={i} x={xOf(v)} y={H - MB + 14} textAnchor="middle" fontSize="10" fill="#64748b">
          {fmtNum(v)}
        </text>
      ))}
      {/* Axes */}
      <line x1={ML} y1={MT} x2={ML} y2={H - MB} stroke="#cbd5e1" strokeWidth="1.5" />
      <line x1={ML} y1={H - MB} x2={W - MR} y2={H - MB} stroke="#cbd5e1" strokeWidth="1.5" />
      {/* Points */}
      {points.map((p, i) => {
        const color = colors[p.cluster % colors.length] ?? "#3B82F6";
        return (
          <circle key={i} cx={xOf(p.x)} cy={yOf(p.y)} r="4.5" fill={color} opacity="0.75" stroke="#fff" strokeWidth="0.8">
            <title>{`${p.year}: (${fmtNum(p.x)}, ${fmtNum(p.y)})`}</title>
          </circle>
        );
      })}
      {/* Cluster legend */}
      {colors.map((c, i) => (
        <g key={i} transform={`translate(${ML + i * 100}, ${H - 6})`}>
          <circle cx="6" cy="-4" r="5" fill={c} opacity="0.75" />
          <text x="14" y="0" fontSize="10" fill="#64748b">Cluster {i + 1}</text>
        </g>
      ))}
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Public component
// ---------------------------------------------------------------------------

interface DataChartsProps {
  charts: ChartData[];
  source?: string;
}

export function DataCharts({ charts, source }: DataChartsProps) {
  if (!charts?.length) return null;

  return (
    <section className="analysis-section">
      <div className="analysis-header">
        <span className="analysis-label">Data Analysis</span>
        {source && <span className="analysis-source">{source}</span>}
      </div>
      <div className="analysis-charts-grid">
        {charts.map((chart, i) => (
          <div className="analysis-chart-card" key={i}>
            <div className="analysis-chart-header">
              <h4 className="analysis-chart-title">{chart.title}</h4>
              {chart.subtitle && <p className="analysis-chart-subtitle">{chart.subtitle}</p>}
            </div>
            <div className="analysis-chart-body">
              {chart.type === "line" && <LineChart chart={chart} />}
              {chart.type === "bar" && <BarChart chart={chart} />}
              {chart.type === "scatter" && <ScatterChart chart={chart} />}
            </div>
            <div className="analysis-axis-labels">
              <span>{chart.y_label}</span>
              <span>{chart.x_label}</span>
            </div>
            <p className="analysis-insight">{chart.insight}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
