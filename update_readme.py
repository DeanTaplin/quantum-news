import os
import json
import requests
from datetime import datetime # timedelta might not be needed anymore

# Define the history directory
NEWS_HISTORY_DIR = "news_history"

def search_brave(query, count=30, freshness_code=None, country='us', search_lang='en'):
    api_key = os.environ.get('BRAVE_API_KEY')
    if not api_key:
        print("Error: BRAVE_API_KEY environment variable not set.")
        raise ValueError("BRAVE_API_KEY environment variable not set.")
    
    headers = {
        'X-Subscription-Token': api_key,
        'Accept': 'application/json'
    }
    # Use the NEWS endpoint
    url = 'https://api.search.brave.com/res/v1/news/search' 
    
    params = {
        'q': query,
        'count': count,
        'country': country,
        'search_lang': search_lang,
        'spellcheck': 'true' # Enable spellcheck as per example
    }
    if freshness_code:
        params['freshness'] = freshness_code
    
    print(f"Searching Brave NEWS API with query: '{query}' and params: {params}")
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during Brave API request: {e}")
        # Return a structure that mimics a valid empty response for news
        return {"results": []} # News API might return 'results' at top level

def generate_readme_content(data_saved_to_history, news_period_label=""): 
    # The API response for news might be a direct list of results, or nested.
    # Based on Brave's general structure, 'results' is often a top-level key for news.
    # If it's nested under 'web', this needs adjustment. Assuming 'results' is top-level for news endpoint.
    api_response_data = data_saved_to_history.get('api_response', {})
    # Let's check common structures for results from news endpoint:
    # Option 1: results is a top-level key in api_response_data
    # Option 2: results is under a 'web' or 'news' key (less likely for specific news endpoint)
    results = api_response_data.get('results', []) # Primary assumption for news endpoint
    if not results and 'web' in api_response_data: # Fallback check if it's like web search
        results = api_response_data.get('web', {}).get('results', [])


    query_details = data_saved_to_history.get('query_details', {})
    
    content_parts = []
    content_parts.append("# Quantum Computing News Tracker\n\n")
    content_parts.append("A curated collection of the latest developments, breakthroughs, and news in the field of Quantum Computing.\n\n")
    
    header_text = news_period_label if news_period_label else datetime.now().strftime("%B %d, %Y")
    content_parts.append(f"## Latest Updates ({header_text})\n\n")
    
    if not results:
        search_type = query_details.get("search_type", "weekly_freshness") # Updated search_type name
        if search_type == "monthly_freshness_fallback":
            content_parts.append("No new relevant articles found for the past 7 days. Displaying notable articles from the past month.\n")
            if not results: # Check if fallback also yielded nothing
                 content_parts.append("No notable articles found for the past month either.\n")
        else: 
            content_parts.append(f"No new relevant articles found for the {news_period_label.lower()}.\n")
    else: 
        search_type = query_details.get("search_type", "weekly_freshness")
        if search_type == "monthly_freshness_fallback":
             content_parts.append("No new relevant articles found for the past 7 days. Displaying notable articles from the past month:\n\n")

    model_releases = []
    innovations = []
    market_trends = []
    
    for item in results: 
        # Adjust keys based on actual News API response structure for title, description, url
        title = item.get('title', item.get('name', 'N/A')) # 'name' is sometimes used
        description = item.get('description', item.get('snippet', 'No description available.')) # 'snippet' is common
        url = item.get('url', item.get('webSearchUrl', '#')) # 'webSearchUrl' or similar

        content_text = f"{title} {description}".lower()
        news_item = f"- **{title}**\n  - {description}\n  - [Source]({url})\n"
        
        # Keyword categorization remains the same
        if any(keyword in content_text for keyword in ['release', 'launch', 'version', 'model', 'gpt', 'claude', 'gemini']):
            model_releases.append(news_item)
        elif any(keyword in content_text for keyword in ['breakthrough', 'innovation', 'research', 'discover']):
            innovations.append(news_item)
        elif any(keyword in content_text for keyword in ['market', 'growth', 'trend', 'industry', 'adoption']):
            market_trends.append(news_item)

    if model_releases:
        content_parts.append("\n### Major Model Releases & Improvements\n\n")
        content_parts.append("\n".join(model_releases[:5]))
    
    if innovations:
        content_parts.append("\n### Notable Innovations\n\n")
        content_parts.append("\n".join(innovations[:5]))
    
    if market_trends:
        content_parts.append("\n### Market Trends\n\n")
        content_parts.append("\n".join(market_trends[:5]))
    
    if results and (model_releases or innovations or market_trends):
        content_parts.append("\n")

    # Ensure the full static part is present in the actual script:
    full_static_readme_part = r'''
## News Archive

Past weekly news updates can be found in the [`news_history`](./news_history/) directory. Files are named with the start date of the week they cover (e.g., `YYYY-MM-DD_quantum_news.json`).

## Contributing

To contribute to this news tracker:
1. Fork the repository
2. Add your news item in the appropriate section
3. Include:
   - Clear, concise summary
   - Date of announcement/development
   - Reliable source link
   - Any relevant technical details
4. Submit a pull request

## News Categories

- Model Releases
- Research Breakthroughs
- Industry Applications
- Market Developments
- Technical Innovations
- Policy & Regulation
- Open Source Developments

## Update Schedule

This repository is updated weekly with the latest developments in the Quantum Computing space. Each update includes verification from multiple sources when available.

## Disclaimer

The information provided in this repository is compiled from various sources and may not be comprehensive. Always refer to the original sources for complete details and verify information independently.

## License

This repository is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
'''
    content_parts.append(full_static_readme_part)
    return "".join(content_parts)


def main():
    print(f"Script started at {datetime.now().isoformat()}")
    search_type = "weekly_freshness" 
    news_period_label_for_readme = "Past 7 Days" # Default label
    current_query = "" # Variable to store the query used for data_to_save
    freshness_applied = 'none' # Variable to store freshness for data_to_save

    if not os.path.exists(NEWS_HISTORY_DIR):
        try:
            os.makedirs(NEWS_HISTORY_DIR)
            print(f"Created directory: {NEWS_HISTORY_DIR}")
        except OSError as e:
            print(f"Error creating directory {NEWS_HISTORY_DIR}: {e}")
            return

    # Primary search: Previous Week using freshness
    current_query = '"Quantum Computing" AND "AI"' # Stricter query for weekly
    freshness_applied = 'pw'
    print(f"Attempting primary search (News API, freshness '{freshness_applied}'): {current_query}")
    raw_api_response = search_brave(current_query, freshness_code=freshness_applied, country='us', search_lang='en')
    
    current_results = raw_api_response.get('results', [])
    if not current_results and 'web' in raw_api_response: 
         current_results = raw_api_response.get('web', {}).get('results', [])

    if not current_results:
        print("No results found for the past 7 days. Attempting fallback to past month.")
        search_type = "monthly_freshness_fallback"
        news_period_label_for_readme = "Past Month"
        
        current_query = '"Quantum Computing"' # Broader query for monthly
        freshness_applied = 'pm'
        print(f"Attempting fallback search (News API, freshness '{freshness_applied}' with broader query): {current_query}")
        raw_api_response = search_brave(current_query, freshness_code=freshness_applied, country='us', search_lang='en')
        current_results = raw_api_response.get('results', [])
        if not current_results and 'web' in raw_api_response:
             current_results = raw_api_response.get('web', {}).get('results', [])

    history_file_run_date_prefix = datetime.now().strftime("%Y-%m-%d")

    data_to_save = {
        "query_details": {
            "query_sent": current_query, 
            "freshness_used": freshness_applied, 
            "country_used": 'us', # Hardcoded for now
            "search_lang_used": 'en', # Hardcoded for now
            "search_type": search_type,
            "retrieval_timestamp": datetime.now().isoformat()
        },
        "api_response": raw_api_response 
    }

    history_filename = os.path.join(NEWS_HISTORY_DIR, f"{history_file_run_date_prefix}_quantum_news.json")
    
    try:
        with open(history_filename, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=4)
        print(f"News data saved to {history_filename}")
    except IOError as e:
        print(f"Error saving news data to {history_filename}: {e}")

    new_readme_content = generate_readme_content(data_to_save, news_period_label_for_readme) 
    
    try:
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(new_readme_content)
        print("README.md updated successfully.")
    except IOError as e:
        print(f"Error writing README.md: {e}")

    print(f"Script finished at {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()
