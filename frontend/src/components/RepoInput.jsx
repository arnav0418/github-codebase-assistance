import { useState } from "react";
import { ingestRepo } from "../api.js";

const SAMPLE_REPOS = [
  {
    label: "records",
    url: "https://github.com/kennethreitz/records",
    description: "SQL for Humans — tiny query library (~9 files)",
  },
  {
    label: "colorama",
    url: "https://github.com/tartley/colorama",
    description: "Cross-platform colored terminal text (~23 files)",
  },
  {
    label: "humanize",
    url: "https://github.com/python-humanize/humanize",
    description: "Human-readable numbers, dates, sizes (~13 files)",
  },
  {
    label: "tenacity",
    url: "https://github.com/jd/tenacity",
    description: "Retrying library for Python (~20 files)",
  },
];

const SELF_REPO = "https://github.com/arnav0418/github-codebase-assistance";

export default function RepoInput({ onIngested }) {
  const [url, setUrl] = useState("");
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [pending, setPending] = useState(false);

  async function ingest(repoUrl) {
    if (!repoUrl.trim() || pending) return;

    setPending(true);
    setError(null);
    setStatus(null);
    try {
      const result = await ingestRepo(repoUrl.trim());
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

  function handleSubmit(event) {
    event.preventDefault();
    ingest(url);
  }

  function handleSample(repoUrl) {
    setUrl(repoUrl);
    ingest(repoUrl);
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

      <div className="samples">
        <span className="samples-label">try a sample repo:</span>
        <div className="samples-list">
          {SAMPLE_REPOS.map((repo) => (
            <button
              key={repo.url}
              type="button"
              className="sample-chip"
              disabled={pending}
              title={repo.description}
              onClick={() => handleSample(repo.url)}
            >
              {repo.label}
            </button>
          ))}
        </div>
      </div>

      <div className="samples">
        <span className="samples-label">
          curious how this assistant itself is built? Load its own repo and ask it questions:
        </span>
        <div className="samples-list">
          <button
            type="button"
            className="sample-chip"
            disabled={pending}
            title="This project's own source code"
            onClick={() => handleSample(SELF_REPO)}
          >
            self repo
          </button>
        </div>
      </div>

      {pending && <p className="hint">Cloning and indexing — this can take a minute.</p>}
      {status && <p className="status">{status}</p>}
      {error && <p className="error">{error}</p>}
    </>
  );
}
