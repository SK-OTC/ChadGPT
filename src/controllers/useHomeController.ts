// Controller layer — custom hook that owns all home-page state and orchestrates
// calls between the Model (chad-data) and the View (React components).

import { useCallback, useRef, useState } from "react";
import {
  type Message,
  type ChartData,
  askBackend,
  detectTopic,
  extractHighlights,
  fetchChartData,
  fetchGraphStats,
} from "../model/chad-data";

export function useHomeController() {
  const [overlayVisible, setOverlayVisible] = useState(false);
  const [question, setQuestion] = useState("");
  const [title, setTitle] = useState<string | null>(null);
  const [highlights, setHighlights] = useState<string[]>([]);
  const [conversation, setConversation] = useState<Message[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [charts, setCharts] = useState<ChartData[]>([]);
  const [isChartsLoading, setIsChartsLoading] = useState(false);
  const [isChatLoading, setIsChatLoading] = useState(false);

  // ref used to cancel in-flight polls when a new search is triggered
  const searchAbortRef = useRef<{ cancelled: boolean }>({ cancelled: false });

  const search = useCallback(async (query: string) => {
    const trimmed = query.trim();
    if (!trimmed) return;

    // Cancel any previous pending poll
    searchAbortRef.current.cancelled = true;
    const abort = { cancelled: false };
    searchAbortRef.current = abort;

    setIsLoading(true);
    setCharts([]);

    // Poll until the embedding model + knowledge graph are ready
    try {
      let stats = await fetchGraphStats();
      if (!stats.initialized || stats.chunks === 0) {
        setStatusMessage("Preparing knowledge graph…");
        while (!abort.cancelled && (!stats.initialized || stats.chunks === 0)) {
          await new Promise<void>((r) => setTimeout(r, 2500));
          if (abort.cancelled) return;
          stats = await fetchGraphStats();
        }
        if (abort.cancelled) return;
        setStatusMessage(null);
      }
    } catch {
      // Stats endpoint unreachable — proceed and surface any error via askBackend
      if (abort.cancelled) return;
      setStatusMessage(null);
    }

    try {
      const data = await askBackend(trimmed);
      const answer = data.answer ?? "No answer received.";
      const nextTopic = detectTopic(trimmed, data.sources ?? []);
      const nextHighlights = extractHighlights(answer);
      setQuestion(trimmed);
      setTitle(data.title ?? null);
      setHighlights(nextHighlights);
      setConversation([
        { role: "user", content: trimmed },
        { role: "assistant", content: answer },
      ]);
      setOverlayVisible(true);
      // Fetch charts in background — updates state when ready
      setIsChartsLoading(true);
      fetchChartData(nextTopic, trimmed)
        .then((res) => setCharts(res?.charts ?? []))
        .catch(() => {})
        .finally(() => setIsChartsLoading(false));
    } catch (e) {
      setConversation([
        { role: "user", content: trimmed },
        {
          role: "assistant",
          content: e instanceof Error ? e.message : "Failed to load API response.",
        },
      ]);
      setOverlayVisible(true);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const sendChatMessage = useCallback(
    async (message: string) => {
      const trimmed = message.trim();
      if (!trimmed) return;
      const withUser: Message[] = [...conversation, { role: "user", content: trimmed }];
      setConversation(withUser);
      setChatInput("");
      setIsChatLoading(true);
      try {
        const data = await askBackend(trimmed, withUser.slice(0, -1));
        const answer = data.answer ?? "No answer received.";
        setConversation([...withUser, { role: "assistant", content: answer }]);
        setQuestion(trimmed);
        setTitle(data.title ?? null);
        const nextFollowUpTopic = detectTopic(trimmed, data.sources ?? []);
        setHighlights(extractHighlights(answer));
        // Refresh charts for every follow-up question
        setIsChartsLoading(true);
        fetchChartData(nextFollowUpTopic, trimmed)
          .then((res) => setCharts(res?.charts ?? []))
          .catch(() => {})
          .finally(() => setIsChartsLoading(false));
      } catch (e) {
        setConversation([
          ...withUser,
          {
            role: "assistant",
            content: e instanceof Error ? e.message : "Failed to load API response.",
          },
        ]);
      } finally {
        setIsChatLoading(false);
      }
    },
    [conversation],
  );

  const closeOverlay = useCallback(() => {
    // Cancel any in-flight readiness poll
    searchAbortRef.current.cancelled = true;
    setOverlayVisible(false);
    setConversation([]);
    setTitle(null);
    setHighlights([]);
    setCharts([]);
    setIsChartsLoading(false);
    setIsChatLoading(false);
    setStatusMessage(null);
  }, []);

  return {
    overlayVisible,
    question,
    title,
    highlights,
    conversation,
    chatInput,
    setChatInput,
    isLoading,
    statusMessage,
    charts,
    isChartsLoading,
    isChatLoading,
    search,
    sendChatMessage,
    closeOverlay,
  };
}
