// View — hero section with title, tagline, and search input.

import { useState } from "react";
import type { KeyboardEvent } from "react";
import { SEARCH_PLACEHOLDERS } from "../model/chad-data";

interface HeroProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
}

export function Hero({ onSearch, isLoading }: HeroProps) {
  const [value, setValue] = useState("");
  const [placeholderIdx, setPlaceholderIdx] = useState(
    () => Math.floor(Math.random() * SEARCH_PLACEHOLDERS.length),
  );

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key !== "Enter") return;
    e.preventDefault();
    const trimmed = value.trim();
    if (trimmed) {
      onSearch(trimmed);
      setValue("");
    }
  }

  function handleFocus() {
    setPlaceholderIdx((i) => (i + 1) % SEARCH_PLACEHOLDERS.length);
  }

  return (
    <div className="hero">
      <h1>
        Chad<span className="letter-g">G</span>
        <span className="letter-p">P</span>
        <span className="letter-t">T</span>
      </h1>
      <p>Not the site you were looking for? Maybe you meant:</p>
      <a href="https://openai.com/chatgpt">ChatGPT</a>
      <input
        type="text"
        className="search-box"
        placeholder={SEARCH_PLACEHOLDERS[placeholderIdx] ?? SEARCH_PLACEHOLDERS[0]}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onFocus={handleFocus}
        disabled={isLoading}
      />
      {isLoading && (
        <div style={{ marginTop: 10, display: "inline-flex", gap: 8, alignItems: "center" }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--chad-blue)", animation: "pulse 1.4s infinite 0s" }} />
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--chad-blue)", animation: "pulse 1.4s infinite 0.2s" }} />
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--chad-blue)", animation: "pulse 1.4s infinite 0.4s" }} />
          <style>{`@keyframes pulse { 0%,100% { opacity: .4 } 50% { opacity: 1 } }`}</style>
        </div>
      )}
    </div>
  );
}
