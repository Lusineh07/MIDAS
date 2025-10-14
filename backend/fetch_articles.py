import requests
import feedparser

def fetch_articles(ticker, keyword):
    rss_url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
    resp = requests.get(rss_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    resp.raise_for_status()
    feed = feedparser.parse(resp.content)

    def contains_keyword(entry) -> bool:
        title = (entry.get("title") or "")
        summary = (entry.get("summary") or "")
        kw = keyword.lower()
        return kw in title.lower() or kw in summary.lower()

    articles = []
    for entry in feed.entries:
        if not contains_keyword(entry):
            continue
        articles.append({
            "title": (entry.get("title") or "").strip(),
            "link": (entry.get("link") or "").strip(),
            "published": (entry.get("published") or "").strip(),
            "summary": (entry.get("summary") or "").strip(),
        })
    return articles