import { useState, useEffect } from "react";
import { askQuestion } from "../api.js";
import Citations from "./Citations.jsx";

const SAMPLE_QUESTIONS = [
  "what does this module implement?",
  "what are the main classes and functions defined here?",
  "what imports and dependencies does this code use?",
  "explain a key function in this codebase.",
];

function formatResponse(text) {
  const lines = text.split("\n");
  const elements = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (!line.trim()) {
      i++;
      continue;
    }

    if (line.startsWith("* **")) {
      const bulletMatch = line.match(/^\* \*\*([^*]+)\*\*: (.+)$/);
      if (bulletMatch) {
        elements.push(
          <div key={`bullet-${i}`} className="response-bullet">
            <strong>{bulletMatch[1]}:</strong> {bulletMatch[2]}
          </div>
        );
      } else {
        elements.push(
          <div key={`bullet-${i}`} className="response-bullet">
            {line.replace(/^\* /, "")}
          </div>
        );
      }
    } else if (line.startsWith("**") && line.includes("**:")) {
      const headerMatch = line.match(/^\*\*([^*]+)\*\*:?\s*(.*)$/);
      if (headerMatch) {
        elements.push(
          <div key={`header-${i}`} className="response-section">
            <strong>{headerMatch[1]}:</strong> {headerMatch[2]}
          </div>
        );
      }
    } else {
      elements.push(
        <div key={`text-${i}`} className="response-text">
          {line}
        </div>
      );
    }

    i++;
  }

  return elements.length > 0 ? elements : <p>{text}</p>;
};

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
            <div className="message-content">
              {m.role === "assistant" ? formatResponse(m.text) : <p>{m.text}</p>}
            </div>
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
