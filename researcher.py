import urllib.request, urllib.parse, json, re, os, socket, time, datetime

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE   = os.path.join(SCRIPT_DIR, "data", "research_cache.json")
REPORTS_DIR  = os.path.join(SCRIPT_DIR, "data", "research_reports")
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(os.path.join(SCRIPT_DIR, "data"), exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def _fetch(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw     = r.read(500000)
            charset = r.headers.get_content_charset() or "utf-8"
            return raw.decode(charset, errors="ignore")
    except Exception:
        return None

def _strip_html(html):
    html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>",   " ", html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r"<[^>]+>", " ", html)
    html = re.sub(r"&nbsp;",  " ", html)
    html = re.sub(r"&amp;",   "&", html)
    html = re.sub(r"&lt;",    "<", html)
    html = re.sub(r"&gt;",    ">", html)
    html = re.sub(r"&quot;",  '"', html)
    html = re.sub(r"&#\d+;",  " ", html)
    html = re.sub(r"\s{3,}",  "\n", html)
    return html.strip()

def _load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_cache(cache):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass

def _cache_key(query):
    import hashlib
    return hashlib.md5(query.encode()).hexdigest()[:12]

# ── SEARCH ENGINES ──────────────────────────────────────────────────────────

def search_ddg(query, max_results=8):
    q   = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={q}"
    html = _fetch(url)
    if not html:
        return []
    results = []
    pattern = re.compile(
        r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
        r'class="result__snippet"[^>]*>(.*?)</(?:span|div)>',
        re.DOTALL
    )
    for m in pattern.finditer(html):
        href    = _strip_html(m.group(1)).strip()
        title   = _strip_html(m.group(2)).strip()
        snippet = _strip_html(m.group(3)).strip()
        if "duckduckgo.com" in href or not href.startswith("http"):
            continue
        results.append({"url": href, "title": title, "snippet": snippet, "source": "ddg"})
        if len(results) >= max_results:
            break
    return results

def search_wikipedia(query):
    q   = urllib.parse.quote_plus(query)
    url = f"https://en.wikipedia.org/w/api.php?action=search&list=search&srsearch={q}&format=json&srlimit=3"
    html = _fetch(url)
    if not html:
        return []
    try:
        data    = json.loads(html)
        results = []
        for item in data.get("query", {}).get("search", []):
            title   = item.get("title", "")
            snippet = re.sub(r"<[^>]+>", "", item.get("snippet", ""))
            page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ','_'))}"
            results.append({"url": page_url, "title": title, "snippet": snippet, "source": "wikipedia"})
        return results
    except Exception:
        return []

def fetch_wikipedia_summary(title):
    t   = urllib.parse.quote(title.replace(" ", "_"))
    url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles={t}&format=json"
    html = _fetch(url)
    if not html:
        return None
    try:
        data  = json.loads(html)
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            extract = page.get("extract", "")
            if extract:
                return extract[:5000]
    except Exception:
        pass
    return None

def fetch_page_content(url, max_chars=6000):
    html = _fetch(url, timeout=12)
    if not html:
        return None
    text  = _strip_html(html)
    lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 50]
    joined = "\n".join(lines)
    if len(joined) > max_chars:
        joined = joined[:max_chars] + "\n[...truncated]"
    return joined if joined.strip() else None

def fetch_arxiv(query, max_results=3):
    q   = urllib.parse.quote_plus(query)
    url = f"https://export.arxiv.org/api/query?search_query=all:{q}&start=0&max_results={max_results}"
    xml = _fetch(url)
    if not xml:
        return []
    results = []
    entries = re.findall(r"<entry>(.*?)</entry>", xml, re.DOTALL)
    for entry in entries:
        title   = re.search(r"<title>(.*?)</title>",     entry, re.DOTALL)
        summary = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
        link    = re.search(r'href="(https://arxiv[^"]+)"', entry)
        if title and summary:
            results.append({
                "url":     link.group(1) if link else "https://arxiv.org",
                "title":   title.group(1).strip().replace("\n", " "),
                "snippet": summary.group(1).strip()[:300].replace("\n", " "),
                "source":  "arxiv",
            })
    return results

def fetch_news(query):
    q   = urllib.parse.quote_plus(query + " news")
    url = f"https://news.google.com/rss/search?q={q}&hl=en"
    xml = _fetch(url)
    if not xml:
        return []
    results = []
    items   = re.findall(r"<item>(.*?)</item>", xml, re.DOTALL)
    for item in items[:5]:
        title = re.search(r"<title>(.*?)</title>", item)
        link  = re.search(r"<link/>(.*?)<",        item, re.DOTALL)
        if not link:
            link = re.search(r"<link>(.*?)</link>", item)
        desc  = re.search(r"<description>(.*?)</description>", item, re.DOTALL)
        if title:
            t = re.sub(r"<[^>]+>", "", title.group(1)).strip()
            l = link.group(1).strip() if link else ""
            d = re.sub(r"<[^>]+>", "", desc.group(1) if desc else "").strip()[:200]
            results.append({"url": l, "title": t, "snippet": d, "source": "news"})
    return results

# ── DEEP RESEARCH ENGINE ────────────────────────────────────────────────────

def deep_research(query, mode="standard", status_cb=None):
    """
    modes: standard | academic | news | comprehensive
    Returns a structured research package ready to send to AI for synthesis
    """
    cache     = _load_cache()
    cache_key = _cache_key(query + mode)
    if cache_key in cache:
        cached = cache[cache_key]
        age_hours = (time.time() - cached.get("timestamp", 0)) / 3600
        if age_hours < 6:
            if status_cb: status_cb("Using cached research (< 6h old)")
            return cached["data"]

    if status_cb: status_cb(f"Researching: {query}")

    all_sources  = []
    full_content = []

    # 1. Web search
    if status_cb: status_cb("Searching the web...")
    web_results = search_ddg(query, max_results=6)
    all_sources.extend(web_results)

    # 2. Wikipedia
    if status_cb: status_cb("Checking Wikipedia...")
    wiki_results = search_wikipedia(query)
    if wiki_results:
        for wr in wiki_results[:2]:
            title   = wr["title"]
            summary = fetch_wikipedia_summary(title)
            if summary:
                full_content.append({
                    "source": "Wikipedia",
                    "title":  title,
                    "url":    wr["url"],
                    "content": summary,
                })
                if status_cb: status_cb(f"Got Wikipedia: {title}")

    # 3. Academic papers (for academic/comprehensive mode)
    if mode in ("academic", "comprehensive"):
        if status_cb: status_cb("Searching academic papers (arXiv)...")
        arxiv_results = fetch_arxiv(query, max_results=3)
        for ar in arxiv_results:
            full_content.append({
                "source":  "arXiv",
                "title":   ar["title"],
                "url":     ar["url"],
                "content": ar["snippet"],
            })

    # 4. News (for news/comprehensive mode)
    if mode in ("news", "comprehensive"):
        if status_cb: status_cb("Fetching latest news...")
        news_results = fetch_news(query)
        all_sources.extend(news_results)

    # 5. Fetch full content from top web results
    if status_cb: status_cb("Reading top sources...")
    fetched = 0
    for result in web_results[:4]:
        if fetched >= 3:
            break
        url     = result.get("url", "")
        content = fetch_page_content(url, max_chars=4000)
        if content and len(content) > 200:
            full_content.append({
                "source":  result.get("title", url),
                "title":   result.get("title", ""),
                "url":     url,
                "content": content,
            })
            fetched += 1
            if status_cb: status_cb(f"Read: {result.get('title','')[:50]}")
        time.sleep(0.3)

    package = {
        "query":        query,
        "mode":         mode,
        "timestamp":    datetime.datetime.now().isoformat(),
        "source_count": len(all_sources) + len(full_content),
        "sources":      all_sources[:8],
        "full_content": full_content,
    }

    cache[cache_key] = {"timestamp": time.time(), "data": package}
    old_keys = sorted(cache.keys(), key=lambda k: cache[k].get("timestamp", 0))
    for k in old_keys[:-30]:
        del cache[k]
    _save_cache(cache)

    return package

def build_research_prompt(package):
    query   = package["query"]
    sources = package["full_content"]
    snippets = package["sources"]

    parts = [
        f"[DEEP RESEARCH TASK]\n"
        f"Query: {query}\n"
        f"Sources gathered: {package['source_count']}\n"
        f"Mode: {package['mode']}\n\n"
        f"INSTRUCTIONS:\n"
        f"- Synthesise ALL the source material below into a comprehensive, accurate answer\n"
        f"- Cite sources by name when making specific claims\n"
        f"- Highlight where sources agree and where they conflict\n"
        f"- Give your own synthesis and conclusion at the end\n"
        f"- Structure clearly: Overview → Key Findings → Details → Conclusion\n"
        f"- Be specific with numbers, dates, names — no vague generalisations\n"
        f"- If sources are insufficient, say so clearly\n\n"
        f"SOURCE MATERIAL:\n"
        f"{'='*50}\n"
    ]

    for i, src in enumerate(sources, 1):
        parts.append(f"\n[SOURCE {i}: {src['source']} — {src['title'][:60]}]")
        parts.append(f"URL: {src['url']}")
        content = src["content"]
        if len(content) > 3000:
            content = content[:3000] + "..."
        parts.append(content)
        parts.append("---")

    if snippets:
        parts.append("\nADDITIONAL SEARCH RESULTS (snippets):")
        for s in snippets[:5]:
            parts.append(f"• {s['title']}: {s['snippet'][:150]}")

    return "\n".join(parts)

def save_report(query, report_text):
    safe = re.sub(r'[^\w\s-]', '', query)[:40].strip().replace(' ', '_')
    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    path = os.path.join(REPORTS_DIR, f"{ts}_{safe}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Research Report: {query}\n")
        f.write(f"Generated: {datetime.datetime.now().strftime('%d %b %Y %H:%M')}\n")
        f.write("=" * 60 + "\n\n")
        f.write(report_text)
    return path

def list_reports():
    files = sorted(os.listdir(REPORTS_DIR), reverse=True)
    if not files:
        return "No research reports saved yet."
    lines = ["Saved research reports:"]
    for f in files[:10]:
        path = os.path.join(REPORTS_DIR, f)
        size = os.path.getsize(path) // 1024
        lines.append(f"  {f} ({size}KB)")
    return "\n".join(lines)

def is_research_request(text):
    keywords = [
        "research", "deep dive", "comprehensive", "in depth", "investigate",
        "find everything", "tell me everything", "full report", "detailed report",
        "what is the latest", "current state of", "overview of", "explain everything",
        "all about", "give me a report", "study on", "analysis of",
    ]
    return any(k in text.lower() for k in keywords)

def detect_research_mode(text):
    tl = text.lower()
    if any(w in tl for w in ["paper", "academic", "scientific", "study", "journal", "arxiv", "research paper"]):
        return "academic"
    if any(w in tl for w in ["news", "latest", "recent", "today", "current", "breaking"]):
        return "news"
    if any(w in tl for w in ["everything", "comprehensive", "complete", "full", "all about", "in depth"]):
        return "comprehensive"
    return "standard"
