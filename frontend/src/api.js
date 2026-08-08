const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function post(path, body) {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(payload?.detail || `Request failed (${response.status})`);
  }
  return payload;
}

export function ingestRepo(repoUrl) {
  return post("/ingest", { repo_url: repoUrl });
}

export function askQuestion(question) {
  return post("/query", { question });
}
