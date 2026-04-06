import { useHomeController } from "./controllers/useHomeController";
import { Hero } from "./components/Hero";
import { InfoCards } from "./components/InfoCards";
import { ResultsPanel } from "./components/ResultsPanel";
import { Sidebar } from "./components/Sidebar";

export function App() {
  const ctrl = useHomeController();
  
  return ( 
    <>
      <Sidebar />
      <div className="app">
        <Hero onSearch={ctrl.search} isLoading={ctrl.isLoading} />
        <InfoCards onCardClick={ctrl.search} />
      </div>
      <ResultsPanel
        visible={ctrl.overlayVisible}
        question={ctrl.question}
        highlights={ctrl.highlights}
        charts={ctrl.charts}
        conversation={ctrl.conversation}
        chatInput={ctrl.chatInput}
        onChatInputChange={ctrl.setChatInput}
        onChatSubmit={ctrl.sendChatMessage}
        onClose={ctrl.closeOverlay}
      />
    </>
  );
}
