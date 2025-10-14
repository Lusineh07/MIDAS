import requests
import feedparser
from transformers import pipeline

# Identifiable ticker symbol
ticker = "TSLA"

# Name of company to filter search
keyword = "Tesla"

# FinBERT for financial sentiment
pipe = pipeline("text-classification", model="ProsusAI/finbert")

rss_url = f"https://finance.yahoo.com/rss/headline?s={ticker}"

# Yahoo sometimes blocks default clients; set a UA and fetch manually
resp = requests.get(rss_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
resp.raise_for_status()
feed = feedparser.parse(resp.content)

total_score = 0.0      # signed sum: positive adds, negative subtracts
num_articles = 0

def contains_keyword(entry, kw: str) -> bool:
    title = entry.get("title", "") or ""
    summary = entry.get("summary", "") or ""
    return kw.lower() in title.lower() or kw.lower() in summary.lower()

for i, entry in enumerate(feed.entries):
    if not contains_keyword(entry, keyword):
        continue

    title = entry.get("title", "").strip()
    link = entry.get("link", "").strip()
    published = entry.get("published", "").strip()
    summary = entry.get("summary", "").strip()

    print(f"Title: {title}")
    print(f"Link: {link}")
    print(f"Published: {published}")
    print(f"Summary: {summary}")

    # Classify; truncate long texts to model limit
    sentiment = pipe(summary, truncation=True)[0]
    label = sentiment["label"].lower()
    score = float(sentiment["score"])

    print(f"Sentiment: {label.capitalize()}, Score: {score:.3f}")
    print("-" * 40)

    # Map to signed score: positive = +score, negative = -score, neutral = 0
    if label == "positive":
        total_score += score
        num_articles += 1
    elif label == "negative":
        total_score -= score
        num_articles += 1
    else:  # neutral
        num_articles += 1  # count it, but add 0

# Guard against no matching articles
if num_articles == 0:
    print("No articles matched your keyword filter.")
else:
    final_score = total_score / num_articles
    # Simple band for overall sentiment
    if final_score >= 0.15:
        overall = "Positive"
    elif final_score <= -0.15:
        overall = "Negative"
    else:
        overall = "Neutral"

    print(f"Overall Sentiment: {overall} ({final_score:.3f}) from {num_articles} articles")