"""Clone a GitHub repo and walk it for Python files."""

import os
import re
import shutil
import subprocess
from urllib.parse import urlparse

SKIP_DIRS = {".git", "venv", ".venv", "__pycache__", "node_modules", ".mypy_cache",
             ".pytest_cache", "site-packages", "dist", "build", ".tox"}

# Skip files large enough to be generated or vendored rather than hand-written.
MAX_FILE_BYTES = 512 * 1024

_SLUG_RE = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")


def parse_repo_slug(repo_url: str) -> str:
    """Return "owner/repo" for a GitHub URL, or raise ValueError."""
    parsed = urlparse(repo_url.strip())
    if parsed.scheme not in ("http", "https") or parsed.hostname not in (
        "github.com",
        "www.github.com",
    ):
        raise ValueError("Only https://github.com/owner/repo URLs are supported")

    slug = parsed.path.strip("/").removesuffix(".git")
    if not _SLUG_RE.match(slug):
        raise ValueError("URL must look like https://github.com/owner/repo")
    return slug


def clone_repo(repo_url: str, dest_dir: str) -> tuple[str, str]:
    """Shallow-clone `repo_url` under `dest_dir`. Return (slug, checkout_path)."""
    slug = parse_repo_slug(repo_url)
    checkout = os.path.join(dest_dir, slug.replace("/", "__"))

    # Clean up old clones to prevent disk fill-up. Only keep the current one.
    try:
        for old_dir in os.listdir(dest_dir):
            old_path = os.path.join(dest_dir, old_dir)
            if old_path != checkout and os.path.isdir(old_path):
                shutil.rmtree(old_path, ignore_errors=True)
    except OSError:
        pass

    # Always re-clone: cheaper to redo a depth-1 clone than to reconcile a stale one.
    if os.path.exists(checkout):
        shutil.rmtree(checkout, ignore_errors=True)
    os.makedirs(os.path.dirname(checkout) or ".", exist_ok=True)

    result = subprocess.run(
        ["git", "clone", "--depth", "1", f"https://github.com/{slug}.git", checkout],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        shutil.rmtree(checkout, ignore_errors=True)
        raise RuntimeError(f"git clone failed: {result.stderr.strip()[:400]}")

    return slug, checkout


def iter_python_files(root: str):
    """Yield (repo_relative_path, absolute_path) for each .py file under `root`."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            absolute = os.path.join(dirpath, filename)
            try:
                if os.path.getsize(absolute) > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            relative = os.path.relpath(absolute, root).replace(os.sep, "/")
            yield relative, absolute
