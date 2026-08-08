// Renders file:line references returned alongside an answer.
// TODO: link each citation to its GitHub blob URL at the right line.
export default function Citations({ items }) {
  return (
    <ul className="citations">
      {items.map((c, i) => (
        <li key={i}>
          {c.file_path}:{c.start_line}-{c.end_line} ({c.kind} {c.name})
        </li>
      ))}
    </ul>
  );
}
