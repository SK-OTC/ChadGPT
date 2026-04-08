import { useHomeController } from "./controllers/useHomeController";
import { Hero } from "./components/Hero";
import { InfoCards } from "./components/InfoCards";
import { ResultsPanel } from "./components/ResultsPanel";

export function App() {
  const ctrl = useHomeController();
  
  return ( 
    <>
      <div className="app">
        <Hero onSearch={ctrl.search} isLoading={ctrl.isLoading} statusMessage={ctrl.statusMessage} />
        <InfoCards onCardClick={ctrl.search} />
      </div>
      <ResultsPanel
        visible={ctrl.overlayVisible}
        question={ctrl.question}
        title={ctrl.title}
        highlights={ctrl.highlights}
        charts={ctrl.charts}
        isChartsLoading={ctrl.isChartsLoading}
        conversation={ctrl.conversation}
        isChatLoading={ctrl.isChatLoading}
        chatInput={ctrl.chatInput}
        onChatInputChange={ctrl.setChatInput}
        onChatSubmit={ctrl.sendChatMessage}
        onClose={ctrl.closeOverlay}
      />
    </>
  );
}
