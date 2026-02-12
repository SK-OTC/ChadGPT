// import { APITester } from "./APITester";
import "./index.css";

import logo from "./flag.svg";

export function App() {
  return (
    <div className="app">
      <img src={logo} className="logo" alt="logo" />

      <h1>Bun + React</h1>
      <p>
        Edit <code>src/App.tsx</code> and save to test HMR
      </p>
      {/* <APITester /> */}
    </div>
  );
}

export default App;
