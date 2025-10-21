import requests
import feedparser

# fetch_articles retrieves recent RSS entries from Yahoo Finance for a given ticker
# and returns only those entries whose title or summary contains the provided keyword.
def fetch_articles(ticker, keyword):

    # Build the Yahoo Finance RSS URL for the specified ticker
    rss_url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
    
    # Requests RSS feed
    resp = requests.get(rss_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    resp.raise_for_status()
    
    # Parse the feed content into a feedparser object
    feed = feedparser.parse(resp.content)

    # Helper function that checks whether an entry's title or summary contains the keyword
    def contains_keyword(entry) -> bool:
        # Extract title and summary
        title = (entry.get("title") or "")
        summary = (entry.get("summary") or "")
        kw = keyword.lower()
        # Case-insensitive keyword check
        return kw in title.lower() or kw in summary.lower()

    articles = []
    # Iterate over the feed entries and collect ones matching the keyword
    for entry in feed.entries:
        if not contains_keyword(entry):
            continue
        # Normalize entries into a dict
        articles.append({
            "title": (entry.get("title") or "").strip(),
            "link": (entry.get("link") or "").strip(),
            "published": (entry.get("published") or "").strip(),
            "summary": (entry.get("summary") or "").strip(),
        })
    return articles