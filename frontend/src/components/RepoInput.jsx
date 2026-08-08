import { useState } from "react";

// TODO: on submit, call ingestRepo(url), show pending/error state,
// and call onIngested(result.repo) when it succeeds.
export default function RepoInput({ onIngested }) {
  const [url, setUrl] = useState("");

  return (
    <form className="repo-input" onSubmit={(e) => e.preventDefault()}>
      <input
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="https://github.com/owner/repo"
      />
      <button type="submit">Ingest</button>
    </form>
  );
}
