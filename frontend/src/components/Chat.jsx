import { useState } from "react";
import { askQuestion } from "../api.js";
import Citations from "./Citations.jsx";

export default function Chat({ repo }) {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [pending, setPending] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    const text = question.trim();
    if (!text || pending) return;

    setMessages((prev) => [...prev, { role: "user", text }]);
    setQuestion("");
    setPending(true);
    try {
      const result = await askQuestion(text);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: result.answer, citations: result.citations },
      ]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: "error", text: err.message }]);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="chat">
      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            <p>{m.text}</p>
            {m.citations?.length > 0 && <Citations items={m.citations} repo={repo} />}
          </div>
        ))}
        {pending && <p className="hint">Thinking…</p>}
      </div>
      <form onSubmit={handleSubmit}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={
            repo ? `Ask about ${repo}…` : "Ingest a repo first, then ask a question"
          }
          disabled={pending}
        />
        <button type="submit" disabled={pending || !question.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
