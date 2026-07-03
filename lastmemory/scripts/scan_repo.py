"""scan_repo: build a compact, token cheap map of an existing repository.

Usage:
    python scan_repo.py <repo_root> [--max-files-per-dir N]

This does NOT write any memory. It prints a small map that the /lastmemory init
procedure reads to propose an initial memory (zones, critical facts, and any
existing decision records). It uses only the standard library.

The output is intentionally short: top level areas with file and line counts,
the dominant languages per area, and the key project files it found. The agent
then reads only those flagged files, not the whole repo, keeping the bootstrap
cheap.
"""

import argparse
import os
import sys


# Directories that are noise for a memory map.
SKIP_DIRS = set([
    ".git", ".hg", ".svn", "node_modules", "dist", "build", "out", "target",
    "__pycache__", ".venv", "venv", "env", "vendor", ".next", ".nuxt",
    "coverage", ".cache", ".idea", ".vscode", "bin", "obj", ".terraform",
    "memory",  # do not scan lastmemory's own folder
])

# Extension to language label.
LANG = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript",
    ".tsx": "TypeScript", ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin",
    ".rb": "Ruby", ".php": "PHP", ".cs": "C#", ".cpp": "C++", ".c": "C", ".h": "C header",
    ".swift": "Swift", ".m": "Objective C", ".scala": "Scala", ".sh": "Shell",
    ".sql": "SQL", ".css": "CSS", ".scss": "SCSS", ".html": "HTML", ".vue": "Vue",
    ".svelte": "Svelte", ".md": "Markdown", ".json": "JSON", ".yml": "YAML",
    ".yaml": "YAML", ".toml": "TOML",
}

# Root level files that signal stack, tooling, or decisions.
KEY_FILES = [
    "README.md", "README", "readme.md", "package.json", "pyproject.toml",
    "requirements.txt", "setup.py", "go.mod", "Cargo.toml", "pom.xml",
    "build.gradle", "Gemfile", "composer.json", "Dockerfile",
    "docker-compose.yml", "docker-compose.yaml", "tsconfig.json", "Makefile",
    ".env.example", "CONTRIBUTING.md", "ARCHITECTURE.md",
]

# Folders that usually hold existing decision records (ADRs).
ADR_DIRS = [
    os.path.join("docs", "decisions"),
    os.path.join("docs", "adr"),
    os.path.join("docs", "architecture", "decisions"),
    "adr",
    "decisions",
]

TEXT_EXTS = set(LANG.keys())


def count_lines(path):
    """Best effort line count for a text file. Returns 0 on any problem."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return 0


def top_area(rel_path):
    """The area a file belongs to: its first path segment, or 'root'."""
    parts = rel_path.replace("\\", "/").split("/")
    if len(parts) == 1:
        return "root"
    # For a src/ layout, use the second level so areas are meaningful.
    if parts[0] in ("src", "app", "lib", "packages", "apps") and len(parts) > 2:
        return parts[0] + "/" + parts[1]
    return parts[0]


def scan(repo_root):
    areas = {}
    key_found = []
    adr_found = []

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".git")]
        for name in files:
            abs_path = os.path.join(root, name)
            rel = os.path.relpath(abs_path, repo_root)
            area = top_area(rel)
            ext = os.path.splitext(name)[1].lower()

            entry = areas.setdefault(area, {"files": 0, "lines": 0, "langs": {}})
            entry["files"] += 1
            if ext in TEXT_EXTS:
                lines = count_lines(abs_path)
                entry["lines"] += lines
                lang = LANG.get(ext, ext)
                entry["langs"][lang] = entry["langs"].get(lang, 0) + lines

            # Key root files.
            if os.path.dirname(rel) == "" and name in KEY_FILES:
                key_found.append(rel)

        # Existing ADR folders.
        rel_dir = os.path.relpath(root, repo_root).replace("\\", "/")
        for adr in ADR_DIRS:
            if rel_dir == adr.replace("\\", "/"):
                for name in files:
                    if name.lower().endswith(".md"):
                        adr_found.append(os.path.join(rel_dir, name))

    return areas, sorted(set(key_found)), sorted(set(adr_found))


def dominant_langs(langs, top=2):
    ordered = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)
    return ", ".join(name for name, _ in ordered[:top]) if ordered else "n/a"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Map a repo for lastmemory init.")
    parser.add_argument("repo_root", help="Path to the repository root.")
    args = parser.parse_args(argv)

    root = args.repo_root
    if not os.path.isdir(root):
        print("Error: repo root not found: %s" % root)
        return 1

    areas, key_found, adr_found = scan(root)

    # Rank code areas by lines of code, drop the root bucket to the end.
    ranked = sorted(
        areas.items(),
        key=lambda kv: (kv[0] == "root", -kv[1]["lines"]),
    )

    print("lastmemory repo map")
    print("===================")
    print("Root: %s" % os.path.abspath(root))
    print("")
    print("Code areas (candidate zones), by size:")
    for area, data in ranked:
        if data["lines"] == 0 and area == "root":
            continue
        print("  %-28s %5d files  %7d lines  [%s]" % (
            area, data["files"], data["lines"], dominant_langs(data["langs"])))

    print("")
    print("Key project files (read these to infer stack and critical facts):")
    if key_found:
        for f in key_found:
            print("  %s" % f)
    else:
        print("  none found at root")

    print("")
    print("Existing decision records (import as decision neurons):")
    if adr_found:
        for f in adr_found:
            print("  %s" % f)
    else:
        print("  none found")

    print("")
    print("Next: /lastmemory init reads the flagged files only, proposes zones and")
    print("critical facts marked as bootstrapped (low strength, needs verification),")
    print("and asks for approval before writing anything.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
