#!/usr/bin/env python3
"""Report the health of a lastmemory /memory brain.

Usage:
    python brain_stats.py <memory_dir> [--now YYYY-MM-DD]

What it reports:
    - Total neurons broken down by type.
    - Hot / warm / cold counts using the MemoryBank temperature formula
      temperature = exp(-t / S) with thresholds hot > 0.6, warm 0.15 to 0.6,
      cold < 0.15.
    - Number of orphan neurons (no resolved links in or out).
    - Total size of the memory folder in KB.
    - Line count of BRAIN.md.
    - Sum of importance of session neurons created since the last dream (the
      last dream date is read from the BRAIN.md header if present).
    - A "dream recommended" recommendation, true when any of these hold:
        cold >= 3, BRAIN.md over 50 lines, accumulated session importance
        at or above dream_trigger (read from config.md, default 40), or any
        scar past its expires_hint date.

    Only the Python standard library is used, so it runs anywhere offline.

Notes:
    --now overrides the reference date used for the temperature clock and for
    the scar expiry check. Without it the current local date is used.
"""

import argparse
import datetime
import math
import os
import re
import sys


NEURON_FOLDERS = ["sessions", "zones", "decisions", "scars", "reflections"]

HOT_THRESHOLD = 0.6
WARM_THRESHOLD = 0.15
BRAIN_LINE_LIMIT = 50
DEFAULT_DREAM_TRIGGER = 40
COLD_COUNT_TRIGGER = 3


def strip_inline_comment(value):
    """Remove a trailing YAML style comment (a hash preceded by whitespace)."""
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
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if inner == "":
            return []
        parts = [p.strip().strip('"').strip("'") for p in inner.split(",")]
        return [p for p in parts if p != ""]
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def parse_frontmatter(text):
    """Parse a leading --- fenced YAML-ish block. Returns (meta, body)."""
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
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(value).strip())
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
    if temp > 1.0:
        temp = 1.0
    if temp < 0.0:
        temp = 0.0
    return temp


WIKILINK_RE = re.compile(r"\[\[\s*([^\]|]+?)\s*(?:\|[^\]]*)?\]\]")


def extract_targets(meta, body):
    """Collect all link targets (frontmatter links, source_ids, inline)."""
    targets = []
    raw_links = meta.get("links")
    if isinstance(raw_links, list):
        for item in raw_links:
            m = WIKILINK_RE.search(str(item))
            if m:
                targets.append(m.group(1).strip())
            elif str(item).strip():
                targets.append(str(item).strip())
    raw_sources = meta.get("source_ids")
    if isinstance(raw_sources, list):
        for src in raw_sources:
            if str(src).strip():
                targets.append(str(src).strip())
    for m in WIKILINK_RE.finditer(body):
        targets.append(m.group(1).strip())
    return targets


def infer_type_from_folder(folder):
    mapping = {
        "sessions": "session",
        "zones": "zone",
        "decisions": "decision",
        "scars": "scar",
        "reflections": "reflection",
    }
    return mapping.get(folder, folder)


def collect_neurons(memory_dir, now):
    """Read every neuron and attach parsed fields plus temperature."""
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
            neuron_id = meta.get("id") or os.path.splitext(name)[0]
            ntype = meta.get("type") or infer_type_from_folder(folder)
            neurons.append({
                "id": str(neuron_id).strip(),
                "type": str(ntype).strip(),
                "importance": int(to_float(meta.get("importance"), 1.0)),
                "temperature": compute_temperature(meta, now),
                "created": parse_date(meta.get("created")),
                "last_accessed": parse_date(meta.get("last_accessed")),
                "expires_hint": parse_date(meta.get("expires_hint")),
                "targets": extract_targets(meta, body),
            })
    return neurons


def count_orphans(neurons):
    """Count neurons with no resolved links in or out."""
    id_set = set(n["id"] for n in neurons)
    degree = dict((n["id"], 0) for n in neurons)
    for neuron in neurons:
        source = neuron["id"]
        for target in neuron["targets"]:
            target = target.strip()
            if not target or target == source or target not in id_set:
                continue
            degree[source] = degree.get(source, 0) + 1
            degree[target] = degree.get(target, 0) + 1
    return sum(1 for n in neurons if degree.get(n["id"], 0) == 0)


def folder_size_kb(memory_dir):
    """Total size of every file under the memory dir, in KB."""
    total = 0
    for root, _dirs, files in os.walk(memory_dir):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                continue
    return total / 1024.0


def read_brain(memory_dir):
    """Return (line_count, last_dream_date) for BRAIN.md, tolerating absence."""
    brain_path = os.path.join(memory_dir, "BRAIN.md")
    if not os.path.isfile(brain_path):
        return 0, None
    try:
        with open(brain_path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError):
        return 0, None
    line_count = len(text.splitlines())
    last_dream = None
    match = re.search(r"Last dream:\s*(\d{4}-\d{2}-\d{2})", text)
    if match:
        last_dream = parse_date(match.group(1))
    return line_count, last_dream


def read_dream_trigger(memory_dir):
    """Read dream_trigger from config.md, defaulting to DEFAULT_DREAM_TRIGGER."""
    config_path = os.path.join(memory_dir, "config.md")
    if not os.path.isfile(config_path):
        return DEFAULT_DREAM_TRIGGER
    try:
        with open(config_path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError):
        return DEFAULT_DREAM_TRIGGER
    meta, _body = parse_frontmatter(text)
    return int(to_float(meta.get("dream_trigger"), DEFAULT_DREAM_TRIGGER))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Report lastmemory brain health.")
    parser.add_argument("memory_dir", help="Path to the /memory folder.")
    parser.add_argument("--now", default=None, help="Reference date YYYY-MM-DD for the clock.")
    args = parser.parse_args(argv)

    memory_dir = args.memory_dir
    if not os.path.isdir(memory_dir):
        print("Error: memory dir not found: %s" % memory_dir)
        return 1

    now = parse_date(args.now) or datetime.date.today()

    neurons = collect_neurons(memory_dir, now)

    by_type = {}
    hot = warm = cold = 0
    for neuron in neurons:
        by_type[neuron["type"]] = by_type.get(neuron["type"], 0) + 1
        temp = neuron["temperature"]
        if temp > HOT_THRESHOLD:
            hot += 1
        elif temp >= WARM_THRESHOLD:
            warm += 1
        else:
            cold += 1

    orphans = count_orphans(neurons)
    size_kb = folder_size_kb(memory_dir)
    brain_lines, last_dream = read_brain(memory_dir)
    dream_trigger = read_dream_trigger(memory_dir)

    # Accumulated importance of sessions created since the last dream. When no
    # last dream date is known, every session counts.
    accumulated = 0
    for neuron in neurons:
        if neuron["type"] != "session":
            continue
        created = neuron["created"] or neuron["last_accessed"]
        if last_dream is None or created is None or created > last_dream:
            accumulated += neuron["importance"]

    # Scars past their expiry hint.
    expired_scars = [
        n for n in neurons
        if n["type"] == "scar" and n["expires_hint"] is not None and n["expires_hint"] < now
    ]

    reasons = []
    if cold >= COLD_COUNT_TRIGGER:
        reasons.append("cold neurons %d >= %d" % (cold, COLD_COUNT_TRIGGER))
    if brain_lines > BRAIN_LINE_LIMIT:
        reasons.append("BRAIN.md %d lines > %d" % (brain_lines, BRAIN_LINE_LIMIT))
    if accumulated >= dream_trigger:
        reasons.append("accumulated importance %d >= %d" % (accumulated, dream_trigger))
    if expired_scars:
        reasons.append("%d scar(s) past expires_hint" % len(expired_scars))
    dream_recommended = bool(reasons)

    total = len(neurons)

    print("=" * 52)
    print("lastmemory brain health")
    print("=" * 52)
    print("Reference date: %s" % now.isoformat())
    print("")
    print("Total neurons: %d" % total)
    if by_type:
        for ntype in sorted(by_type):
            print("  %-12s %d" % (ntype, by_type[ntype]))
    else:
        print("  (no neurons found)")
    print("")
    print("Temperature (hot > %.2f, warm %.2f to %.2f, cold < %.2f):"
          % (HOT_THRESHOLD, WARM_THRESHOLD, HOT_THRESHOLD, WARM_THRESHOLD))
    print("  hot   %d" % hot)
    print("  warm  %d" % warm)
    print("  cold  %d" % cold)
    print("")
    print("Orphan neurons: %d" % orphans)
    print("Memory folder size: %.1f KB" % size_kb)
    print("BRAIN.md lines: %d (limit %d)" % (brain_lines, BRAIN_LINE_LIMIT))
    if last_dream is not None:
        print("Last dream: %s" % last_dream.isoformat())
    else:
        print("Last dream: unknown (not found in BRAIN.md)")
    print("Accumulated session importance since last dream: %d (trigger %d)"
          % (accumulated, dream_trigger))
    if expired_scars:
        print("Scars past expires_hint: %d" % len(expired_scars))
        for scar in expired_scars:
            print("  - %s (expired %s)" % (scar["id"], scar["expires_hint"].isoformat()))
    print("")
    print("Dream recommended: %s" % ("YES" if dream_recommended else "no"))
    if reasons:
        for reason in reasons:
            print("  - %s" % reason)
    print("=" * 52)
    return 0


if __name__ == "__main__":
    sys.exit(main())
