from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from requests.exceptions import Timeout, ConnectionError
from json.decoder import JSONDecodeError
import requests

app = Flask(__name__)

# Function to get search results count
def get_search_results_count(keyword):
    url = f"https://www.bing.com/search?q={keyword}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        count_element = soup.find("span", class_="sb_count")
        if count_element:
            count_text = count_element.text
            count = ''.join(filter(str.isdigit, count_text))
            return int(count)
        else:
            return None
    except Exception as e:
        if isinstance(e, ConnectionError) and 'IncompleteRead' in str(e):
            return None
        return None  # Don't print error messages in the result

# Function to fetch suggestions with retry logic and timeout
def fetch_suggestions_with_retry(url: str) -> list:
    retries = 5  # Increased number of retries
    timeout = 30  # Increased timeout value to 30 seconds
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                try:
                    suggestions = response.json()[1]
                    return suggestions
                except JSONDecodeError as e:
                    pass  # Don't print JSON decode errors
            else:
                pass  # Don't print failed to fetch suggestions errors
        except Timeout as e:
            if attempt < retries - 1:
                continue
            else:
                pass  # Don't print timeout warnings
        except ConnectionError as e:
            pass  # Don't print connection errors
    return []  # Return empty list if maximum retries exceeded or error occurred

# Function to fetch suggestions from Google
def fetch_suggestions_google(keyword: str) -> list:
    url = f"http://suggestqueries.google.com/complete/search?client=firefox&q={keyword}"
    return fetch_suggestions_with_retry(url)

# Function to fetch suggestions from YouTube
def fetch_suggestions_youtube(keyword: str) -> list:
    url = f"http://suggestqueries.google.com/complete/search?client=youtube&ds=yt&q={keyword}"
    return fetch_suggestions_with_retry(url)

# Generating keyword suggestions
def generate_keywords(base_keyword: str, categories: dict) -> list:
    keywords = []
    for category, values in categories.items():
        for value in values:
            keyword = f"{base_keyword} {value}"
            if category == "YouTube":
                suggestions = fetch_suggestions_youtube(keyword)
            else:
                suggestions = fetch_suggestions_google(keyword)
            keywords.extend(suggestions)
    return keywords

# Main route
@app.route('/api/keywords', methods=['GET'])
def get_keywords():
    base_keyword = request.args.get('keyword')
    if not base_keyword:
        return jsonify({"error": "Keyword parameter is missing"}), 400

    categories = {
"Questions": ["who", "what", "where", "when", "why", "how", "are", "which"],
                "Prepositions": ["can", "with", "for", "of", "in", "on", "to", "from"],
                "Alphabet": list("abcdefghijklmnopqrstuvwxyz"),
                "Numbers": list("012345678910"),
                "Comparisons": ["vs", "versus", "or", "than", "as"],
                "Intent-Based": ["buy", "review", "price", "best", "top", "how to", "why to", "what is", "interested"],
                "Time-Related": ["when", "schedule", "deadline", "today", "now", "latest", "duration", "date", "time"],
                "Audience-Specific": ["for beginners", "for students", "for kids", "for seniors", "for professionals", "for business"],
                "Problem-Solving": ["solution", "issue", "error", "troubleshoot", "fix", "help", "repair", "resolve"],
                "Feature-Specific": ["with video", "with images", "analytics", "tools", "functions", "capabilities", "specs"],
                "Opinions/Reviews": ["review", "opinion", "rating", "feedback", "recommendation", "impression"],
                "Cost-Related": ["price", "cost", "budget", "cheap", "expensive", "value", "discount", "payment", "subscribe"],
                "Trend-Based": ["trends", "new", "upcoming", "popular", "latest", "hottest"],
                "Confirmation": ["yes", "no", "confirm", "agree", "okay"],
                "Availability": ["in stock", "out of stock", "delivery", "inventory", "backorder", "shipping"],
                "Statistics": ["numbers", "data", "metrics", "results", "analytics", "stats"],
                "Permissions": ["allow", "deny", "restrict", "permissions", "access", "authorization"],
                "Notifications": ["notify", "alert", "message", "update", "notifications", "notify me"],
                "Locations": ["address", "store", "location", "map", "store hours", "near me"],
                "Professional": ["business", "enterprise", "corporate", "industry", "company"],
                "Search": ["find", "lookup", "search", "keyword"],
                "FAQ": ["question", "answer", "frequently asked questions", "help topics"],
                "Support": ["help", "assistance", "contact", "customer service"],
                "YouTube": ["tutorial", "how to", "guide", "review", "demo","tips","5 tips","tricks","easy way", "stop using","stop","method", "tips and tricks","the best","dumb things ","this","this habit ","i stopped","alternative","the most"],
                "Social Media": ["Facebook", "Twitter", "Instagram", "LinkedIn", "Pinterest", "YouTube"],
                "Security": ["security", "privacy", "encryption", "authentication", "secure"],
                "Education": ["learn", "education", "tutorial", "course", "training", "guide"],
                "Health/Wellness": ["health", "wellness", "fitness", "nutrition", "diet", "exercise"],
                "Entertainment": ["movies", "music", "books", "games", "TV shows", "celebrities"],
                "Technology": ["technology", "gadgets", "devices", "software", "hardware", "IT"],
                "Travel": ["travel", "vacation", "destination", "hotel", "flight", "tourist attractions"],
                "Food": ["food", "recipes", "restaurants", "cooking", "cuisine", "healthy eating"],
                "Fashion": ["fashion", "clothing", "style", "accessories", "trends", "outfits"],
                "Sports": ["sports", "football", "basketball", "soccer", "tennis", "golf"],    }

    easy_keywords = []
    keywords = generate_keywords(base_keyword, categories)
    for keyword in keywords:
        result_count = get_search_results_count(keyword)
        if result_count is not None and result_count <= 650000 and not keyword[0].isdigit():
            easy_keywords.append(keyword)

    return jsonify({"keywords": easy_keywords})

if __name__ == "__main__":
    app.run(debug=True)
