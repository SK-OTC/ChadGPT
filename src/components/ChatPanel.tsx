// View — conversational chat panel inside the results overlay.

import { useEffect, useRef } from "react";
import type { FormEvent } from "react";
import type { Message } from "../model/chad-data";

interface ChatPanelProps {
  conversation: Message[];
  inputValue: string;
  onInputChange: (value: string) => void;
  onSubmit: (message: string) => void;
}

export function ChatPanel({ conversation, inputValue, onInputChange, onSubmit }: ChatPanelProps) {
  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [conversation]);

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    onSubmit(inputValue);
  }
  console.log(conversation);
  return (
    <div className="results-chat-panel">
      <div className="results-chat-messages" ref={chatRef}>
        {conversation.map((msg, i) => (
          <article className={`chat-bubble ${msg.role}`} key={i}>
            <p className="chat-role">{msg.role === "user" ? "You" : "ChadGPT"}</p>
            <div className="chat-text">{msg.content}</div>
          </article>
        ))}
      </div>
      <form className="results-chat-form" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Continue conversation..."
          autoComplete="off"
          value={inputValue}
          onChange={(e) => onInputChange(e.target.value)}
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}
