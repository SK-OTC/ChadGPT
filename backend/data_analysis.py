"""
Data analysis module for ChadGPT.
Uses Kaggle-style CSV datasets + scikit-learn to produce chart-ready JSON
for each query topic.

Chart types returned:
  line   — time series trend with optional linear/polynomial regression overlay
  bar    — categorical comparison
  scatter — correlation between two indicators
"""

import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.metrics import r2_score
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

_DATA_DIR = os.path.join(os.path.dirname(__file__), "datasets")
_df: pd.DataFrame | None = None


def _load() -> pd.DataFrame:
    global _df
    if _df is None:
        path = os.path.join(_DATA_DIR, "chad_indicators.csv")
        _df = pd.read_csv(path)
    return _df


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _linear_trend(x: np.ndarray, y: np.ndarray) -> tuple[list[float], float]:
    """Fit a linear regression and return predicted values + R²."""
    lr = LinearRegression()
    X = x.reshape(-1, 1)
    lr.fit(X, y)
    y_pred = lr.predict(X)
    r2 = float(r2_score(y, y_pred))
    return y_pred.tolist(), round(r2, 3)


def _poly_trend(x: np.ndarray, y: np.ndarray, degree: int = 2) -> tuple[list[float], float]:
    """Fit a polynomial regression and return predicted values + R²."""
    poly = PolynomialFeatures(degree=degree, include_bias=False)
    X_poly = poly.fit_transform(x.reshape(-1, 1))
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_poly)
    lr = LinearRegression()
    lr.fit(X_scaled, y)
    y_pred = lr.predict(X_scaled)
    r2 = float(r2_score(y, y_pred))
    return y_pred.tolist(), round(r2, 3)


def _series(df: pd.DataFrame, col: str, start: int = 1990) -> tuple[list[int], list[float]]:
    sub = df[df["year"] >= start][["year", col]].dropna()
    return sub["year"].tolist(), sub[col].round(2).tolist()


def _fmt_num(v: float) -> str:
    if abs(v) >= 1e9:
        return f"{v / 1e9:.1f}B"
    if abs(v) >= 1e6:
        return f"{v / 1e6:.1f}M"
    if abs(v) >= 1e3:
        return f"{v / 1e3:.1f}K"
    return f"{v:.1f}"


# ---------------------------------------------------------------------------
# Per-topic chart builders
# ---------------------------------------------------------------------------

def population_charts(df: pd.DataFrame) -> list[dict]:
    charts = []

    # 1. Population growth — line + linear regression
    years, pop = _series(df, "population_millions")
    x = np.array(years, dtype=float)
    trend, r2 = _linear_trend(x, np.array(pop))
    charts.append({
        "type": "line",
        "title": "Population Growth (1990–2024)",
        "subtitle": f"Linear trend R² = {r2}",
        "x_label": "Year",
        "y_label": "Population (millions)",
        "series": [
            {"label": "Population", "data": pop, "color": "#3B82F6"},
            {"label": "Linear Trend", "data": [round(v, 2) for v in trend], "color": "#FBBF24", "dashed": True},
        ],
        "labels": years,
        "insight": f"Population grew from {pop[0]}M in 1990 to {pop[-1]}M in 2024 — a {round((pop[-1]/pop[0]-1)*100, 1)}% increase.",
    })

    # 2. Infant mortality decline — bar chart
    years_b, infant = _series(df, "infant_mortality_per1000", start=2000)
    charts.append({
        "type": "bar",
        "title": "Infant Mortality Rate per 1,000 Births",
        "subtitle": "Declining but still high by global standards",
        "x_label": "Year",
        "y_label": "Deaths per 1,000 live births",
        "series": [{"label": "Infant Mortality", "data": infant, "color": "#EF4444"}],
        "labels": years_b,
        "insight": f"Infant mortality fell from {infant[0]} in 2000 to {infant[-1]} in 2024 — a {round((1 - infant[-1]/infant[0])*100, 1)}% reduction.",
    })

    # 3. KMeans clustering: population vs life expectancy (3 eras)
    sub = df[["year", "population_millions", "life_expectancy"]].dropna()
    features = sub[["population_millions", "life_expectancy"]].values
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    km = KMeans(n_clusters=3, random_state=42, n_init=10)
    labels_km = km.fit_predict(features_scaled)
    cluster_colors = ["#3B82F6", "#FBBF24", "#EF4444"]
    points = [
        {"x": float(row["population_millions"]), "y": float(row["life_expectancy"]),
         "year": int(row["year"]), "cluster": int(labels_km[i])}
        for i, (_, row) in enumerate(sub.iterrows())
    ]
    charts.append({
        "type": "scatter",
        "title": "Population vs Life Expectancy (K-Means, 3 clusters)",
        "subtitle": "Clustered by development era",
        "x_label": "Population (millions)",
        "y_label": "Life Expectancy (years)",
        "points": points,
        "cluster_colors": cluster_colors,
        "insight": "K-Means identifies three development eras: pre-oil (low pop/low LE), oil boom (rapid growth), and post-2015 (austerity).",
    })

    return charts


def economy_charts(df: pd.DataFrame) -> list[dict]:
    charts = []

    # 1. GDP over time — polynomial regression (oil shock curve)
    years, gdp = _series(df, "gdp_usd_billions")
    x = np.array(years, dtype=float)
    trend, r2 = _poly_trend(x, np.array(gdp), degree=3)
    charts.append({
        "type": "line",
        "title": "GDP Over Time (USD Billions)",
        "subtitle": f"Polynomial degree-3 trend R² = {r2}",
        "x_label": "Year",
        "y_label": "GDP (USD Billions)",
        "series": [
            {"label": "GDP", "data": gdp, "color": "#10B981"},
            {"label": "Poly Trend", "data": [round(v, 2) for v in trend], "color": "#F59E0B", "dashed": True},
        ],
        "labels": years,
        "insight": f"GDP peaked at ~${max(gdp):.1f}B ({years[int(np.argmax(gdp))]}), driven by oil revenues discovered in 2003.",
    })

    # 2. Oil revenue vs agriculture share — stacked-style bar comparison
    years_b, oil = _series(df, "oil_revenue_pct_gdp", start=2003)
    _, agri = _series(df, "agriculture_pct_gdp", start=2003)
    charts.append({
        "type": "bar",
        "title": "Oil Revenue vs Agriculture Share of GDP",
        "subtitle": "Structural shift since oil discovery (2003)",
        "x_label": "Year",
        "y_label": "% of GDP",
        "series": [
            {"label": "Oil Revenue %", "data": oil, "color": "#F59E0B"},
            {"label": "Agriculture %", "data": agri, "color": "#10B981"},
        ],
        "labels": years_b,
        "insight": "Oil revenues peaked at 42% of GDP in 2008; agriculture declined from 40% in 1990 to 23% by 2024.",
    })

    # 3. GDP per capita scatter vs poverty rate
    sub = df[["year", "gdp_per_capita_usd", "poverty_rate_pct"]].dropna()
    points = [
        {"x": float(r["gdp_per_capita_usd"]), "y": float(r["poverty_rate_pct"]), "year": int(r["year"]), "cluster": 0}
        for _, r in sub.iterrows()
    ]
    charts.append({
        "type": "scatter",
        "title": "GDP Per Capita vs Poverty Rate",
        "subtitle": "Each point is one year (1990–2024)",
        "x_label": "GDP per capita (USD)",
        "y_label": "Poverty rate (%)",
        "points": points,
        "cluster_colors": ["#6366F1"],
        "insight": "A clear negative correlation: higher GDP per capita correlates with lower poverty — but even at peak GDP (~$876), poverty remained above 58%.",
    })

    return charts


def geography_charts(df: pd.DataFrame) -> list[dict]:
    charts = []

    # 1. Lake Chad area shrinkage — polynomial regression
    years, lake = _series(df, "lake_chad_area_km2")
    x = np.array(years, dtype=float)
    trend, r2 = _poly_trend(x, np.array(lake), degree=2)
    charts.append({
        "type": "line",
        "title": "Lake Chad Surface Area (km²)",
        "subtitle": f"Polynomial shrinkage trend R² = {r2}",
        "x_label": "Year",
        "y_label": "Surface Area (km²)",
        "series": [
            {"label": "Lake Area", "data": lake, "color": "#06B6D4"},
            {"label": "Trend", "data": [round(v, 0) for v in trend], "color": "#EF4444", "dashed": True},
        ],
        "labels": years,
        "insight": f"Lake Chad has shrunk from {lake[0]:,} km² (1990) to {lake[-1]:,} km² (2024) — a {round((1-lake[-1]/lake[0])*100, 1)}% loss.",
    })

    # 2. Forest area decline — bar
    years_b, forest = _series(df, "forest_area_pct")
    charts.append({
        "type": "bar",
        "title": "Forest Area (% of Land)",
        "subtitle": "Ongoing deforestation trend",
        "x_label": "Year",
        "y_label": "Forest cover (%)",
        "series": [{"label": "Forest %", "data": forest, "color": "#16A34A"}],
        "labels": years_b,
        "insight": f"Forest cover fell from {forest[0]}% (1990) to {forest[-1]}% (2024), driven by land conversion and fuelwood demand.",
    })

    # 3. CO2 scatter vs GDP
    sub = df[["year", "gdp_usd_billions", "co2_emissions_kt"]].dropna()
    points = [
        {"x": float(r["gdp_usd_billions"]), "y": float(r["co2_emissions_kt"]), "year": int(r["year"]), "cluster": 0}
        for _, r in sub.iterrows()
    ]
    charts.append({
        "type": "scatter",
        "title": "CO₂ Emissions vs GDP",
        "subtitle": "Economic growth and emissions footprint",
        "x_label": "GDP (USD Billions)",
        "y_label": "CO₂ Emissions (kt)",
        "points": points,
        "cluster_colors": ["#F97316"],
        "insight": "CO₂ emissions rose sharply after oil extraction began in 2003, closely tracking GDP — suggesting fossil-fuel dependency.",
    })

    return charts


def challenges_charts(df: pd.DataFrame) -> list[dict]:
    charts = []

    # 1. Poverty rate with linear trend
    years, poverty = _series(df, "poverty_rate_pct")
    x = np.array(years, dtype=float)
    trend, r2 = _linear_trend(x, np.array(poverty))
    charts.append({
        "type": "line",
        "title": "Poverty Rate Over Time (%)",
        "subtitle": f"Linear trend R² = {r2}",
        "x_label": "Year",
        "y_label": "Poverty Rate (%)",
        "series": [
            {"label": "Poverty Rate", "data": poverty, "color": "#EF4444"},
            {"label": "Trend", "data": [round(v, 2) for v in trend], "color": "#6B7280", "dashed": True},
        ],
        "labels": years,
        "insight": f"Poverty peaked at {max(poverty)}% (1992) and has slowly declined to {poverty[-1]}% by 2024, with setbacks during oil price crashes.",
    })

    # 2. Human development indicators — multi-series bar
    years_b, life = _series(df, "life_expectancy", start=2000)
    _, literacy = _series(df, "literacy_rate_pct", start=2000)
    charts.append({
        "type": "bar",
        "title": "Life Expectancy vs Literacy Rate",
        "subtitle": "Two key human development indicators",
        "x_label": "Year",
        "y_label": "Value",
        "series": [
            {"label": "Life Expectancy (yrs)", "data": life, "color": "#8B5CF6"},
            {"label": "Literacy Rate (%)", "data": literacy, "color": "#F59E0B"},
        ],
        "labels": years_b,
        "insight": f"Life expectancy rose from {life[0]} to {life[-1]} years (2000–2024); literacy improved from {literacy[0]}% to {literacy[-1]}%.",
    })

    # 3. PCA on development indicators — 2D projection
    cols = ["gdp_per_capita_usd", "life_expectancy", "infant_mortality_per1000",
            "literacy_rate_pct", "poverty_rate_pct", "access_to_electricity_pct"]
    sub = df[["year"] + cols].dropna()
    scaler = StandardScaler()
    scaled = scaler.fit_transform(sub[cols])
    pca = PCA(n_components=2)
    components = pca.fit_transform(scaled)
    variance = pca.explained_variance_ratio_
    km = KMeans(n_clusters=3, random_state=42, n_init=10)
    clusters = km.fit_predict(scaled)
    points = [
        {"x": round(float(components[i, 0]), 3), "y": round(float(components[i, 1]), 3),
         "year": int(sub.iloc[i]["year"]), "cluster": int(clusters[i])}
        for i in range(len(sub))
    ]
    charts.append({
        "type": "scatter",
        "title": "PCA: Development Indicators (6 variables → 2D)",
        "subtitle": f"PC1 {variance[0]*100:.1f}% variance · PC2 {variance[1]*100:.1f}% variance",
        "x_label": "PC1 (Development axis)",
        "y_label": "PC2 (Health-Education axis)",
        "points": points,
        "cluster_colors": ["#3B82F6", "#FBBF24", "#EF4444"],
        "insight": f"PCA reduces 6 indicators to 2 components capturing {(variance[0]+variance[1])*100:.1f}% of variance. Clusters reflect pre-oil, oil-boom, and recent eras.",
    })

    return charts


def general_charts(df: pd.DataFrame) -> list[dict]:
    charts = []

    # 1. Mobile subscriptions — tech growth line
    years, mobile = _series(df, "mobile_subscriptions_per100", start=2000)
    x = np.array(years, dtype=float)
    trend, r2 = _poly_trend(x, np.array(mobile), degree=2)
    charts.append({
        "type": "line",
        "title": "Mobile Subscriptions per 100 People",
        "subtitle": f"Rapid digital adoption (R² = {r2})",
        "x_label": "Year",
        "y_label": "Subscriptions per 100",
        "series": [
            {"label": "Mobile Subscriptions", "data": mobile, "color": "#6366F1"},
            {"label": "Trend", "data": [round(v, 2) for v in trend], "color": "#FBBF24", "dashed": True},
        ],
        "labels": years,
        "insight": f"Mobile subscriptions grew from {mobile[0]} per 100 (2000) to {mobile[-1]} (2024) — one of Africa's faster adoption curves.",
    })

    # 2. Electricity access — bar
    years_b, elec = _series(df, "access_to_electricity_pct", start=2000)
    charts.append({
        "type": "bar",
        "title": "Access to Electricity (% of Population)",
        "subtitle": "Slow but accelerating progress",
        "x_label": "Year",
        "y_label": "Population with electricity (%)",
        "series": [{"label": "Electricity Access %", "data": elec, "color": "#FBBF24"}],
        "labels": years_b,
        "insight": f"Only {elec[-1]}% of Chad's population has electricity (2024), though this has grown from {elec[0]}% in 2000.",
    })

    # 3. Multi-indicator scatter: GDP per capita vs life expectancy
    sub = df[["year", "gdp_per_capita_usd", "life_expectancy"]].dropna()
    points = [
        {"x": float(r["gdp_per_capita_usd"]), "y": float(r["life_expectancy"]), "year": int(r["year"]), "cluster": 0}
        for _, r in sub.iterrows()
    ]
    charts.append({
        "type": "scatter",
        "title": "GDP Per Capita vs Life Expectancy (1990–2024)",
        "subtitle": "Wealth-health relationship over time",
        "x_label": "GDP per capita (USD)",
        "y_label": "Life Expectancy (years)",
        "points": points,
        "cluster_colors": ["#10B981"],
        "insight": "Life expectancy rises steadily with GDP, but the relationship plateaus above $700/capita — suggesting non-economic constraints on health.",
    })

    return charts


# ---------------------------------------------------------------------------
# Topic router
# ---------------------------------------------------------------------------

_TOPIC_MAP = {
    "population": population_charts,
    "economy": economy_charts,
    "geography": geography_charts,
    "challenges": challenges_charts,
    "history": economy_charts,      # reuse economy (GDP timeline)
    "tourism": geography_charts,    # reuse geography (environment)
    "culture": general_charts,
    "general": general_charts,
}


def get_charts_for_topic(topic: str) -> dict:
    """
    Return chart data for a given topic string.
    Returns {"charts": [...], "topic": topic, "source": "Kaggle/World Bank"}
    """
    df = _load()
    fn = _TOPIC_MAP.get(topic, general_charts)
    charts = fn(df)
    return {
        "charts": charts,
        "topic": topic,
        "source": "World Bank Development Indicators (via Kaggle)",
        "dataset": "chad_indicators.csv",
        "rows": len(df),
    }
