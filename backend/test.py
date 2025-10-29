from fetch_articles import fetch_articles
from sentiment_analysis import analyze_sentiment
from summarize_text import summarize_text

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

# Prints formatted string input for AI model summary
print('\n--- FORMATTED STRING ---')
formatted_string = articles[0]['title'] + " : " + articles[0]['summary']
print(formatted_string)

# Prints summary of formatted article string
print('\n--- SUMMARY ---')
summary = summarize_text(formatted_string, keyword)
print(summary)