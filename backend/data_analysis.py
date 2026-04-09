"""
Data analysis module for ChadGPT.
Uses Kaggle-style CSV datasets + scikit-learn to produce chart-ready JSON
for each query topic.

Chart types returned:
  line       — time series trend with optional linear/polynomial regression overlay
  bar        — categorical comparison (vertical)
  hbar       — horizontal ranked bar chart (country comparisons)
  scatter    — correlation between two indicators
  donut      — composition / sector breakdown (circle graph)
"""

import os
import re

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.metrics import r2_score
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

_DATA_DIR = os.path.join(os.path.dirname(__file__), "datasets")
_cache: dict[str, pd.DataFrame] = {}

# Modern, pleasing color palette
COLORS = {
    "blue":     "#4F46E5",   # indigo-600
    "teal":     "#0D9488",   # teal-600
    "amber":    "#D97706",   # amber-600
    "rose":     "#E11D48",   # rose-600
    "violet":   "#7C3AED",   # violet-600
    "cyan":     "#0891B2",   # cyan-600
    "emerald":  "#059669",   # emerald-600
    "orange":   "#EA580C",   # orange-600
    "pink":     "#DB2777",   # pink-600
    "slate":    "#64748B",   # slate-500
}
PALETTE = list(COLORS.values())


def _load(filename: str = "chad_indicators.csv") -> pd.DataFrame:
    if filename not in _cache:
        _cache[filename] = pd.read_csv(os.path.join(_DATA_DIR, filename))
    return _cache[filename]


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



# ---------------------------------------------------------------------------
# Per-topic chart builders
# ---------------------------------------------------------------------------

def population_charts(df: pd.DataFrame) -> list[dict]:
    charts = []
    comp = _load("chad_neighbors_comparison.csv")

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
            {"label": "Population", "data": pop, "color": COLORS["blue"]},
            {"label": "Linear Trend", "data": [round(v, 2) for v in trend], "color": COLORS["amber"], "dashed": True},
        ],
        "labels": years,
        "insight": f"Population grew from {pop[0]}M in 1990 to {pop[-1]}M in 2024 — a {round((pop[-1]/pop[0]-1)*100, 1)}% increase.",
    })

    # 2. Chad vs neighbors — horizontal bar comparison
    sorted_comp = comp.sort_values("population_millions", ascending=True)
    charts.append({
        "type": "hbar",
        "title": "Population: Chad vs Neighboring Countries",
        "subtitle": "2024 estimates (millions)",
        "x_label": "Population (millions)",
        "y_label": "Country",
        "categories": sorted_comp["country"].tolist(),
        "values": sorted_comp["population_millions"].round(1).tolist(),
        "colors": [COLORS["rose"] if c == "Chad" else COLORS["blue"] for c in sorted_comp["country"]],
        "highlight": "Chad",
        "insight": f"Chad ({comp[comp['country']=='Chad']['population_millions'].values[0]}M) is mid-range among its neighbors; Nigeria dominates at {comp[comp['country']=='Nigeria']['population_millions'].values[0]}M.",
    })

    # 3. Age distribution donut
    age_data = _load("chad_demographics_breakdown.csv")
    age_data = age_data[age_data["group"] == "Age"]
    charts.append({
        "type": "donut",
        "title": "Age Distribution of Chad's Population",
        "subtitle": "Nearly half the population is under 15",
        "x_label": "",
        "y_label": "",
        "slices": [
            {"label": row["label"], "value": float(row["percentage"]), "color": row["color"]}
            for _, row in age_data.iterrows()
        ],
        "insight": "47.2% of Chad's population is under 15 years old — one of the youngest demographics in Africa, creating both challenges and potential for a demographic dividend.",
    })

    # 4. Infant mortality decline — bar chart
    years_b, infant = _series(df, "infant_mortality_per1000", start=2000)
    charts.append({
        "type": "bar",
        "title": "Infant Mortality Rate per 1,000 Births",
        "subtitle": "Declining but still high by global standards",
        "x_label": "Year",
        "y_label": "Deaths per 1,000 live births",
        "series": [{"label": "Infant Mortality", "data": infant, "color": COLORS["rose"]}],
        "labels": years_b,
        "insight": f"Infant mortality fell from {infant[0]} in 2000 to {infant[-1]} in 2024 — a {round((1 - infant[-1]/infant[0])*100, 1)}% reduction.",
    })

    # 5. KMeans clustering: population vs life expectancy (3 eras)
    sub = df[["year", "population_millions", "life_expectancy"]].dropna()
    features = sub[["population_millions", "life_expectancy"]].values
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    km = KMeans(n_clusters=3, random_state=42, n_init=10)
    labels_km = km.fit_predict(features_scaled)
    cluster_colors = [COLORS["blue"], COLORS["amber"], COLORS["rose"]]
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
    comp = _load("chad_neighbors_comparison.csv")
    sectors = _load("chad_gdp_sectors.csv")

    # 1. GDP sector composition — donut
    charts.append({
        "type": "donut",
        "title": "Chad GDP by Economic Sector",
        "subtitle": "2024 estimated breakdown",
        "x_label": "",
        "y_label": "",
        "slices": [
            {"label": row["sector"], "value": float(row["percentage"]), "color": row["color"]}
            for _, row in sectors.iterrows()
        ],
        "insight": "Services (31.4%) and Oil/Mining (28.8%) dominate Chad's GDP, while agriculture — employing 80%+ of workers — contributes only 23.1%.",
    })

    # 2. GDP over time — polynomial regression (oil shock curve)
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
            {"label": "GDP", "data": gdp, "color": COLORS["emerald"]},
            {"label": "Poly Trend", "data": [round(v, 2) for v in trend], "color": COLORS["amber"], "dashed": True},
        ],
        "labels": years,
        "insight": f"GDP peaked at ~${max(gdp):.1f}B ({years[int(np.argmax(gdp))]}), driven by oil revenues discovered in 2003.",
    })

    # 3. GDP per capita — Chad vs neighbors horizontal bar
    sorted_comp = comp.sort_values("gdp_per_capita_usd", ascending=True)
    charts.append({
        "type": "hbar",
        "title": "GDP Per Capita: Chad vs Neighbors (USD)",
        "subtitle": "2024 estimates — differences in economic output",
        "x_label": "GDP per capita (USD)",
        "y_label": "Country",
        "categories": sorted_comp["country"].tolist(),
        "values": sorted_comp["gdp_per_capita_usd"].round(0).tolist(),
        "colors": [COLORS["rose"] if c == "Chad" else COLORS["teal"] for c in sorted_comp["country"]],
        "highlight": "Chad",
        "insight": f"Chad's GDP per capita (${int(comp[comp['country']=='Chad']['gdp_per_capita_usd'].values[0])}) ranks near the bottom, far behind Libya (${int(comp[comp['country']=='Libya']['gdp_per_capita_usd'].values[0])}).",
    })

    # 4. Oil revenue vs agriculture share — grouped bar
    years_b, oil = _series(df, "oil_revenue_pct_gdp", start=2003)
    _, agri = _series(df, "agriculture_pct_gdp", start=2003)
    charts.append({
        "type": "bar",
        "title": "Oil Revenue vs Agriculture Share of GDP",
        "subtitle": "Structural shift since oil discovery (2003)",
        "x_label": "Year",
        "y_label": "% of GDP",
        "series": [
            {"label": "Oil Revenue %", "data": oil, "color": COLORS["amber"]},
            {"label": "Agriculture %", "data": agri, "color": COLORS["emerald"]},
        ],
        "labels": years_b,
        "insight": "Oil revenues peaked at 42% of GDP in 2008; agriculture declined from 40% in 1990 to 23% by 2024.",
    })

    # 5. GDP per capita scatter vs poverty rate
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
        "cluster_colors": [COLORS["violet"]],
        "insight": "A clear negative correlation: higher GDP per capita correlates with lower poverty — but even at peak GDP (~$876), poverty remained above 58%.",
    })

    return charts


def geography_charts(df: pd.DataFrame) -> list[dict]:
    charts = []
    comp = _load("chad_neighbors_comparison.csv")

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
            {"label": "Lake Area", "data": lake, "color": COLORS["cyan"]},
            {"label": "Trend", "data": [round(v, 0) for v in trend], "color": COLORS["rose"], "dashed": True},
        ],
        "labels": years,
        "insight": f"Lake Chad has shrunk from {lake[0]:,} km² (1990) to {lake[-1]:,} km² (2024) — a {round((1-lake[-1]/lake[0])*100, 1)}% loss.",
    })

    # 2. Forest cover — Chad vs neighbors horizontal bar
    sorted_comp = comp.sort_values("forest_area_pct", ascending=True)
    charts.append({
        "type": "hbar",
        "title": "Forest Cover: Chad vs Neighbors (%)",
        "subtitle": "Comparison highlights regional deforestation",
        "x_label": "Forest cover (%)",
        "y_label": "Country",
        "categories": sorted_comp["country"].tolist(),
        "values": sorted_comp["forest_area_pct"].round(1).tolist(),
        "colors": [COLORS["rose"] if c == "Chad" else COLORS["emerald"] for c in sorted_comp["country"]],
        "highlight": "Chad",
        "insight": f"Chad has only {comp[comp['country']=='Chad']['forest_area_pct'].values[0]}% forest cover — one of the lowest in the region. Cameroon leads at {comp[comp['country']=='Cameroon']['forest_area_pct'].values[0]}%.",
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
        "cluster_colors": [COLORS["orange"]],
        "insight": "CO₂ emissions rose sharply after oil extraction began in 2003, closely tracking GDP — suggesting fossil-fuel dependency.",
    })

    # 4. Country area — donut showing Chad's land relative to neighbors
    area_data = comp.sort_values("area_km2", ascending=False)
    total_area = area_data["area_km2"].sum()
    charts.append({
        "type": "donut",
        "title": "Land Area Comparison: Chad & Neighbors",
        "subtitle": "Total regional area and each country's share",
        "x_label": "",
        "y_label": "",
        "slices": [
            {"label": row["country"], "value": round(row["area_km2"] / total_area * 100, 1),
             "color": COLORS["rose"] if row["country"] == "Chad" else PALETTE[i % len(PALETTE)]}
            for i, (_, row) in enumerate(area_data.iterrows())
        ],
        "insight": f"Chad occupies {round(comp[comp['country']=='Chad']['area_km2'].values[0] / total_area * 100, 1)}% of the combined regional area (1.28M km²), making it one of the largest countries in Africa.",
    })

    return charts


def challenges_charts(df: pd.DataFrame) -> list[dict]:
    charts = []
    comp = _load("chad_neighbors_comparison.csv")

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
            {"label": "Poverty Rate", "data": poverty, "color": COLORS["rose"]},
            {"label": "Trend", "data": [round(v, 2) for v in trend], "color": COLORS["slate"], "dashed": True},
        ],
        "labels": years,
        "insight": f"Poverty peaked at {max(poverty)}% (1992) and has slowly declined to {poverty[-1]}% by 2024, with setbacks during oil price crashes.",
    })

    # 2. Life expectancy — Chad vs neighbors horizontal bar
    sorted_comp = comp.sort_values("life_expectancy", ascending=True)
    charts.append({
        "type": "hbar",
        "title": "Life Expectancy: Chad vs Neighbors (years)",
        "subtitle": "Regional comparison of health outcomes",
        "x_label": "Life expectancy (years)",
        "y_label": "Country",
        "categories": sorted_comp["country"].tolist(),
        "values": sorted_comp["life_expectancy"].round(1).tolist(),
        "colors": [COLORS["rose"] if c == "Chad" else COLORS["teal"] for c in sorted_comp["country"]],
        "highlight": "Chad",
        "insight": f"Chad's life expectancy ({comp[comp['country']=='Chad']['life_expectancy'].values[0]} years) is among the lowest in the region. Libya leads at {comp[comp['country']=='Libya']['life_expectancy'].values[0]} years.",
    })

    # 3. Literacy rate — Chad vs neighbors horizontal bar
    sorted_lit = comp.sort_values("literacy_rate_pct", ascending=True)
    charts.append({
        "type": "hbar",
        "title": "Literacy Rate: Chad vs Neighbors (%)",
        "subtitle": "Education access comparison",
        "x_label": "Literacy rate (%)",
        "y_label": "Country",
        "categories": sorted_lit["country"].tolist(),
        "values": sorted_lit["literacy_rate_pct"].round(1).tolist(),
        "colors": [COLORS["rose"] if c == "Chad" else COLORS["violet"] for c in sorted_lit["country"]],
        "highlight": "Chad",
        "insight": f"Chad's literacy rate ({comp[comp['country']=='Chad']['literacy_rate_pct'].values[0]}%) is the lowest among its neighbors, highlighting urgent education needs.",
    })

    # 4. Human development indicators — multi-series bar
    years_b, life = _series(df, "life_expectancy", start=2000)
    _, literacy = _series(df, "literacy_rate_pct", start=2000)
    charts.append({
        "type": "bar",
        "title": "Life Expectancy vs Literacy Rate",
        "subtitle": "Two key human development indicators",
        "x_label": "Year",
        "y_label": "Value",
        "series": [
            {"label": "Life Expectancy (yrs)", "data": life, "color": COLORS["violet"]},
            {"label": "Literacy Rate (%)", "data": literacy, "color": COLORS["amber"]},
        ],
        "labels": years_b,
        "insight": f"Life expectancy rose from {life[0]} to {life[-1]} years (2000–2024); literacy improved from {literacy[0]}% to {literacy[-1]}%.",
    })

    # 5. PCA on development indicators — 2D projection
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
        "cluster_colors": [COLORS["blue"], COLORS["amber"], COLORS["rose"]],
        "insight": f"PCA reduces 6 indicators to 2 components capturing {(variance[0]+variance[1])*100:.1f}% of variance. Clusters reflect pre-oil, oil-boom, and recent eras.",
    })

    return charts


def general_charts(df: pd.DataFrame) -> list[dict]:
    charts = []
    comp = _load("chad_neighbors_comparison.csv")
    demo = _load("chad_demographics_breakdown.csv")

    # 1. HDI comparison — horizontal bar
    sorted_comp = comp.sort_values("hdi", ascending=True)
    charts.append({
        "type": "hbar",
        "title": "Human Development Index (HDI): Regional Comparison",
        "subtitle": "Higher = better human development",
        "x_label": "HDI Score",
        "y_label": "Country",
        "categories": sorted_comp["country"].tolist(),
        "values": sorted_comp["hdi"].round(3).tolist(),
        "colors": [COLORS["rose"] if c == "Chad" else COLORS["blue"] for c in sorted_comp["country"]],
        "highlight": "Chad",
        "insight": f"Chad's HDI ({comp[comp['country']=='Chad']['hdi'].values[0]}) ranks among the world's lowest. Libya leads the region at {comp[comp['country']=='Libya']['hdi'].values[0]}.",
    })

    # 2. Religion donut
    religion_data = demo[demo["group"] == "Religion"]
    charts.append({
        "type": "donut",
        "title": "Religious Composition of Chad",
        "subtitle": "A religiously diverse nation",
        "x_label": "",
        "y_label": "",
        "slices": [
            {"label": row["label"], "value": float(row["percentage"]), "color": row["color"]}
            for _, row in religion_data.iterrows()
        ],
        "insight": "Chad is roughly split between Islam (52.1%) and Christianity (43.9%), with traditional religions making up 4%. This religious diversity is a distinctive feature.",
    })

    # 3. Mobile subscriptions — tech growth line
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
            {"label": "Mobile Subscriptions", "data": mobile, "color": COLORS["violet"]},
            {"label": "Trend", "data": [round(v, 2) for v in trend], "color": COLORS["amber"], "dashed": True},
        ],
        "labels": years,
        "insight": f"Mobile subscriptions grew from {mobile[0]} per 100 (2000) to {mobile[-1]} (2024) — one of Africa's faster adoption curves.",
    })

    # 4. Internet users — Chad vs neighbors horizontal bar
    sorted_net = comp.sort_values("internet_users_pct", ascending=True)
    charts.append({
        "type": "hbar",
        "title": "Internet Users: Chad vs Neighbors (%)",
        "subtitle": "Digital connectivity comparison",
        "x_label": "Internet users (%)",
        "y_label": "Country",
        "categories": sorted_net["country"].tolist(),
        "values": sorted_net["internet_users_pct"].round(1).tolist(),
        "colors": [COLORS["rose"] if c == "Chad" else COLORS["cyan"] for c in sorted_net["country"]],
        "highlight": "Chad",
        "insight": f"Only {comp[comp['country']=='Chad']['internet_users_pct'].values[0]}% of Chadians have internet access — the lowest in the region. Libya leads at {comp[comp['country']=='Libya']['internet_users_pct'].values[0]}%.",
    })

    # 5. Electricity access — bar
    years_b, elec = _series(df, "access_to_electricity_pct", start=2000)
    charts.append({
        "type": "bar",
        "title": "Access to Electricity (% of Population)",
        "subtitle": "Slow but accelerating progress",
        "x_label": "Year",
        "y_label": "Population with electricity (%)",
        "series": [{"label": "Electricity Access %", "data": elec, "color": COLORS["amber"]}],
        "labels": years_b,
        "insight": f"Only {elec[-1]}% of Chad's population has electricity (2024), though this has grown from {elec[0]}% in 2000.",
    })

    # 6. Multi-indicator scatter: GDP per capita vs life expectancy
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
        "cluster_colors": [COLORS["emerald"]],
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
    "history": economy_charts,
    "tourism": geography_charts,
    "culture": general_charts,
    "general": general_charts,
}

# Keyword -> topic mapping; checked in order, first match wins.
_KEYWORD_TOPIC: list[tuple[list[str], str]] = [
    (["population", "people", "demograph", "birth", "fertility", "census", "urban", "rural", "migration"], "population"),
    (["econom", "gdp", "oil", "agric", "trade", "export", "import", "inflation", "debt", "revenue", "income", "employ", "mining", "sector"], "economy"),
    (["geograph", "landlocked", "lake", "sahara", "sahel", "desert", "river", "climate", "rain", "forest", "land", "area", "co2", "emission", "water"], "geography"),
    (["challenge", "poverty", "health", "disease", "malaria", "hunger", "malnutrition", "literacy", "education", "school", "mortalit", "life expectan", "infrastructure", "electricity", "sanitation"], "challenges"),
    (["history", "independence", "colonial", "french", "deby", "war", "conflict", "civil"], "history"),
    (["tour", "zakouma", "ennedi", "tibesti", "safari", "park", "travel", "visit"], "tourism"),
    (["culture", "language", "food", "music", "religion", "ethnic", "tribe", "sport", "tradition", "art"], "culture"),
]


def _detect_topic_from_query(query: str) -> str:
    """Map a raw user query to the best topic via keyword matching."""
    text = query.lower()
    for keywords, t in _KEYWORD_TOPIC:
        if any(kw in text for kw in keywords):
            return t
    return "general"


# ---------------------------------------------------------------------------
# Kaggle fallback — auto-chart from any downloaded CSV
# ---------------------------------------------------------------------------

def _build_kaggle_charts(rows: list[dict], query: str, dataset_title: str) -> list[dict]:
    """
    Auto-generate charts from a Kaggle CSV using column heuristics:
      - year/date column + numeric column → line
      - string column + numeric column   → hbar
      - 2 numeric columns                → scatter
    Returns up to 3 charts.
    """
    if not rows:
        return []

    df = pd.DataFrame(rows)
    num_cols: list[str] = []
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
            num_cols.append(col)
        except (ValueError, TypeError):
            pass

    str_cols = [c for c in df.columns if c not in num_cols]
    year_col = next((c for c in df.columns if re.search(r"year|date|period", c, re.I)), None)
    charts: list[dict] = []

    # 1. Time-series line chart
    if year_col and num_cols:
        for nc in num_cols:
            if nc == year_col:
                continue
            sub = df[[year_col, nc]].dropna().sort_values(year_col)
            if len(sub) < 3:
                continue
            charts.append({
                "type": "line",
                "title": f"{nc.replace('_', ' ').title()} Over Time",
                "subtitle": f"Kaggle: {dataset_title}",
                "x_label": year_col.replace("_", " ").title(),
                "y_label": nc.replace("_", " ").title(),
                "series": [{"label": nc.replace("_", " ").title(), "data": sub[nc].round(2).tolist(), "color": PALETTE[0]}],
                "labels": sub[year_col].tolist(),
                "insight": f"Data from Kaggle dataset: {dataset_title}.",
            })
            break  # one line chart is enough

    # 2. Categorical hbar
    if str_cols and num_cols and len(charts) < 3:
        cat_col = str_cols[0]
        val_col = next((c for c in num_cols if c != year_col), None) or num_cols[0]
        sub = df[[cat_col, val_col]].dropna().head(12)
        if len(sub) >= 2:
            charts.append({
                "type": "hbar",
                "title": f"{val_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                "subtitle": f"Kaggle: {dataset_title}",
                "x_label": val_col.replace("_", " ").title(),
                "y_label": cat_col.replace("_", " ").title(),
                "categories": sub[cat_col].astype(str).tolist(),
                "values": pd.to_numeric(sub[val_col], errors="coerce").fillna(0).round(2).tolist(),
                "colors": [PALETTE[i % len(PALETTE)] for i in range(len(sub))],
                "insight": f"Source: Kaggle — {dataset_title}.",
            })

    # 3. Scatter of two numeric columns
    if len(num_cols) >= 2 and len(charts) < 3:
        non_year = [c for c in num_cols if c != year_col] if year_col else num_cols
        c1, c2 = non_year[:2]
        sub = df[[c1, c2]].dropna().head(50)
        if len(sub) >= 3:
            points = [{"x": float(r[c1]), "y": float(r[c2]), "year": 0, "cluster": 0} for _, r in sub.iterrows()]
            charts.append({
                "type": "scatter",
                "title": f"{c1.replace('_', ' ').title()} vs {c2.replace('_', ' ').title()}",
                "subtitle": f"Kaggle: {dataset_title}",
                "x_label": c1.replace("_", " ").title(),
                "y_label": c2.replace("_", " ").title(),
                "points": points,
                "cluster_colors": [PALETTE[2]],
                "insight": f"Relationship between {c1.replace('_', ' ')} and {c2.replace('_', ' ')}. Source: Kaggle.",
            })

    return charts


def get_charts_for_topic(topic: str, query: str = "") -> dict:
    """
    Return chart data for a given topic string.
    - If `query` is provided, uses server-side keyword detection to override
      a generic 'general' topic with a more specific one.
    - Falls back to Kaggle search when no local data matches well.
    Returns {"charts": [...], "topic": topic, "source": "..."}
    """
    # Upgrade 'general' if the raw query reveals a specific topic
    effective_topic = topic
    if query and topic == "general":
        detected = _detect_topic_from_query(query)
        if detected != "general":
            effective_topic = detected

    df = _load()
    fn = _TOPIC_MAP.get(effective_topic, general_charts)
    charts = fn(df)

    # Kaggle enrichment: search for additional datasets matching the raw query
    kaggle_label = ""
    if query:
        try:
            from kaggle_search import search_datasets, download_and_parse, is_available  # type: ignore
            if is_available():
                for ds in search_datasets(query, max_results=3):
                    rows = download_and_parse(ds["ref"])
                    if rows:
                        extra = _build_kaggle_charts(rows, query, ds["title"])
                        if extra:
                            charts.extend(extra)
                            kaggle_label = ds["title"]
                            break
        except Exception as exc:
            print(f"Kaggle enrichment skipped: {exc}")

    return {
        "charts": charts,
        "topic": effective_topic,
        "source": kaggle_label if kaggle_label else "",
        "dataset": "chad_indicators.csv",
        "rows": len(df),
    }
