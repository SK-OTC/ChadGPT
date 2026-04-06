// View — full-screen results overlay rendered when overlayVisible is true.
// Composes highlight cards, DataCharts, and ChatPanel sub-views.

import type { ChartData, Message } from "../model/chad-data";
import { ChatPanel } from "./ChatPanel";
import { DataCharts } from "./DataCharts";

interface ResultsPanelProps {
  visible: boolean;
  question: string;
  highlights: string[];
  charts: ChartData[];
  conversation: Message[];
  chatInput: string;
  onChatInputChange: (value: string) => void;
  onChatSubmit: (message: string) => void;
  onClose: () => void;
}

export function ResultsPanel({
  visible,
  question,
  highlights,
  charts,
  conversation,
  chatInput,
  onChatInputChange,
  onChatSubmit,
  onClose,
}: ResultsPanelProps) {
  if (!visible) return null;

  return (
    <div className="results-overlay">
      <div className="results-body">
        <div className="results-shell">
          <button className="results-back-btn" onClick={onClose}>
            ← Back
          </button>
          <div className="results-layout">
            {/* Left panel: answer visualization (70%) */}
            <div className="results-main-panel">
              <div className="question-card">
                <div className="question-card-content">
                  <h2>{question}</h2>
                  <p>{highlights[0] ?? ""}</p>
                </div>
              </div>
              
              <DataCharts charts={charts} source="World Bank Indicators · scikit-learn analysis" />
            </div>

            {/* Right panel: chat continuation (30%) */}
            <ChatPanel
              conversation={conversation}
              inputValue={chatInput}
              onInputChange={onChatInputChange}
              onSubmit={onChatSubmit}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
