"""Structural chunking of Python source using tree-sitter.

Splits at function/class granularity rather than fixed-size text windows.
Each chunk carries file path, symbol name, and start/end lines for citations.
"""

from dataclasses import dataclass


@dataclass
class Chunk:
    file_path: str  # repo-relative path
    name: str  # function/class name, or "<module>"
    kind: str  # "function" | "class" | "module"
    start_line: int  # 1-indexed, inclusive
    end_line: int  # 1-indexed, inclusive
    code: str


def chunk_python_file(file_path: str, source: str) -> list[Chunk]:
    """Parse `source` with tree-sitter-python and return function/class chunks.

    TODO: implement.
      - parse source, walk top-level children of the module node
      - emit a Chunk per function_definition / class_definition (and decorated forms)
      - collect leftover top-level code (imports, constants) into a "<module>" chunk
      - fall back to a single whole-file chunk if parsing fails
    """
    raise NotImplementedError
