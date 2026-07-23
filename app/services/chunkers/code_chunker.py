"""
Code-Aware Structural Chunker
------------------------------
Strategy: Structure-aware chunking — splits code files at natural boundaries
(function/class definitions) rather than arbitrary character counts or LLM calls.

Why this is the best approach for code:
- Code already has clear structural boundaries (def, class, function keywords)
- LLM chunking wastes tokens and is slow for large codebases
- Structure-aware chunks are self-contained units (a full function/class is meaningful)
- Each chunk carries rich metadata: repo, file path, language, line range

Supported strategies per language:
  - Python:     Split at `def ` and `class ` top-level definitions
  - JavaScript/TypeScript: Split at `function`, `class`, arrow functions
  - Java:       Split at class/method boundaries
  - Markdown:   Split at `##` headings
  - Generic:    Sliding window (800 chars, 150 char overlap)
"""

import re
from app.models.chunk import Chunk


# Max characters per chunk for the sliding window fallback
WINDOW_SIZE = 800
OVERLAP = 150


# ── Language-specific splitters ───────────────────────────────────────────────

def _split_python(content: str, file_meta: dict) -> list[Chunk]:
    """Split Python files at top-level def/class boundaries."""
    # Pattern: line starting with `def ` or `class ` (top-level, no leading spaces)
    pattern = re.compile(r"^(?=def |class )", re.MULTILINE)
    segments = pattern.split(content)

    chunks = []
    for i, segment in enumerate(segments):
        segment = segment.strip()
        if not segment:
            continue

        # Extract function/class name for title
        first_line = segment.split("\n")[0].strip()
        if first_line.startswith("def "):
            name = first_line.split("def ")[1].split("(")[0].strip()
            title = f"Function: {name}"
        elif first_line.startswith("class "):
            name = first_line.split("class ")[1].split("(")[0].split(":")[0].strip()
            title = f"Class: {name}"
        else:
            title = f"Module-level code {i+1}"

        chunks.append(Chunk(
            title=f"{file_meta['name']} — {title}",
            content=segment,
            metadata={
                "repo": file_meta.get("repo", ""),
                "file_path": file_meta.get("path", ""),
                "language": "python",
                "chunking_method": "structural_python",
            }
        ))

    return chunks if chunks else _sliding_window(content, file_meta)


def _split_js_ts(content: str, file_meta: dict) -> list[Chunk]:
    """Split JS/TS files at function/class/arrow function boundaries."""
    # Match: `function foo`, `class Foo`, `const foo = (`, `async function`, `export function`
    pattern = re.compile(
        r"^(?=(?:export\s+)?(?:async\s+)?(?:function|class)\s|"
        r"(?:export\s+)?(?:const|let|var)\s+\w+\s*=\s*(?:async\s*)?\()",
        re.MULTILINE
    )
    segments = pattern.split(content)

    chunks = []
    for i, segment in enumerate(segments):
        segment = segment.strip()
        if not segment or len(segment) < 30:
            continue

        first_line = segment.split("\n")[0].strip()
        # Extract a readable name from first line
        name_match = re.search(r"(?:function|class)\s+(\w+)", first_line)
        if name_match:
            title = f"{name_match.group(0)}"
        else:
            const_match = re.search(r"(?:const|let|var)\s+(\w+)", first_line)
            title = f"Function: {const_match.group(1)}" if const_match else f"Block {i+1}"

        chunks.append(Chunk(
            title=f"{file_meta['name']} — {title}",
            content=segment,
            metadata={
                "repo": file_meta.get("repo", ""),
                "file_path": file_meta.get("path", ""),
                "language": file_meta.get("language", "javascript"),
                "chunking_method": "structural_js_ts",
            }
        ))

    return chunks if chunks else _sliding_window(content, file_meta)


def _split_java(content: str, file_meta: dict) -> list[Chunk]:
    """Split Java files at class and method boundaries."""
    # Match public/private/protected methods and class declarations
    pattern = re.compile(
        r"^(?=\s*(?:public|private|protected|static|abstract|final|class|interface|enum)\s)",
        re.MULTILINE
    )
    segments = pattern.split(content)

    chunks = []
    for i, segment in enumerate(segments):
        segment = segment.strip()
        if not segment or len(segment) < 30:
            continue

        first_line = segment.split("\n")[0].strip()
        name_match = re.search(r"(?:class|interface|enum)\s+(\w+)", first_line)
        method_match = re.search(r"(\w+)\s*\(", first_line)
        if name_match:
            title = f"Class: {name_match.group(1)}"
        elif method_match:
            title = f"Method: {method_match.group(1)}"
        else:
            title = f"Block {i+1}"

        chunks.append(Chunk(
            title=f"{file_meta['name']} — {title}",
            content=segment,
            metadata={
                "repo": file_meta.get("repo", ""),
                "file_path": file_meta.get("path", ""),
                "language": "java",
                "chunking_method": "structural_java",
            }
        ))

    return chunks if chunks else _sliding_window(content, file_meta)


def _split_markdown(content: str, file_meta: dict) -> list[Chunk]:
    """Split Markdown files at ## heading boundaries."""
    pattern = re.compile(r"^(?=#{1,3} )", re.MULTILINE)
    segments = pattern.split(content)

    chunks = []
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue

        first_line = segment.split("\n")[0].strip().lstrip("#").strip()
        title = first_line[:60] if first_line else "Section"

        chunks.append(Chunk(
            title=f"{file_meta['name']} — {title}",
            content=segment,
            metadata={
                "repo": file_meta.get("repo", ""),
                "file_path": file_meta.get("path", ""),
                "language": "markdown",
                "chunking_method": "structural_markdown",
            }
        ))

    return chunks if chunks else _sliding_window(content, file_meta)


def _sliding_window(content: str, file_meta: dict) -> list[Chunk]:
    """
    Generic sliding-window chunker used as fallback for unknown languages
    or when structural splitting yields no results.
    Produces overlapping chunks of WINDOW_SIZE characters.
    """
    chunks = []
    start = 0
    part = 1

    while start < len(content):
        end = start + WINDOW_SIZE
        segment = content[start:end].strip()
        if segment:
            chunks.append(Chunk(
                title=f"{file_meta['name']} — Part {part}",
                content=segment,
                metadata={
                    "repo": file_meta.get("repo", ""),
                    "file_path": file_meta.get("path", ""),
                    "language": file_meta.get("language", "unknown"),
                    "chunking_method": "sliding_window",
                }
            ))
        start += WINDOW_SIZE - OVERLAP
        part += 1

    return chunks


# ── Main dispatcher ────────────────────────────────────────────────────────────

def chunk_code_file(file: dict) -> list[Chunk]:
    """
    Chunk a single code file using the most appropriate strategy for its language.

    Args:
        file: dict with keys: name, path, content, language, repo

    Returns:
        List of Chunk objects ready for embedding and storage.
    """
    content: str = file.get("content", "").strip()
    language: str = file.get("language", "unknown")

    if not content:
        return []

    if language == "python":
        chunks = _split_python(content, file)
    elif language in ("javascript", "typescript"):
        chunks = _split_js_ts(content, file)
    elif language == "java":
        chunks = _split_java(content, file)
    elif language == "markdown":
        chunks = _split_markdown(content, file)
    else:
        # C, Go, Rust, plain text — use sliding window
        chunks = _sliding_window(content, file)

    # Post-processing: drop empty or tiny chunks
    chunks = [c for c in chunks if len(c.content.strip()) >= 30]

    print(
        f"[Code Chunker] '{file.get('path', '?')}' "
        f"({language}) -> {len(chunks)} chunk(s) [{file.get('chunking_method', 'structural')}]"
    )
    return chunks
