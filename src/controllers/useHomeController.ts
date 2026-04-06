// Controller layer — custom hook that owns all home-page state and orchestrates
// calls between the Model (chad-data) and the View (React components).

import { useCallback, useState } from "react";
import {
  type Message,
  type TopicKey,
  type ChartData,
  askBackend,
  detectTopic,
  extractHighlights,
  fetchChartData,
  topicData,
} from "../model/chad-data";

export function useHomeController() {
  const [overlayVisible, setOverlayVisible] = useState(false);
  const [question, setQuestion] = useState("");
  const [highlights, setHighlights] = useState<string[]>([]);
  const [sources, setSources] = useState<string[]>([]);
  const [topic, setTopic] = useState<TopicKey>("general");
  const [conversation, setConversation] = useState<Message[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [charts, setCharts] = useState<ChartData[]>([]);

  const config = topicData[topic];

  const search = useCallback(async (query: string) => {
    const trimmed = query.trim();
    if (!trimmed) return;
    setIsLoading(true);
    setCharts([]);
    try {
      const data = await askBackend(trimmed);
      const answer = data.answer ?? "No answer received.";
      const nextTopic = detectTopic(trimmed, data.sources ?? []);
      const nextHighlights = extractHighlights(answer);
      setQuestion(trimmed);
      setSources(data.sources ?? []);
      setTopic(nextTopic);
      setHighlights(nextHighlights);
      setConversation([
        { role: "user", content: trimmed },
        { role: "assistant", content: answer },
      ]);
      setOverlayVisible(true);
      // Fetch charts in background — updates state when ready
      fetchChartData(nextTopic).then((res) => setCharts(res?.charts ?? [])).catch(() => {});
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
      try {
        const data = await askBackend(trimmed, withUser.slice(0, -1));
        const answer = data.answer ?? "No answer received.";
        setConversation([...withUser, { role: "assistant", content: answer }]);
        setQuestion(trimmed);
        setSources(data.sources ?? []);
        setTopic(detectTopic(trimmed, data.sources ?? []));
        setHighlights(extractHighlights(answer));
      } catch (e) {
        setConversation([
          ...withUser,
          {
            role: "assistant",
            content: e instanceof Error ? e.message : "Failed to load API response.",
          },
        ]);
      }
    },
    [conversation],
  );

  const closeOverlay = useCallback(() => {
    setOverlayVisible(false);
    setConversation([]);
    setSources([]);
    setHighlights([]);
    setCharts([]);
  }, []);

  return {
    overlayVisible,
    question,
    highlights,
    config,
    conversation,
    chatInput,
    setChatInput,
    isLoading,
    charts,
    search,
    sendChatMessage,
    closeOverlay,
  };
}
