import { useState } from "react";
import { ingestRepo } from "../api.js";

export default function RepoInput({ onIngested }) {
  const [url, setUrl] = useState("");
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [pending, setPending] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!url.trim() || pending) return;

    setPending(true);
    setError(null);
    setStatus(null);
    try {
      const result = await ingestRepo(url.trim());
      setStatus(
        `Indexed ${result.repo} — ${result.files_indexed} files, ${result.chunks_indexed} chunks.`
      );
      onIngested(result.repo);
    } catch (err) {
      setError(err.message);
      onIngested(null);
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      <form className="repo-input" onSubmit={handleSubmit}>
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://github.com/owner/repo"
          disabled={pending}
        />
        <button type="submit" disabled={pending || !url.trim()}>
          {pending ? "Ingesting…" : "Ingest"}
        </button>
      </form>
      {pending && <p className="hint">Cloning and indexing — this can take a minute.</p>}
      {status && <p className="status">{status}</p>}
      {error && <p className="error">{error}</p>}
    </>
  );
}
