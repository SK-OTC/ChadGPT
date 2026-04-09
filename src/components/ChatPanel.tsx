// View — conversational chat panel inside the results overlay.

import { useEffect, useRef } from "react";
import type { FormEvent } from "react";
import type { Message } from "../model/chad-data";

interface ChatPanelProps {
  conversation: Message[];
  inputValue: string;
  onInputChange: (value: string) => void;
  onSubmit: (message: string) => void;
  isTyping?: boolean;
}

export function ChatPanel({ conversation, inputValue, onInputChange, onSubmit, isTyping = false }: ChatPanelProps) {
  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [conversation, isTyping]);

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    onSubmit(inputValue);
  }

  return (
    <div className="results-chat-panel">
      <div className="results-chat-messages" ref={chatRef}>
        {conversation.map((msg, i) => (
          <article className={`chat-bubble ${msg.role}`} key={i}>
            <p className="chat-role">{msg.role === "user" ? "You" : "ChadGPT"}</p>
            <div className="chat-text">{msg.content}</div>
            {msg.role === "assistant" && msg.web_sources && msg.web_sources.length > 0 && (
              <div className="chat-web-sources">
                <p className="chat-sources-label">Web Sources</p>
                <ul className="chat-sources-list">
                  {msg.web_sources.map((src, j) => (
                    <li key={j}>
                      <a href={src.url} target="_blank" rel="noopener noreferrer">{src.title}</a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </article>
        ))}
        {isTyping && (
          <article className="chat-bubble assistant">
            <p className="chat-role">ChadGPT</p>
            <div className="chat-typing-indicator">
              <span /><span /><span />
            </div>
          </article>
        )}
      </div>
      <form className="results-chat-form" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Continue conversation..."
          autoComplete="off"
          value={inputValue}
          onChange={(e) => onInputChange(e.target.value)}
          disabled={isTyping}
        />
        <button type="submit" disabled={isTyping}>Send</button>
      </form>
    </div>
  );
}
