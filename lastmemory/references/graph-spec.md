# graph-spec: the offline memory graph

Load this for `/lastmemory view`. The output is `memory/graph.html`, a single self contained HTML file with zero network dependencies. It must work opened directly from disk, offline, with no CDN, no external fonts, and no remote images.

## Pipeline

`scripts/generate_graph.py memory` does the work:

1. Walk every neuron under `memory/` (sessions, zones, decisions, scars, reflections).
2. Parse frontmatter: id, type, summary, status, importance, strength, last_accessed, created, links, source_ids.
3. Parse inline typed wikilinks in the body: `- verb [[target-id]]` and bare `[[target-id]]`.
4. Compute temperature per node with the scoring formula (weeks since last_accessed over strength).
5. Build nodes and edges, mark orphans (degree 0), count dangling links (targets that do not resolve).
6. Read `assets/graph-template.html`, replace the token `/*__GRAPH_DATA__*/` with a JSON literal, write `memory/graph.html`.

## Node and edge data

Node: `{id, type, summary, zone, tags, text, importance, temperature, status, degree, orphan}`.
Edge: `{source, target, relation}`.

`text` is the flattened body of the neuron (headings and list markers stripped, whitespace collapsed, capped so the file stays small). It is what the in graph search reads, so the graph can answer "where is this documented" without any model or network call.

## Logic search (no model, no network)

The graph ships a deterministic keyword finder in the corner. It tokenizes the query, scores every node by matches across its id, type, zone, tags, and summary (weighted high) plus its body text (weighted low), boosts nodes that contain all tokens, and lists the top hits. Each hit shows a snippet taken from a window around the first match, so the result reads like a pointer into the project document. Clicking a hit centers the camera on that node and opens its panel. This is the searchable index of the repo, computed entirely client side.

## Clickable relations

The node panel lists the real synapses of the selected node in two groups, "Links out" (its outgoing typed links) and "Linked from" (neurons that point at it), each showing the relation verb and the target id. Clicking any relation navigates to that neuron. This turns the panel into a way to walk the network by hand, the same synapses the agent follows.

## Visual contract

- Dark theme, clean and modern. This HTML is the README screenshot, so it must look good.
- Nodes colored by type: session, zone, decision, scar, reflection. Small legend.
- Node radius scales with degree or importance.
- Node brightness scales with temperature: hot bright, cold dim.
- superseded or deprecated nodes are muted gray.
- Orphan nodes get a dashed outline, a visual flag for disconnected memory or an undocumented zone.
- Edges are thin lines; relation can tint the color or show on hover.
- Interaction: drag nodes, wheel to zoom, drag background to pan, click a node to open a side panel with its id, type, and summary.
- If there are no nodes, show a friendly centered message.

## Why we ship our own renderer

The template embeds a small vanilla JavaScript force simulation on a canvas, with no library. This satisfies the offline requirement more strictly than vendoring a third party build, and keeps the whole thing in one file. If you ever want a heavier renderer, vasturiano force-graph can be vendored into `assets/` and inlined, but do not reference any CDN.
