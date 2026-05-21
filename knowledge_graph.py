import os, json, re, datetime, collections

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GRAPH_FILE = os.path.join(SCRIPT_DIR, "data", "knowledge_graph.json")
os.makedirs(os.path.join(SCRIPT_DIR, "data"), exist_ok=True)

STOP_WORDS = {"i","a","an","the","is","are","was","were","be","been","have","has",
              "do","does","did","will","would","could","should","may","might","can",
              "to","of","in","on","at","by","for","with","about","and","or","but",
              "if","then","my","your","it","this","that","what","how","when","where",
              "who","why","me","you","we","they","he","she","just","also","so","very",
              "really","quite","more","some","any","all","one","two","three","aria"}

def _load():
    if os.path.exists(GRAPH_FILE):
        try:
            with open(GRAPH_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"nodes": {}, "edges": [], "sources": []}

def _save(graph):
    with open(GRAPH_FILE, "w") as f:
        json.dump(graph, f, indent=2)

def _extract_concepts(text):
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = text.split()
    concepts = [w for w in words if len(w) > 3 and w not in STOP_WORDS]
    bigrams  = [f"{concepts[i]} {concepts[i+1]}" for i in range(len(concepts)-1)]
    return list(dict.fromkeys(concepts[:15] + bigrams[:5]))

def add_knowledge(text, source="conversation", tags=None):
    graph = _load()
    concepts = _extract_concepts(text)
    now = datetime.datetime.now().isoformat()
    for concept in concepts:
        if concept not in graph["nodes"]:
            graph["nodes"][concept] = {
                "count":   0,
                "sources": [],
                "tags":    tags or [],
                "first":   now,
                "last":    now,
            }
        graph["nodes"][concept]["count"] += 1
        graph["nodes"][concept]["last"]   = now
        if source not in graph["nodes"][concept]["sources"]:
            graph["nodes"][concept]["sources"].append(source)
    for i in range(len(concepts)):
        for j in range(i+1, min(i+4, len(concepts))):
            edge = {"a": concepts[i], "b": concepts[j], "source": source, "time": now}
            existing = [e for e in graph["edges"]
                        if (e["a"]==concepts[i] and e["b"]==concepts[j]) or
                           (e["a"]==concepts[j] and e["b"]==concepts[i])]
            if not existing:
                graph["edges"].append(edge)
    if source not in graph["sources"]:
        graph["sources"].append(source)
    graph["edges"] = graph["edges"][-5000:]
    _save(graph)
    return len(concepts)

def search_knowledge(query, top_n=8):
    graph = _load()
    query_concepts = _extract_concepts(query)
    if not query_concepts or not graph["nodes"]:
        return [], []
    matched_nodes = []
    for qc in query_concepts:
        for node, data in graph["nodes"].items():
            if qc in node or node in qc:
                matched_nodes.append((node, data["count"]))
    matched_nodes.sort(key=lambda x: -x[1])
    matched_nodes = list(dict.fromkeys(n for n, _ in matched_nodes))[:top_n]
    connected = []
    for node in matched_nodes:
        for edge in graph["edges"]:
            if edge["a"] == node:
                connected.append(edge["b"])
            elif edge["b"] == node:
                connected.append(edge["a"])
    connected = [c for c in connected if c not in matched_nodes]
    connected_counts = collections.Counter(connected)
    top_connected = [n for n, _ in connected_counts.most_common(5)]
    return matched_nodes, top_connected

def find_connections(topic_a, topic_b):
    graph = _load()
    concepts_a = _extract_concepts(topic_a)
    concepts_b = _extract_concepts(topic_b)
    connections = []
    for ca in concepts_a:
        for cb in concepts_b:
            for edge in graph["edges"]:
                if (ca in edge["a"] or edge["a"] in ca) and (cb in edge["b"] or edge["b"] in cb):
                    connections.append((edge["a"], edge["b"], edge.get("source", "?")))
                elif (cb in edge["a"] or edge["a"] in cb) and (ca in edge["b"] or edge["b"] in ca):
                    connections.append((edge["b"], edge["a"], edge.get("source", "?")))
    if not connections:
        bridge_nodes = []
        for ca in concepts_a:
            for edge in graph["edges"]:
                if ca in edge["a"] or edge["a"] in ca:
                    bridge_nodes.append(edge["b"])
                elif ca in edge["b"] or edge["b"] in ca:
                    bridge_nodes.append(edge["a"])
        for cb in concepts_b:
            for edge in graph["edges"]:
                if cb in edge["a"] or edge["a"] in cb:
                    if edge["b"] in bridge_nodes:
                        connections.append((ca, edge["b"], "indirect"))
                elif cb in edge["b"] or edge["b"] in cb:
                    if edge["a"] in bridge_nodes:
                        connections.append((ca, edge["a"], "indirect"))
    return connections[:10]

def get_knowledge_context(query):
    matched, connected = search_knowledge(query)
    if not matched:
        return ""
    parts = ["\n[YOUR KNOWLEDGE GRAPH — relevant concepts you've discussed before]:"]
    parts.append(f"Related concepts: {', '.join(matched[:6])}")
    if connected:
        parts.append(f"Connected to: {', '.join(connected[:4])}")
    return "\n".join(parts)

def format_connections(topic_a, topic_b, connections):
    if not connections:
        return f"No direct connections found between '{topic_a}' and '{topic_b}' in your knowledge yet. Discuss both more and connections will appear."
    lines = [f"Connections between {topic_a} and {topic_b}:"]
    for a, b, source in connections[:5]:
        lines.append(f"  {a} ↔ {b}  (from: {source})")
    return "\n".join(lines)

def get_stats():
    graph = _load()
    nodes = len(graph["nodes"])
    edges = len(graph["edges"])
    sources = len(graph["sources"])
    if nodes == 0:
        return "Knowledge graph: empty. Start talking and it builds automatically."
    top = sorted(graph["nodes"].items(), key=lambda x: -x[1]["count"])[:5]
    top_str = ", ".join(f"{n}({d['count']})" for n, d in top)
    return f"Knowledge graph: {nodes} concepts, {edges} connections, {sources} sources\nTop concepts: {top_str}"
