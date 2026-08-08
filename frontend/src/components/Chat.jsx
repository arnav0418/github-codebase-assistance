import { useState } from "react";
import Citations from "./Citations.jsx";

// TODO: on submit, call askQuestion(question), append { role, text, citations }
// to messages, and render each turn with its citations underneath.
export default function Chat({ repo }) {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");

  return (
    <div className="chat">
      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            <p>{m.text}</p>
            {m.citations && <Citations items={m.citations} />}
          </div>
        ))}
      </div>
      <form onSubmit={(e) => e.preventDefault()}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about the codebase..."
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}
