"""
GitHub API Client
-----------------
Fetches all relevant code files from a GitHub repository using the GitHub REST API.

Supported file extensions: .py, .js, .ts, .java, .cpp, .c, .go, .rs, .md, .txt

Each file is returned as a dict:
  {
    "name":     "filename.py",
    "path":     "src/module/filename.py",
    "content":  "<decoded source code>",
    "language": "python"   # inferred from extension
  }
"""

import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# File extensions to ingest and their language labels
SUPPORTED_EXTENSIONS = {
    ".py":   "python",
    ".js":   "javascript",
    ".ts":   "typescript",
    ".java": "java",
    ".cpp":  "cpp",
    ".c":    "c",
    ".go":   "go",
    ".rs":   "rust",
    ".md":   "markdown",
    ".txt":  "text",
    ".json": "json",
    ".yaml": "yaml",
    ".yml":  "yaml",
    ".toml": "toml",
    ".html": "html",
    ".css":  "css",
    ".sh":   "shell",
    ".xml":  "xml",
    ".sql":  "sql",
}

# Extension-less filenames that are still worth ingesting as plain text
SUPPORTED_BARE_NAMES = {
    "readme", "makefile", "dockerfile", "procfile",
    "license", "contributing", "changelog", "authors",
    "gemfile", "rakefile", "jenkinsfile",
}


def _get_headers(token: str = None) -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    effective_token = token or GITHUB_TOKEN  # per-request token takes priority over env var
    if effective_token:
        headers["Authorization"] = f"Bearer {effective_token}"
    return headers


def _github_get(url: str, token: str = None) -> dict | list:
    """Make a GET request to the GitHub API and return parsed JSON."""
    response = requests.get(url, headers=_get_headers(token), timeout=30)
    if response.status_code != 200:
        raise RuntimeError(
            f"GitHub API error {response.status_code} for {url}: {response.text[:200]}"
        )
    return response.json()


def get_repo_info(owner: str, repo: str, token: str = None) -> dict:
    """Fetch basic repository metadata."""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    return _github_get(url, token)


def _get_default_branch(owner: str, repo: str, token: str = None) -> str:
    """Return the default branch name (e.g. 'main' or 'master')."""
    info = get_repo_info(owner, repo, token)
    return info.get("default_branch", "main")


def _traverse_repo_tree(owner: str, repo: str, branch: str, token: str = None) -> list[dict]:
    """
    Recursively list all blob (file) entries in the repo tree.
    Returns files whose extension is in SUPPORTED_EXTENSIONS OR whose
    bare filename (lowercased) is in SUPPORTED_BARE_NAMES (e.g. README, Makefile).
    """
    url = (
        f"https://api.github.com/repos/{owner}/{repo}"
        f"/git/trees/{branch}?recursive=1"
    )
    data = _github_get(url, token)

    files = []
    for item in data.get("tree", []):
        if item.get("type") != "blob":
            continue
        path: str = item["path"]
        filename = path.split("/")[-1]
        ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""

        if ext in SUPPORTED_EXTENSIONS:
            files.append({
                "path": path,
                "name": filename,
                "language": SUPPORTED_EXTENSIONS[ext],
            })
        elif filename.lower() in SUPPORTED_BARE_NAMES:
            files.append({
                "path": path,
                "name": filename,
                "language": "text",
            })

    return files


def _fetch_file_content(owner: str, repo: str, path: str, branch: str, token: str = None) -> str | None:
    """
    Fetch the raw decoded content of a single file.
    Returns None if the file is binary or cannot be decoded.
    """
    url = (
        f"https://api.github.com/repos/{owner}/{repo}"
        f"/contents/{path}?ref={branch}"
    )
    try:
        data = _github_get(url, token)
        if "content" not in data:
            return None
        decoded = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
        return decoded
    except Exception as e:
        print(f"[GitHub Client] Skipping '{path}': {e}")
        return None


def get_all_repo_files(owner: str, repo: str, token: str = None) -> list[dict]:
    """
    Main entry point: fetches all supported code/text files from a GitHub repo.
    Pass an optional token to override the server-side GITHUB_TOKEN env var
    (useful for accessing private repos per-request).
    """
    print(f"[GitHub Client] Fetching repo: {owner}/{repo}")
    branch = _get_default_branch(owner, repo, token)
    print(f"[GitHub Client] Default branch: {branch}")

    file_list = _traverse_repo_tree(owner, repo, branch, token)
    print(f"[GitHub Client] Found {len(file_list)} supported files in tree.")

    result = []
    for file_meta in file_list:
        content = _fetch_file_content(owner, repo, file_meta["path"], branch, token)
        if content and content.strip():
            file_meta["content"] = content
            result.append(file_meta)
            print(f"[GitHub Client]   + {file_meta['path']} ({file_meta['language']})")
        else:
            print(f"[GitHub Client]   - Skipped (empty/binary): {file_meta['path']}")

    print(f"[GitHub Client] Successfully fetched {len(result)} files.")
    return result
