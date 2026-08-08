import { useState } from "react";
import RepoInput from "./components/RepoInput.jsx";
import Chat from "./components/Chat.jsx";

export default function App() {
  const [ingestedRepo, setIngestedRepo] = useState(null);

  return (
    <div className="app">
      <h1>Codebase Assistant</h1>
      <RepoInput onIngested={setIngestedRepo} />
      <Chat repo={ingestedRepo} />
    </div>
  );
}
