"""Structural chunking of Python source using tree-sitter.

Splits at function/class granularity rather than fixed-size text windows.
Each chunk carries file path, symbol name, and start/end lines for citations.
"""

from dataclasses import dataclass
from functools import lru_cache

import tree_sitter_python
from tree_sitter import Language, Node, Parser

# Definitions we emit as their own chunk. A decorated_definition wraps one of
# these, so we unwrap it and keep the outer node's line span (decorators included).
DEF_TYPES = {"function_definition", "class_definition"}


@dataclass
class Chunk:
    file_path: str  # repo-relative path
    name: str  # function/class name, or "<module>"
    kind: str  # "function" | "class" | "module"
    start_line: int  # 1-indexed, inclusive
    end_line: int  # 1-indexed, inclusive
    code: str


@lru_cache(maxsize=1)
def _parser() -> Parser:
    return Parser(Language(tree_sitter_python.language()))


def _node_name(node: Node) -> str:
    name = node.child_by_field_name("name")
    return name.text.decode("utf-8", "replace") if name is not None else "<anonymous>"


def _unwrap(node: Node) -> Node | None:
    """Return the definition inside a decorated_definition, if there is one."""
    if node.type in DEF_TYPES:
        return node
    if node.type == "decorated_definition":
        inner = node.child_by_field_name("definition")
        if inner is not None and inner.type in DEF_TYPES:
            return inner
    return None


def chunk_python_file(file_path: str, source: str) -> list[Chunk]:
    """Parse `source` with tree-sitter-python and return function/class chunks.

    Top-level code that isn't a function or class (imports, constants, `main`
    guards) is collected into a single "<module>" chunk so it stays searchable.
    Unparseable files fall back to one whole-file chunk.
    """
    lines = source.splitlines()
    if not lines:
        return []

    try:
        tree = _parser().parse(source.encode("utf-8"))
        root = tree.root_node
    except Exception:
        return [_whole_file(file_path, source, len(lines))]

    chunks: list[Chunk] = []
    covered: set[int] = set()  # 0-indexed lines claimed by a def chunk

    for child in root.children:
        definition = _unwrap(child)
        if definition is None:
            continue

        # `child` rather than `definition` so decorators are part of the span.
        start, end = child.start_point[0], child.end_point[0]
        kind = "function" if definition.type == "function_definition" else "class"
        chunks.append(
            Chunk(
                file_path=file_path,
                name=_node_name(definition),
                kind=kind,
                start_line=start + 1,
                end_line=end + 1,
                code="\n".join(lines[start : end + 1]),
            )
        )
        covered.update(range(start, end + 1))

    # Top-level code outside any def: imports, constants, `if __name__` blocks.
    leftover = [i for i in range(len(lines)) if i not in covered and lines[i].strip()]
    if leftover:
        chunks.append(
            Chunk(
                file_path=file_path,
                name="<module>",
                kind="module",
                start_line=leftover[0] + 1,
                end_line=leftover[-1] + 1,
                # Only the uncovered lines — skips the def bodies in between.
                code="\n".join(lines[i] for i in leftover),
            )
        )

    if not chunks:
        return [_whole_file(file_path, source, len(lines))]

    chunks.sort(key=lambda c: c.start_line)
    return chunks


def _whole_file(file_path: str, source: str, line_count: int) -> Chunk:
    return Chunk(
        file_path=file_path,
        name="<module>",
        kind="module",
        start_line=1,
        end_line=line_count,
        code=source,
    )
