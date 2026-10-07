import { useState, useEffect } from "react";
import { askQuestion } from "../api.js";
import Citations from "./Citations.jsx";

// Phrased around real file/symbol names: chunks are embedded with their path and
// symbol name, so these stay well inside the retrieval distance threshold.
const SAMPLE_QUESTIONS_BY_REPO = {
  "kennethreitz/records": [
    "How does the Database class in records.py run a query?",
    "What is the difference between Record and RecordCollection?",
    "How do first(), one() and scalar() work on a RecordCollection?",
    "How does Record.export() convert rows to other formats?",
  ],
  "tartley/colorama": [
    "What does init() in initialise.py do?",
    "How does AnsiToWin32 convert ANSI escape codes into Windows console calls?",
    "How are AnsiFore, AnsiBack and AnsiStyle defined in ansi.py?",
    "How does StreamWrapper wrap stdout and stderr?",
  ],
  "python-humanize/humanize": [
    "How does naturalsize in filesize.py format file sizes?",
    "How does naturaltime compute a relative time like '3 hours ago'?",
    "How does intcomma add thousands separators to a number?",
    "How does i18n.activate switch the translation locale?",
  ],
  "arnav0418/github-codebase-assistance": [
    "How does chunk_python_file split a source file into chunks?",
    "How does search() in store.py query Chroma and filter by MAX_DISTANCE?",
    "How does build_prompt in query.py assemble the prompt from retrieved hits?",
    "How does the ingest endpoint in main.py clone, chunk and index a repo?",
  ],
};

const DEFAULT_SAMPLE_QUESTIONS = [
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
            {(SAMPLE_QUESTIONS_BY_REPO[repo] ?? DEFAULT_SAMPLE_QUESTIONS).map((q) => (
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
