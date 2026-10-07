import { useState, useEffect } from "react";
import { askQuestion } from "../api.js";
import Citations from "./Citations.jsx";

const SAMPLE_QUESTIONS = [
  "what does this module implement?",
  "what are the main classes and functions defined here?",
  "what imports and dependencies does this code use?",
  "explain a key function in this codebase.",
];

export default function Chat({ repo }) {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [pending, setPending] = useState(false);

  useEffect(() => {
    setMessages([]);
  }, [repo]);

  async function ask(text) {
    if (!text.trim() || pending) return;

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

  function handleSubmit(event) {
    event.preventDefault();
    ask(question);
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

      {repo && (
        <div className="samples">
          <span className="samples-label">Try a sample question:</span>
          <div className="samples-list">
            {SAMPLE_QUESTIONS.map((q) => (
              <button
                key={q}
                type="button"
                className="sample-chip"
                disabled={pending}
                onClick={() => ask(q)}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
