import urllib.request, urllib.parse, json, re, os, socket, time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def _fetch(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw     = r.read(300000)
            charset = r.headers.get_content_charset() or "utf-8"
            return raw.decode(charset, errors="ignore")
    except Exception:
        return None

def _strip_html(html):
    if not html:
        return ""
    html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>",   " ", html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r"<[^>]+>", " ", html)
    for entity, char in [("&nbsp;"," "),("&amp;","&"),("&lt;","<"),
                          ("&gt;",">"),("&quot;",'"'),("&#39;","'")]:
        html = html.replace(entity, char)
    html = re.sub(r"\s{3,}", "\n", html)
    return html.strip()

def search_ddg(query, max_results=6):
    q   = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={q}&kl=us-en"
    html = _fetch(url)
    if not html:
        return []
    results = []
    chunks = re.split(r'class="result[^"]*"', html)
    for chunk in chunks[1:]:
        title_m   = re.search(r'class="result__a"[^>]*>(.*?)</a>', chunk, re.DOTALL)
        snippet_m = re.search(r'class="result__snippet"[^>]*>(.*?)</(?:span|div|a)>', chunk, re.DOTALL)
        url_m     = re.search(r'href="//duckduckgo\.com/l/\?uddg=([^"&]+)', chunk)
        if not url_m:
            url_m = re.search(r'href="(https?://[^"]+)"', chunk)
        if title_m and snippet_m:
            title   = _strip_html(title_m.group(1)).strip()
            snippet = _strip_html(snippet_m.group(1)).strip()
            link    = urllib.parse.unquote(url_m.group(1)).strip() if url_m else ""
            if link and "duckduckgo.com" not in link and title:
                results.append({"url": link, "title": title, "snippet": snippet})
        if len(results) >= max_results:
            break
    return results

def search_wikipedia(query):
    q   = urllib.parse.quote_plus(query)
    url = f"https://en.wikipedia.org/w/api.php?action=search&list=search&srsearch={q}&format=json&srlimit=2"
    html = _fetch(url)
    if not html:
        return []
    try:
        data = json.loads(html)
        results = []
        for item in data.get("query", {}).get("search", []):
            title   = item.get("title","")
            snippet = re.sub(r"<[^>]+>", "", item.get("snippet",""))
            page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ','_'))}"
            results.append({"url": page_url, "title": title, "snippet": snippet, "source": "Wikipedia"})
        return results
    except Exception:
        return []

def fetch_wikipedia_summary(title):
    t   = urllib.parse.quote(title.replace(" ", "_"))
    url = (f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts"
           f"&exintro&explaintext&titles={t}&format=json&exsentences=10")
    html = _fetch(url)
    if not html:
        return None
    try:
        data  = json.loads(html)
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            extract = page.get("extract", "")
            if extract:
                return extract[:3000]
    except Exception:
        pass
    return None

def fetch_page_content(url, max_chars=5000):
    html = _fetch(url, timeout=10)
    if not html:
        return None
    text  = _strip_html(html)
    lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 40]
    joined = "\n".join(lines[:100])
    if len(joined) > max_chars:
        joined = joined[:max_chars] + "\n[truncated]"
    return joined if len(joined) > 100 else None

def search_and_summarise(query, max_results=5):
    results = []
    web = search_ddg(query, max_results=max_results)
    results.extend(web)
    wiki = search_wikipedia(query)
    for wr in wiki:
        summary = fetch_wikipedia_summary(wr["title"])
        if summary:
            wr["snippet"] = summary[:400]
        results.append(wr)
    if not results:
        return None
    lines = [f"Web search results for: {query}\n"]
    for i, r in enumerate(results[:6], 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   {r.get('snippet','')[:200]}")
        if r.get("url"):
            lines.append(f"   Source: {r['url']}")
        lines.append("")
    return "\n".join(lines)

def fetch_and_read(url, max_chars=5000):
    wiki_match = re.search(r"wikipedia\.org/wiki/(.+)", url)
    if wiki_match:
        title   = urllib.parse.unquote(wiki_match.group(1).replace("_", " "))
        summary = fetch_wikipedia_summary(title)
        if summary:
            return summary
    return fetch_page_content(url, max_chars=max_chars)

def is_search_request(text):
    keywords = [
        "what is","what are","who is","who are","when did","when is",
        "where is","how does","how do","why does","why is",
        "latest","current","recent","today","news","price","score",
        "population","capital","best","top","list of","examples of",
        "define","meaning of","tell me about","explain","search",
        "look up","find out","how many","how much",
    ]
    tl = text.lower()
    return any(k in tl for k in keywords)

def is_url(text):
    return bool(re.search(r'https?://[^\s]+', text))

def extract_url(text):
    m = re.search(r'https?://[^\s]+', text)
    return m.group(0) if m else None

def has_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False
