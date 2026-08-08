const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function ingestRepo(repoUrl) {
  // TODO: POST {API_URL}/ingest with { repo_url }, return the JSON body
  throw new Error("not implemented");
}

export async function askQuestion(question) {
  // TODO: POST {API_URL}/query with { question }, return { answer, citations }
  throw new Error("not implemented");
}
