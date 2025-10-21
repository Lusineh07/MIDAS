from fetch_articles import fetch_articles
from transformers import pipeline

def analyze_sentiment(articles):
  # Initialize a Hugging Face transformers pipeline for text classification
  pipe = pipeline("text-classification", model="ProsusAI/finbert")

  results = []
  total_score = 0.0
  num_articles = 0
  overall_score = 0


  # Process each article, classify its summary and accumulate scores
  for a in articles:
    # Get summary text
    summary = a.get("summary", "")
    # Run the model pipeline; truncation=True ensures long texts are handled
    sentiment = pipe(summary, truncation=True)[0]
    label = sentiment["label"].lower()
    score = float(sentiment["score"])
    # Create a signed score: positive -> +score, negative -> -score, neutral -> 0.0
    signed_score = score if label == "positive" else (-score if label == "negative" else 0.0)

    # Append augmented article dict with sentiment metadata
    results.append({**a, "sentiment_label": label, "sentiment_score": score, "signed": signed_score})
    total_score += signed_score

  # Number of processed articles
  num_articles = len(results)

  # computes overall_score for sentiment
  if num_articles > 0:
    overall_score = total_score / num_articles

  # Map average signed score to an overall sentiment label using thresholds
  if num_articles == 0:
    overall_sentiment = "Neutral"
  elif overall_score >= 0.15:
      overall_sentiment = "Positive"
  elif overall_score <= -0.15:
      overall_sentiment = "Negative"
  else:
      overall_sentiment = "Neutral"

  # Return the aggregated sentiment information and the per-article results
  return {
    "overall_sentiment": overall_sentiment,
    "overall_score": overall_score,
    "num_articles": num_articles,
    "articles": results,
    }