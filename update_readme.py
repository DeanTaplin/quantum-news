import os
import json
import requests
from datetime import datetime, timedelta

# Define the history directory
NEWS_HISTORY_DIR = "news_history"

def search_brave(query, count=30):
    api_key = os.environ.get('BRAVE_API_KEY')
    if not api_key:
        print("Error: BRAVE_API_KEY environment variable not set.")
        raise ValueError("BRAVE_API_KEY environment variable not set.")
    
    headers = {
        'X-Subscription-Token': api_key,
        'Accept': 'application/json'
    }
    url = 'https://api.search.brave.com/res/v1/web/search'
    params = {'q': query, 'count': count}
    
    print(f"Searching Brave with query: '{query}' and params: {params}")
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during Brave API request: {e}")
        return {"web": {"results": []}}

def generate_readme_content(news_data_from_history_file):
    current_date_in_header = datetime.now().strftime("%B %d, %Y")
    
    api_response_data = news_data_from_history_file.get('api_response', {})
    results = api_response_data.get('web', {}).get('results', [])
    
    content_parts = []
    content_parts.append(f"# Quantum Computing News Tracker\n\n")
    content_parts.append("A curated collection of the latest developments, breakthroughs, and news in the field of Quantum Computing.\n\n")
    content_parts.append(f"## Latest Updates ({current_date_in_header})\n\n")
    
    if not results:
        content_parts.append("No new relevant articles found for the latest period.\n")

    model_releases = []
    innovations = []
    market_trends = []
    
    for item in results:
        title = item.get('title', 'N/A')
        description = item.get('description', 'No description available.')
        url = item.get('url', '#')
        
        content_text = f"{title} {description}".lower()
        news_item = f"- **{title}**\n  - {description}\n  - [Source]({url})\n"
        
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
        content_parts.append("\n") # Add a newline before archive if there was categorized content

    # Using a raw string literal for the static part of the README
    # to avoid issues with backslashes if any were present.
    content_parts.append(r'''
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
''')
    return "".join(content_parts)

def get_date_range_for_query():
    today = datetime.now()
    # Assuming the script runs on Monday (weekday() == 0) as per cron
    # Last week Sunday is `today - timedelta(days=today.weekday() + 1)`
    # Last week Monday is `last week Sunday - timedelta(days=6)`
    end_of_last_week = today - timedelta(days=today.weekday() + 1)
    start_of_last_week = end_of_last_week - timedelta(days=6)
    return start_of_last_week.strftime("%Y-%m-%d"), end_of_last_week.strftime("%Y-%m-%d")

def main():
    print(f"Script started at {datetime.now().isoformat()}")
    
    if not os.path.exists(NEWS_HISTORY_DIR):
        try:
            os.makedirs(NEWS_HISTORY_DIR)
            print(f"Created directory: {NEWS_HISTORY_DIR}")
        except OSError as e:
            print(f"Error creating directory {NEWS_HISTORY_DIR}: {e}")
            return # Exit if cannot create history directory

    start_date_str, end_date_str = get_date_range_for_query()
    # Using a common search engine syntax for date ranges.
    query = f'"Quantum Computing" AND "AI" AND "news" after:{start_date_str} before:{end_date_str}'

    print(f"Fetching news for period: {start_date_str} to {end_date_str} with query: '{query}'")
    raw_api_response = search_brave(query) # Default count is 30
    
    data_to_save = {
        "query_details": {
            "query_sent": query,
            "period_start_date": start_date_str,
            "period_end_date": end_date_str,
            "retrieval_timestamp": datetime.now().isoformat()
        },
        "api_response": raw_api_response 
    }

    history_file_date_prefix = start_date_str 
    history_filename = os.path.join(NEWS_HISTORY_DIR, f"{history_file_date_prefix}_quantum_news.json")
    
    try:
        with open(history_filename, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=4)
        print(f"News data saved to {history_filename}")
    except IOError as e:
        print(f"Error saving news data to {history_filename}: {e}")
        # Continue and update README with current data even if saving history fails,
        # but log the error. The problem would be that history is not persisted.

    new_readme_content = generate_readme_content(data_to_save) 
    
    try:
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(new_readme_content)
        print("README.md updated successfully.")
    except IOError as e:
        print(f"Error writing README.md: {e}")

    print(f"Script finished at {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()
