// View — the three topic quick-start cards.

import { CARD_PROMPTS } from "../model/chad-data";

const CARD_DESCRIPTIONS: Record<string, string> = {
  Geography: "Explore the Sahara Desert and Lake Chad",
  Culture: "Discover traditional music and festivals",
  "General Info": "Learn about the nation and its people",
};

interface InfoCardsProps {
  onCardClick: (query: string) => void;
}

export function InfoCards({ onCardClick }: InfoCardsProps) {
  return (
    <div className="info-cards">
      {Object.entries(CARD_PROMPTS).map(([title, prompt]) => (
        <div className="card" key={title}>
          <h2>{title}</h2>
          <p>{CARD_DESCRIPTIONS[title]}</p>
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault();
              onCardClick(prompt);
            }}
          >
            Take me there!
          </a>
        </div>
      ))}
    </div>
  );
}
