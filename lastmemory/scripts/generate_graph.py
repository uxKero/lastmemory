#!/usr/bin/env python3
"""Generate the lastmemory neural graph from a /memory folder.

Usage:
    python generate_graph.py <memory_dir> [--out <path>] [--now YYYY-MM-DD]

What it does:
    Walks the memory dir (sessions/, zones/, decisions/, scars/, reflections/),
    parses each markdown neuron (frontmatter plus inline typed wikilinks), and
    builds a node and edge graph. Temperature is computed with the MemoryBank
    forgetting formula temperature = exp(-t / S), where t is the number of weeks
    since last_accessed (falling back to created, then to zero) and S is the
    neuron strength (default 1).

    The resulting JSON literal of the form {"nodes":[...],"links":[...]} is
    injected into assets/graph-template.html by replacing the placeholder token
    /*__GRAPH_DATA__*/. If that template does not exist yet (it is produced by a
    separate task), the JSON is written to <memory_dir>/graph.json instead and a
    clear message is printed. The script never fails hard on missing pieces.

    Only the Python standard library is used, so it runs anywhere offline.

Notes:
    --now overrides the reference date used for the temperature clock. If it is
    omitted the current local date is used. Passing --now keeps runs fully
    deterministic (handy for tests and benchmarks).
"""

import argparse
import datetime
import json
import math
import os
import re
import sys


# Ordered list of the neuron sub-folders we scan.
NEURON_FOLDERS = ["sessions", "zones", "decisions", "scars", "reflections"]

# Location of the graph template relative to this script (scripts/ -> assets/).
TEMPLATE_REL_PATH = os.path.join("..", "assets", "graph-template.html")

# The token in the template that gets swapped for the real graph data.
PLACEHOLDER = "/*__GRAPH_DATA__*/"


def strip_inline_comment(value):
    """Remove a trailing YAML style comment (a hash preceded by whitespace).

    Quoted regions are respected so a hash inside quotes is left alone.
    """
    quote = None
    for idx, ch in enumerate(value):
        if ch in ('"', "'"):
            if quote == ch:
                quote = None
            elif quote is None:
                quote = ch
        elif ch == "#" and quote is None and idx > 0 and value[idx - 1] in " \t":
            return value[:idx].rstrip()
    return value


def parse_scalar(raw):
    """Turn a raw frontmatter value string into a scalar or an inline list."""
    value = strip_inline_comment(raw).strip()
    if value == "" or value.lower() in ("null", "none", "~"):
        return None
    # Inline list form: [a, b, c]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if inner == "":
            return []
        parts = [p.strip().strip('"').strip("'") for p in inner.split(",")]
        return [p for p in parts if p != ""]
    # Strip a single pair of surrounding quotes.
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def parse_frontmatter(text):
    """Parse a leading --- fenced YAML-ish block.

    Supports scalars, inline lists (tags: [a, b]) and multi-line lists such as
    links: followed by indented "- item" lines. Returns (meta, body).
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text

    fm_lines = lines[1:end]
    body = "\n".join(lines[end + 1:])

    meta = {}
    i = 0
    while i < len(fm_lines):
        line = fm_lines[i]
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#") or stripped.startswith("-"):
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue

        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()

        if val == "":
            # Possible multi-line list: collect following "- item" lines.
            items = []
            j = i + 1
            while j < len(fm_lines):
                nxt = fm_lines[j].strip()
                if nxt.startswith("- "):
                    items.append(nxt[2:].strip())
                    j += 1
                elif nxt == "":
                    j += 1
                    continue
                else:
                    break
            if items:
                meta[key] = items
                i = j
                continue
            meta[key] = None
            i += 1
            continue

        meta[key] = parse_scalar(val)
        i += 1

    return meta, body


def to_float(value, default):
    """Best effort float conversion with a fallback default."""
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_date(value):
    """Parse a YYYY-MM-DD date, returning a date object or None."""
    if not value:
        return None
    text = str(value).strip()
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", text)
    if not match:
        return None
    try:
        return datetime.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


def compute_temperature(meta, now):
    """Return temperature = exp(-t / S) with t in weeks and S = strength."""
    strength = to_float(meta.get("strength"), 1.0)
    if strength <= 0:
        strength = 1.0

    ref_date = parse_date(meta.get("last_accessed")) or parse_date(meta.get("created"))
    if ref_date is None:
        weeks = 0.0
    else:
        days = (now - ref_date).days
        if days < 0:
            days = 0
        weeks = days / 7.0

    temp = math.exp(-weeks / strength)
    # Clamp defensively into the (0, 1] range.
    if temp > 1.0:
        temp = 1.0
    if temp < 0.0:
        temp = 0.0
    return round(temp, 4)


# Matches an optional relation verb directly before a wikilink, capturing the
# verb (word before the brackets on a list line) and the link target. A target
# may carry a display alias with a pipe, which we drop.
WIKILINK_RE = re.compile(
    r"(?:-\s*([A-Za-z_][A-Za-z0-9_]*)\s+)?\[\[\s*([^\]|]+?)\s*(?:\|[^\]]*)?\]\]"
)


def extract_inline_links(body):
    """Find inline wikilinks in the body: '- verb [[target]]' or bare [[target]].

    Returns a list of (relation, target) tuples. Bare links get the relation
    "reference".
    """
    found = []
    for match in WIKILINK_RE.finditer(body):
        verb = match.group(1)
        target = match.group(2).strip()
        relation = verb if verb else "reference"
        found.append((relation, target))
    return found


def extract_frontmatter_links(meta):
    """Turn frontmatter links: and source_ids: into (relation, target) tuples."""
    edges = []
    raw_links = meta.get("links")
    if isinstance(raw_links, list):
        for item in raw_links:
            item = str(item).strip()
            # Form: "verb [[target]]" or plain "[[target]]" or bare id.
            m = WIKILINK_RE.search(item)
            if m:
                verb = m.group(1)
                target = m.group(2).strip()
                # If the verb was not captured by the list-dash rule, try the
                # leading word of the item instead.
                if not verb:
                    lead = item.split("[[", 1)[0].strip()
                    verb = lead if lead else None
                edges.append((verb if verb else "link", target))
            elif item:
                edges.append(("link", item))
    raw_sources = meta.get("source_ids")
    if isinstance(raw_sources, list):
        for src in raw_sources:
            src = str(src).strip()
            if src:
                edges.append(("source", src))
    return edges


def clean_body_text(body, cap=4000):
    """Flatten a neuron body into plain searchable text.

    Drops heading and list markers, keeps the words and any wikilink targets,
    collapses blank runs, and caps the length so the graph file stays small.
    """
    out = []
    for line in body.splitlines():
        s = line.strip()
        s = re.sub(r"^#{1,6}\s*", "", s)
        s = re.sub(r"^[-*]\s+", "", s)
        if s:
            out.append(s)
    text = "\n".join(out)
    text = re.sub(r"\n{2,}", "\n", text).strip()
    if len(text) > cap:
        text = text[:cap].rstrip() + " ..."
    return text


def infer_type_from_folder(folder):
    """Map a folder name to a neuron type (singular form)."""
    mapping = {
        "sessions": "session",
        "zones": "zone",
        "decisions": "decision",
        "scars": "scar",
        "reflections": "reflection",
    }
    return mapping.get(folder, folder)


def collect_neurons(memory_dir, now):
    """Read every neuron under the known folders. Returns a list of dicts."""
    neurons = []
    for folder in NEURON_FOLDERS:
        folder_path = os.path.join(memory_dir, folder)
        if not os.path.isdir(folder_path):
            continue
        for name in sorted(os.listdir(folder_path)):
            if not name.lower().endswith(".md"):
                continue
            path = os.path.join(folder_path, name)
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    text = handle.read()
            except (OSError, UnicodeDecodeError):
                continue

            meta, body = parse_frontmatter(text)
            neuron_id = meta.get("id")
            if not neuron_id:
                # Fall back to the filename stem as a stable id.
                neuron_id = os.path.splitext(name)[0]
            neuron_id = str(neuron_id).strip()

            ntype = meta.get("type") or infer_type_from_folder(folder)
            summary = meta.get("summary") or ""
            importance = int(to_float(meta.get("importance"), 1.0))
            status = meta.get("status") or "active"
            temperature = compute_temperature(meta, now)

            links = extract_frontmatter_links(meta) + extract_inline_links(body)

            zone = meta.get("zone") or ""
            raw_tags = meta.get("tags")
            if isinstance(raw_tags, list):
                tags = [str(t).strip() for t in raw_tags if str(t).strip()]
            elif raw_tags:
                tags = [str(raw_tags).strip()]
            else:
                tags = []

            neurons.append({
                "id": neuron_id,
                "type": str(ntype).strip(),
                "summary": str(summary).strip(),
                "importance": importance,
                "temperature": temperature,
                "status": str(status).strip(),
                "zone": str(zone).strip(),
                "tags": tags,
                "text": clean_body_text(body),
                "links": links,
                "path": path,
            })
    return neurons


def build_graph(neurons):
    """Build node and edge lists. Returns (nodes, edges, dangling_count)."""
    id_set = set(n["id"] for n in neurons)
    degree = dict((n["id"], 0) for n in neurons)

    edges = []
    seen_edges = set()
    dangling = 0

    for neuron in neurons:
        source = neuron["id"]
        for relation, target in neuron["links"]:
            target = target.strip()
            if not target or target == source:
                continue
            if target not in id_set:
                # Dangling link: skip and count (prefer skipping per spec).
                dangling += 1
                continue
            key = (source, target, relation)
            if key in seen_edges:
                continue
            seen_edges.add(key)
            edges.append({"source": source, "target": target, "relation": relation})
            degree[source] = degree.get(source, 0) + 1
            degree[target] = degree.get(target, 0) + 1

    nodes = []
    for neuron in neurons:
        deg = degree.get(neuron["id"], 0)
        nodes.append({
            "id": neuron["id"],
            "type": neuron["type"],
            "summary": neuron["summary"],
            "importance": neuron["importance"],
            "temperature": neuron["temperature"],
            "status": neuron["status"],
            "zone": neuron.get("zone", ""),
            "tags": neuron.get("tags", []),
            "text": neuron.get("text", ""),
            "degree": deg,
            "orphan": deg == 0,
        })

    return nodes, edges, dangling


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate the lastmemory graph.")
    parser.add_argument("memory_dir", help="Path to the /memory folder.")
    parser.add_argument("--out", default=None, help="Output HTML path (default <memory_dir>/graph.html).")
    parser.add_argument("--now", default=None, help="Reference date YYYY-MM-DD for the temperature clock.")
    args = parser.parse_args(argv)

    memory_dir = args.memory_dir
    if not os.path.isdir(memory_dir):
        print("Error: memory dir not found: %s" % memory_dir)
        return 1

    now = parse_date(args.now) or datetime.date.today()

    neurons = collect_neurons(memory_dir, now)
    nodes, edges, dangling = build_graph(neurons)
    orphans = sum(1 for n in nodes if n["orphan"])

    graph_data = {"nodes": nodes, "links": edges}
    json_literal = json.dumps(graph_data, ensure_ascii=False, indent=2)
    # Escape characters that could terminate or confuse the surrounding inline
    # <script> block (for example a neuron body containing the text </script>).
    # These stay valid JSON and JavaScript parses them back to the same string.
    json_literal = (
        json_literal
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )

    out_path = args.out or os.path.join(memory_dir, "graph.html")
    template_path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), TEMPLATE_REL_PATH))

    if os.path.isfile(template_path):
        try:
            with open(template_path, "r", encoding="utf-8") as handle:
                template = handle.read()
        except (OSError, UnicodeDecodeError) as exc:
            print("Error: could not read template %s (%s)" % (template_path, exc))
            return 1
        if PLACEHOLDER not in template:
            print("Warning: placeholder %s not found in template; appending data as a fallback." % PLACEHOLDER)
            html = template + "\n<script>window.__GRAPH_DATA__ = %s;</script>\n" % json_literal
        else:
            # The template ships the marker directly before a default literal, as in
            #   const GRAPH = /*__GRAPH_DATA__*/ {"nodes":[],"links":[]};
            # Replace the marker plus that trailing default literal, so we do not leave
            # two adjacent object literals (which would be invalid JavaScript).
            marker_plus_default = re.compile(re.escape(PLACEHOLDER) + r"\s*\{[^\n;]*\}")
            if marker_plus_default.search(template):
                html = marker_plus_default.sub(lambda _m: json_literal, template, count=1)
            else:
                html = template.replace(PLACEHOLDER, json_literal, 1)
        try:
            with open(out_path, "w", encoding="utf-8") as handle:
                handle.write(html)
        except OSError as exc:
            print("Error: could not write output %s (%s)" % (out_path, exc))
            return 1
        wrote = out_path
    else:
        # Template not produced yet: write raw JSON so nothing is lost.
        json_path = os.path.join(memory_dir, "graph.json")
        try:
            with open(json_path, "w", encoding="utf-8") as handle:
                handle.write(json_literal)
        except OSError as exc:
            print("Error: could not write JSON %s (%s)" % (json_path, exc))
            return 1
        wrote = json_path
        print("Template missing at %s: wrote graph data to %s instead." % (template_path, json_path))

    print("Graph written to: %s" % wrote)
    print("Summary: %d nodes, %d edges, %d orphans, %d dangling links." % (
        len(nodes), len(edges), orphans, dangling))
    return 0


if __name__ == "__main__":
    sys.exit(main())
