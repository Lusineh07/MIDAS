from fetch_articles import fetch_articles
from transformers import pipeline

def analyze_sentiment(articles):
  pipe = pipeline("text-classification", model="ProsusAI/finbert")

  results = []
  total_score = 0.0      # signed sum: positive adds, negative subtracts
  num_articles = 0

  for a in articles:
    summary = a.get("summary", "")
    sentiment = pipe(summary, truncation=True)[0]
    label = sentiment["label"].lower()
    score = float(sentiment["score"])
    signed_score = score if label == "positive" else (-score if label == "negative" else 0.0)

    results.append({**a, "sentiment_label": label, "sentiment_score": score, "signed": signed_score})
    total_score += signed_score

  num_articles = len(results)
  overall_score = total_score / num_articles

  if num_articles == 0:
    overall_sentiment = "Neutral"
  elif overall_score >= 0.15:
      overall_sentiment = "Positive"
  elif overall_score <= -0.15:
      overall_sentiment = "Negative"
  else:
      overall_sentiment = "Neutral"

  return {
    "overall_sentiment": overall_sentiment,
    "overall_score": overall_score,
    "num_articles": num_articles,
    "articles": results,
    }