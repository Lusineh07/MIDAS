from fetch_articles import fetch_articles
from sentiment_analysis import analyze_sentiment
from summarize_articles import summarize_articles

# Test ticker and keyword for fetching articles
ticker = "TSLA"
keyword = "Tesla"

# Returned Articles
articles = fetch_articles(ticker, keyword)

# Gets sentiments and adds them to article data
article_data = analyze_sentiment(articles)

# Prints sentiment results
print('--- SENTIMENTS ---')
for article in article_data['articles']:
  print(article['title'] + ' : ' + str(article['signed']))

# Prints formatted string input for summary
print('\n--- FORMATTED ARTICLE STRING ---')
formatted_article_string = ''
for article in articles:
  formatted_article_string += (article['title'] + ' : ' + article['summary'])
print(formatted_article_string)

# Prints summary of formatted article string
print('\n--- SUMMARY ---')
summary = summarize_articles(formatted_article_string)
print(summary)