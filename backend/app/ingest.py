"""Clone a GitHub repo and walk it for Python files."""

SKIP_DIRS = {".git", "venv", ".venv", "__pycache__", "node_modules", ".mypy_cache",
             ".pytest_cache", "site-packages", "dist", "build", ".tox"}


def clone_repo(repo_url: str, dest_dir: str) -> str:
    """Shallow-clone `repo_url` into `dest_dir`; return the local checkout path.

    TODO: implement.
      - validate it looks like a GitHub URL
      - `git clone --depth 1`
      - wipe/reuse an existing checkout for the same repo
    """
    raise NotImplementedError


def iter_python_files(root: str):
    """Yield (repo_relative_path, absolute_path) for each .py file under `root`.

    TODO: implement — os.walk, pruning SKIP_DIRS in place, filtering to .py.
    """
    raise NotImplementedError
