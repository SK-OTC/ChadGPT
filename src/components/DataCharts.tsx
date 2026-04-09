// View sub-component — renders scikit-learn analysis results as SVG charts.
// Supports line (with optional dashed trend), grouped bar, and scatter chart types.

import { useEffect, useRef } from "react";
import type { ChartData, ChartSeries, ScatterPoint, DonutSlice } from "../model/chad-data";

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
      {series.map((s, i) => (
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
// Donut chart
// ---------------------------------------------------------------------------

const DONUT_R = 72;
const DONUT_R_INNER = 42;
const DONUT_CX = 110;
const DONUT_CY = 110;
const DONUT_SVG = 220;

function polarToCart(cx: number, cy: number, r: number, deg: number) {
  const rad = ((deg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function DonutChart({ chart }: { chart: ChartData }) {
  const slices = chart.slices ?? [];
  if (!slices.length) return null;

  const total = slices.reduce((s, d) => s + d.value, 0);
  let cumAngle = 0;

  const arcs = slices.map((sl) => {
    const angle = (sl.value / total) * 360;
    const start = cumAngle;
    cumAngle += angle;
    const end = cumAngle;
    const large = angle > 180 ? 1 : 0;
    const s1 = polarToCart(DONUT_CX, DONUT_CY, DONUT_R, start);
    const s2 = polarToCart(DONUT_CX, DONUT_CY, DONUT_R, end);
    const s3 = polarToCart(DONUT_CX, DONUT_CY, DONUT_R_INNER, end);
    const s4 = polarToCart(DONUT_CX, DONUT_CY, DONUT_R_INNER, start);
    const d = [
      `M${s1.x},${s1.y}`,
      `A${DONUT_R},${DONUT_R} 0 ${large} 1 ${s2.x},${s2.y}`,
      `L${s3.x},${s3.y}`,
      `A${DONUT_R_INNER},${DONUT_R_INNER} 0 ${large} 0 ${s4.x},${s4.y}`,
      "Z",
    ].join(" ");
    return { ...sl, d, pct: ((sl.value / total) * 100).toFixed(1) };
  });

  return (
    <div className="donut-chart-wrapper">
      <svg viewBox={`0 0 ${DONUT_SVG} ${DONUT_SVG}`} style={{ width: 220, height: 220, display: "block" }} aria-label={chart.title}>
        {arcs.map((a, i) => (
          <path key={i} d={a.d} fill={a.color} stroke="#fff" strokeWidth="1.5">
            <title>{`${a.label}: ${a.pct}%`}</title>
          </path>
        ))}
        <text x={DONUT_CX} y={DONUT_CY - 4} textAnchor="middle" fontSize="12" fontWeight="600" fill="#334155">
          {total.toFixed(0)}%
        </text>
        <text x={DONUT_CX} y={DONUT_CY + 10} textAnchor="middle" fontSize="9" fill="#64748b">
          Total
        </text>
      </svg>
      <div className="donut-legend">
        {arcs.map((a, i) => (
          <div key={i} className="donut-legend-item">
            <span className="donut-legend-swatch" style={{ background: a.color }} />
            <span className="donut-legend-label">{a.label}</span>
            <span className="donut-legend-pct">{a.pct}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Horizontal bar chart
// ---------------------------------------------------------------------------

const HBAR_H_PER_ROW = 28;
const HBAR_ML = 120;
const HBAR_MR = 40;
const HBAR_W = 620;

function HorizontalBarChart({ chart }: { chart: ChartData }) {
  const categories = chart.categories ?? [];
  const values = chart.values ?? [];
  const colors = chart.colors ?? [];
  if (!categories.length) return null;

  const maxVal = Math.max(...values);
  const barAreaW = HBAR_W - HBAR_ML - HBAR_MR;
  const svgH = categories.length * HBAR_H_PER_ROW + 20;

  return (
    <svg viewBox={`0 0 ${HBAR_W} ${svgH}`} style={{ width: "100%", height: "auto", display: "block" }} aria-label={chart.title}>
      {categories.map((cat, i) => {
        const val = values[i] ?? 0;
        const barW = (val / maxVal) * barAreaW;
        const y = i * HBAR_H_PER_ROW + 10;
        const isHighlight = chart.highlight && cat === chart.highlight;
        return (
          <g key={i}>
            <text x={HBAR_ML - 8} y={y + 14} textAnchor="end" fontSize="11" fill={isHighlight ? "#e11d48" : "#475569"} fontWeight={isHighlight ? "700" : "400"}>
              {cat}
            </text>
            <rect x={HBAR_ML} y={y + 2} width={Math.max(barW, 2)} height={18} fill={colors[i] || "#6366F1"} rx="3" opacity={isHighlight ? 1 : 0.85}>
              <title>{`${cat}: ${val}`}</title>
            </rect>
            <text x={HBAR_ML + barW + 5} y={y + 15} fontSize="10" fill="#64748b" fontWeight="500">
              {fmtNum(val)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Public component
// ---------------------------------------------------------------------------

interface DataChartsProps {
  charts: ChartData[];
  source?: string;
  isLoading?: boolean;
  highlight?: boolean;
}

export function DataCharts({ charts, source, isLoading = false, highlight = false }: DataChartsProps) {
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!highlight) return;
    sectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    sectionRef.current?.classList.add("charts-highlight-pulse");
    const t = setTimeout(() => sectionRef.current?.classList.remove("charts-highlight-pulse"), 2000);
    return () => clearTimeout(t);
  }, [highlight]);
  if (isLoading) {
    return (
      <section ref={sectionRef} className="analysis-section">
        <div className="analysis-header">
          <span className="analysis-label">Data Analysis</span>
          <span className="analysis-source">Fetching visualizations…</span>
        </div>
        <div className="analysis-charts-grid">
          {[0, 1, 2, 3].map((i) => (
            <div className="analysis-chart-card chart-skeleton" key={i}>
              <div className="skeleton-title" />
              <div className="skeleton-subtitle" />
              <div className="skeleton-chart-area" />
              <div className="skeleton-insight" />
            </div>
          ))}
        </div>
      </section>
    );
  }

  if (!charts?.length) return null;

  return (
    <section ref={sectionRef} className="analysis-section">
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
              {chart.type === "donut" && <DonutChart chart={chart} />}
              {chart.type === "hbar" && <HorizontalBarChart chart={chart} />}
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
