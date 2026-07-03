#!/usr/bin/env python3
"""Measure the token cost of getting up to speed with lastmemory.

Usage:
    python measure_tokens.py <memory_dir> [--baseline-glob <glob>] [--out-dir <dir>]

Goal:
    Compare how many tokens it costs to load enough context to answer "where did
    we leave off and what should we watch out for" two ways:

      (a) lastmemory "on" load, approximated as CRITICAL.md + BRAIN.md + the
          single most relevant zone summary (here: the largest zone file, used
          as a stand in for the one zone a session would actually open).
      (b) baseline "dump everything", the concatenation of every .md file under
          the memory dir (the worst case, to size the saving).
      (c) optionally, any files matched by --baseline-glob, a placeholder slot
          for comparing against context exported by other tools later.

Token counting:
    If the tiktoken package is importable it is used for an exact count.
    Otherwise the script falls back to a documented heuristic of roughly one
    token per 4 characters and labels every result as ESTIMATED.

Output (in <out-dir>, default <memory_dir>/results):
    - token-comparison.svg : a hand built horizontal bar chart (no matplotlib).
    - token-comparison.md  : a markdown table with tokens, percent saved versus
      the baseline, and an honest note about exactness. The date is left as a
      literal placeholder because this script never calls any wall clock or
      random function.

Honesty:
    This is a local example on one memory folder, not an academic benchmark.
    The markdown output states this plainly.

Only the Python standard library is required (tiktoken is optional).
"""

import argparse
import glob as globmod
import math
import os
import sys


CHARS_PER_TOKEN = 4  # Documented fallback heuristic when tiktoken is absent.


def load_counter():
    """Return (count_function, exact_flag).

    The count function maps a text string to an integer token count. exact_flag
    is True when a real tokenizer (tiktoken) is used, False for the heuristic.
    """
    try:
        import tiktoken
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            encoding = tiktoken.encoding_for_model("gpt-4")

        def count_exact(text):
            return len(encoding.encode(text))

        return count_exact, True
    except Exception:
        def count_estimate(text):
            return int(math.ceil(len(text) / float(CHARS_PER_TOKEN)))

        return count_estimate, False


def read_text(path):
    """Read a file as UTF-8, returning an empty string on failure."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except (OSError, UnicodeDecodeError):
        return ""


def all_markdown_files(memory_dir):
    """Return a sorted list of every .md file under the memory dir."""
    found = []
    for root, _dirs, files in os.walk(memory_dir):
        for name in files:
            if name.lower().endswith(".md"):
                found.append(os.path.join(root, name))
    return sorted(found)


def pick_relevant_zone(memory_dir, count):
    """Pick the largest zone file (token wise) as the "most relevant" stand in.

    Returns (path, tokens) or (None, 0) when there are no zone files.
    """
    zones_dir = os.path.join(memory_dir, "zones")
    if not os.path.isdir(zones_dir):
        return None, 0
    best_path = None
    best_tokens = 0
    for name in sorted(os.listdir(zones_dir)):
        if not name.lower().endswith(".md"):
            continue
        path = os.path.join(zones_dir, name)
        tokens = count(read_text(path))
        if tokens > best_tokens:
            best_tokens = tokens
            best_path = path
    return best_path, best_tokens


def measure_lastmemory_on(memory_dir, count):
    """Tokens for CRITICAL.md + BRAIN.md + one relevant zone file."""
    parts = []
    total = 0

    for name in ("CRITICAL.md", "BRAIN.md"):
        path = os.path.join(memory_dir, name)
        if os.path.isfile(path):
            tokens = count(read_text(path))
            total += tokens
            parts.append((name, tokens))
        else:
            parts.append((name + " (missing)", 0))

    zone_path, zone_tokens = pick_relevant_zone(memory_dir, count)
    if zone_path is not None:
        total += zone_tokens
        parts.append((os.path.join("zones", os.path.basename(zone_path)), zone_tokens))
    else:
        parts.append(("zones/(none)", 0))

    return total, parts


def measure_dump_everything(memory_dir, count):
    """Tokens for concatenating every .md under the memory dir."""
    files = all_markdown_files(memory_dir)
    total = 0
    for path in files:
        total += count(read_text(path))
    return total, len(files)


def measure_glob(pattern, count):
    """Tokens for every file matched by a glob pattern."""
    files = sorted(globmod.glob(pattern, recursive=True))
    total = 0
    real_files = 0
    for path in files:
        if os.path.isfile(path):
            total += count(read_text(path))
            real_files += 1
    return total, real_files


def percent_saved(value, baseline):
    """Percent that value saves versus baseline (positive means cheaper)."""
    if baseline <= 0:
        return 0.0
    return (baseline - value) / float(baseline) * 100.0


def escape_xml(text):
    """Escape the handful of characters that matter inside SVG text."""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))


def build_svg(rows, exact):
    """Build a hand made horizontal bar chart SVG.

    rows is a list of (label, tokens) tuples. exact toggles the title note.
    """
    width = 720
    row_height = 46
    top_pad = 70
    bottom_pad = 30
    left_pad = 200
    right_pad = 90
    bar_max = width - left_pad - right_pad

    height = top_pad + row_height * len(rows) + bottom_pad
    max_tokens = max((tok for _label, tok in rows), default=0)
    if max_tokens <= 0:
        max_tokens = 1

    colors = ["#4f9dde", "#e06c5a", "#6ac18f", "#c9a24b", "#9b7ede"]

    parts = []
    parts.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
                 'viewBox="0 0 %d %d" font-family="Segoe UI, Helvetica, Arial, sans-serif">'
                 % (width, height, width, height))
    parts.append('<rect x="0" y="0" width="%d" height="%d" fill="#12161c"/>' % (width, height))

    title = "Tokens to get up to speed"
    subtitle = "exact counts (tiktoken)" if exact else "ESTIMATED counts (approx 1 token / 4 chars)"
    parts.append('<text x="24" y="34" fill="#f2f4f8" font-size="22" font-weight="bold">%s</text>'
                 % escape_xml(title))
    parts.append('<text x="24" y="56" fill="#8b95a3" font-size="13">%s</text>'
                 % escape_xml(subtitle))

    for i, (label, tokens) in enumerate(rows):
        y = top_pad + i * row_height
        bar_w = int(round(bar_max * (tokens / float(max_tokens))))
        if tokens > 0 and bar_w < 2:
            bar_w = 2
        color = colors[i % len(colors)]
        bar_y = y + 8
        bar_h = row_height - 18

        parts.append('<text x="%d" y="%d" fill="#d7dde6" font-size="13" text-anchor="end">%s</text>'
                     % (left_pad - 12, bar_y + bar_h - 6, escape_xml(label)))
        parts.append('<rect x="%d" y="%d" width="%d" height="%d" rx="4" fill="%s"/>'
                     % (left_pad, bar_y, bar_w, bar_h, color))
        parts.append('<text x="%d" y="%d" fill="#f2f4f8" font-size="13">%s</text>'
                     % (left_pad + bar_w + 8, bar_y + bar_h - 6, escape_xml("%d" % tokens)))

    parts.append("</svg>")
    return "\n".join(parts)


def build_markdown(rows, baseline_label, baseline_value, exact):
    """Build the markdown report with a table and honest notes."""
    exact_note = ("Counts are exact, produced with the tiktoken tokenizer."
                  if exact else
                  "Counts are ESTIMATED with a heuristic of roughly 1 token per "
                  "%d characters, because tiktoken was not available." % CHARS_PER_TOKEN)

    lines = []
    lines.append("# Token comparison")
    lines.append("")
    lines.append("<!-- TODO: fill date -->")
    lines.append("")
    lines.append("This is a local example measured on one `/memory` folder. It is "
                 "not an academic benchmark: it only shows the token cost of a few "
                 "loading strategies on this particular brain.")
    lines.append("")
    lines.append("| Scenario | Tokens | Percent saved vs baseline |")
    lines.append("|---|---:|---:|")
    for label, tokens in rows:
        saved = percent_saved(tokens, baseline_value)
        if label == baseline_label:
            saved_text = "baseline"
        else:
            saved_text = "%.1f%%" % saved
        lines.append("| %s | %d | %s |" % (label, tokens, saved_text))
    lines.append("")
    lines.append("Baseline for the percentages: **%s** (%d tokens)."
                 % (baseline_label, baseline_value))
    lines.append("")
    lines.append("_%s_" % exact_note)
    lines.append("")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Measure lastmemory token cost.")
    parser.add_argument("memory_dir", help="Path to the /memory folder.")
    parser.add_argument("--baseline-glob", default=None,
                        help="Optional glob of extra files to count (another tool's export).")
    parser.add_argument("--out-dir", default=None,
                        help="Directory to write results into. Default is <memory_dir>/results.")
    args = parser.parse_args(argv)

    memory_dir = args.memory_dir
    if not os.path.isdir(memory_dir):
        print("Error: memory dir not found: %s" % memory_dir)
        return 1

    count, exact = load_counter()

    on_total, on_parts = measure_lastmemory_on(memory_dir, count)
    dump_total, dump_files = measure_dump_everything(memory_dir, count)

    rows = []
    rows.append(("lastmemory on (L0 + BRAIN + 1 zone)", on_total))
    baseline_label = "baseline: dump every .md (%d files)" % dump_files
    rows.append((baseline_label, dump_total))

    if args.baseline_glob:
        glob_total, glob_files = measure_glob(args.baseline_glob, count)
        rows.append(("baseline-glob (%d files)" % glob_files, glob_total))

    results_dir = args.out_dir or os.path.join(memory_dir, "results")
    try:
        os.makedirs(results_dir, exist_ok=True)
    except OSError as exc:
        print("Error: could not create output dir %s (%s)" % (results_dir, exc))
        return 1

    svg = build_svg(rows, exact)
    md = build_markdown(rows, baseline_label, dump_total, exact)

    svg_path = os.path.join(results_dir, "token-comparison.svg")
    md_path = os.path.join(results_dir, "token-comparison.md")
    try:
        with open(svg_path, "w", encoding="utf-8") as handle:
            handle.write(svg)
        with open(md_path, "w", encoding="utf-8") as handle:
            handle.write(md)
    except OSError as exc:
        print("Error: could not write results (%s)" % exc)
        return 1

    label = "exact" if exact else "ESTIMATED"
    print("Token measurement (%s):" % label)
    for name, tokens in on_parts:
        print("  on part: %-28s %d" % (name, tokens))
    print("  lastmemory on total:   %d" % on_total)
    print("  baseline dump total:   %d (%d files)" % (dump_total, dump_files))
    if args.baseline_glob:
        print("  baseline-glob total:   %d" % rows[-1][1])
    if dump_total > 0:
        print("  saving vs baseline:    %.1f%%" % percent_saved(on_total, dump_total))
    print("Wrote: %s" % svg_path)
    print("Wrote: %s" % md_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
