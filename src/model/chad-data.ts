// Model layer — canonical types, data, constants, and pure API helpers.
// Imported by controllers and views; never contains React or DOM code.

export type Tone = "blue" | "yellow" | "red";

export type Metric = { label: string; value: string };

export type Bar = { label: string; value: number; tone: Tone };

export type TopicConfig = { title: string; metrics: Metric[]; bars: Bar[] };

export type TopicKey =
  | "population"
  | "geography"
  | "economy"
  | "tourism"
  | "culture"
  | "history"
  | "challenges"
  | "general";

export type Message = {
  role: "user" | "assistant";
  content: string;
  web_sources?: { title: string; url: string }[];
};

export type AskResponse = {
  answer?: string;
  title?: string;
  sources?: string[];
  graph_sources?: { title: string; url: string }[];
  web_sources?: { title: string; url: string }[];
  show_visualization?: boolean;
};

export type ChartSeries = { label: string; data: number[]; color: string; dashed?: boolean };
export type ScatterPoint = { x: number; y: number; year: number; cluster: number };
export type DonutSlice = { label: string; value: number; color: string };
export type ChartData = {
  type: "line" | "bar" | "scatter" | "donut" | "hbar";
  title: string;
  subtitle?: string;
  x_label: string;
  y_label: string;
  series?: ChartSeries[];
  labels?: (string | number)[];
  points?: ScatterPoint[];
  cluster_colors?: string[];
  slices?: DonutSlice[];
  categories?: string[];
  values?: number[];
  colors?: string[];
  highlight?: string;
  insight: string;
};
export type AnalysisResponse = {
  charts: ChartData[];
  topic: string;
  source: string;
};

export const SEARCH_PLACEHOLDERS = [
  "Fun facts about Chad",
  "National animal of Chad",
  "Is Chad a landlocked country?",
  "What is the currency of Chad?",
  "Population of Chad",
  "Capital of Chad",
];

export const CARD_PROMPTS: Record<string, string> = {
  Geography: "What is the geography of Chad?",
  Culture: "Tell me about the culture of Chad",
  "General Info": "What should I know about Chad?",
};

export const topicData: Record<TopicKey, TopicConfig> = {
  population: {
    title: "Population profile",
    metrics: [
      { label: "Population", value: "19M" },
      { label: "Under 15", value: "47%" },
      { label: "Under 25", value: "65%" },
      { label: "Capital city", value: "1.5M+" },
    ],
    bars: [
      { label: "Youth share", value: 65, tone: "blue" },
      { label: "Urban concentration", value: 38, tone: "yellow" },
      { label: "Rural population", value: 62, tone: "red" },
      { label: "Linguistic diversity", value: 84, tone: "blue" },
    ],
  },
  geography: {
    title: "Geography profile",
    metrics: [
      { label: "Area", value: "1.284M km²" },
      { label: "Landlocked", value: "Yes" },
      { label: "Bioclimatic zones", value: "4" },
      { label: "Lake shrinkage", value: "95%" },
    ],
    bars: [
      { label: "Saharan north", value: 55, tone: "yellow" },
      { label: "Sahelian belt", value: 28, tone: "red" },
      { label: "Savanna south", value: 17, tone: "blue" },
      { label: "Environmental stress", value: 78, tone: "red" },
    ],
  },
  economy: {
    title: "Economy profile",
    metrics: [
      { label: "Poverty rate", value: "80%" },
      { label: "Oil export role", value: "60%" },
      { label: "Agriculture workforce", value: "80%+" },
      { label: "GDP per capita", value: "$1,651" },
    ],
    bars: [
      { label: "Agriculture", value: 82, tone: "blue" },
      { label: "Oil dependency", value: 60, tone: "red" },
      { label: "Livestock activity", value: 52, tone: "yellow" },
      { label: "Diversification", value: 26, tone: "blue" },
    ],
  },
  tourism: {
    title: "Tourism profile",
    metrics: [
      { label: "Zakouma elephants", value: "500+" },
      { label: "Bird species", value: "373+" },
      { label: "Highest peak", value: "3,445m" },
      { label: "UNESCO lake system", value: "18 lakes" },
    ],
    bars: [
      { label: "Wildlife appeal", value: 88, tone: "blue" },
      { label: "Cultural events", value: 58, tone: "yellow" },
      { label: "Adventure travel", value: 79, tone: "red" },
      { label: "Infrastructure readiness", value: 24, tone: "red" },
    ],
  },
  culture: {
    title: "Culture profile",
    metrics: [
      { label: "Ethnic groups", value: "200+" },
      { label: "Languages", value: "120+" },
      { label: "Official languages", value: "2" },
      { label: "Private radio stations", value: "13" },
    ],
    bars: [
      { label: "Language diversity", value: 91, tone: "blue" },
      { label: "Regional traditions", value: 77, tone: "yellow" },
      { label: "Media access", value: 34, tone: "red" },
      { label: "Festival visibility", value: 63, tone: "blue" },
    ],
  },
  history: {
    title: "History profile",
    metrics: [
      { label: "Human settlement", value: "9,000 yrs" },
      { label: "Independence", value: "1960" },
      { label: "Peace restored", value: "1990" },
      { label: "Latest election", value: "2024" },
    ],
    bars: [
      { label: "Ancient legacy", value: 86, tone: "blue" },
      { label: "Colonial period", value: 44, tone: "yellow" },
      { label: "Modern instability", value: 72, tone: "red" },
      { label: "Political transition", value: 51, tone: "blue" },
    ],
  },
  challenges: {
    title: "Challenges profile",
    metrics: [
      { label: "Life expectancy", value: "52 yrs" },
      { label: "Women literacy", value: "25%" },
      { label: "Doctors ratio", value: "1:25k" },
      { label: "Lake shrinkage", value: "95%" },
    ],
    bars: [
      { label: "Poverty pressure", value: 84, tone: "red" },
      { label: "Health strain", value: 74, tone: "yellow" },
      { label: "Climate stress", value: 81, tone: "red" },
      { label: "Infrastructure gap", value: 76, tone: "blue" },
    ],
  },
  general: {
    title: "National overview",
    metrics: [
      { label: "Population", value: "19M" },
      { label: "Area", value: "1.284M km²" },
      { label: "Official languages", value: "French, Arabic" },
      { label: "Capital", value: "N'Djamena" },
    ],
    bars: [
      { label: "Scale", value: 80, tone: "blue" },
      { label: "Diversity", value: 88, tone: "yellow" },
      { label: "Natural resources", value: 61, tone: "red" },
      { label: "Development challenges", value: 79, tone: "red" },
    ],
  },
};

export function detectTopic(question: string, sources: string[]): TopicKey {
  const text = `${question} ${sources.join(" ")}`.toLowerCase();
  if (text.includes("population") || text.includes("people") || text.includes("demograph")) return "population";
  if (text.includes("geograph") || text.includes("landlocked") || text.includes("lake") || text.includes("desert")) return "geography";
  if (text.includes("econom") || text.includes("oil") || text.includes("agric")) return "economy";
  if (text.includes("tour") || text.includes("zakouma") || text.includes("ennedi") || text.includes("travel")) return "tourism";
  if (text.includes("culture") || text.includes("language") || text.includes("food") || text.includes("sport")) return "culture";
  if (text.includes("history") || text.includes("independence") || text.includes("deby") || text.includes("colon")) return "history";
  if (text.includes("challenge") || text.includes("poverty") || text.includes("health") || text.includes("infrastructure")) return "challenges";
  return "general";
}

export function extractHighlights(answer: string): string[] {
  const clean = answer.replace(/\s+/g, " ").trim();
  const sentences = clean.split(/(?<=[.!?])\s+/).filter(Boolean).slice(0, 4);
  return sentences.length ? sentences : [clean || "No answer returned from the API."];
}

export async function askBackend(question: string, history: Message[] = []): Promise<AskResponse> {
  const base = `http://${window.location.hostname}:8000`;
  const response = await fetch(`${base}/api/graph-ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, history }),
  });
  if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
  return response.json() as Promise<AskResponse>;
}

export async function fetchChartData(topic: string, query = ""): Promise<AnalysisResponse> {
  const base = `http://${window.location.hostname}:8000`;
  let url = `${base}/api/analyze?topic=${encodeURIComponent(topic)}`;
  if (query) url += `&q=${encodeURIComponent(query)}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
  return response.json() as Promise<AnalysisResponse>;
}

export type GraphStats = {
  initialized: boolean;
  chunks: number;
  error?: string | null;
};

export async function fetchGraphStats(): Promise<GraphStats> {
  const base = `http://${window.location.hostname}:8000`;
  const response = await fetch(`${base}/api/graph-stats`);
  if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
  return response.json() as Promise<GraphStats>;
}

