// Renders file:line references returned alongside an answer, linked to GitHub
// when we know which repo the answer came from.
export default function Citations({ items, repo }) {
  return (
    <ul className="citations">
      {items.map((c, i) => {
        const label = `${c.file_path}:${c.start_line}-${c.end_line} (${c.kind} ${c.name})`;
        const href = repo
          ? `https://github.com/${repo}/blob/HEAD/${c.file_path}#L${c.start_line}-L${c.end_line}`
          : null;
        return (
          <li key={i}>
            {href ? (
              <a href={href} target="_blank" rel="noreferrer">
                {label}
              </a>
            ) : (
              label
            )}
          </li>
        );
      })}
    </ul>
  );
}
