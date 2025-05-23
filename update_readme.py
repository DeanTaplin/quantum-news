import os
import json
import requests
from datetime import datetime, timedelta
# For robust month calculations, dateutil.relativedelta can be useful.
# Ensure 'python-dateutil' is added to dependencies if you use it.
# For this implementation, we'll use datetime and timedelta.

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

def generate_readme_content(data_saved_to_history, news_period_label=""): 
    api_response_data = data_saved_to_history.get('api_response', {})
    query_details = data_saved_to_history.get('query_details', {})
    results = api_response_data.get('web', {}).get('results', [])
    
    content_parts = []
    content_parts.append("# Quantum Computing News Tracker\n\n")
    content_parts.append("A curated collection of the latest developments, breakthroughs, and news in the field of Quantum Computing.\n\n")
    
    header_text = news_period_label if news_period_label else datetime.now().strftime("%B %d, %Y")
    content_parts.append(f"## Latest Updates ({header_text})\n\n")
    
    if not results:
        search_type = query_details.get("search_type", "weekly")
        if search_type == "monthly_fallback":
            content_parts.append("No new relevant articles found for the past week. Displaying notable articles from the past month.\n")
            # Check again if fallback also yielded nothing specifically for the message
            if not api_response_data.get('web', {}).get('results', []): # Check results from fallback specifically
                 content_parts.append("No notable articles found for the past month either.\n")
        else: # weekly search that found nothing
            content_parts.append("No new relevant articles found for the past week. Consider checking the archive or if a fallback monthly search occurs next.\n")
    else: # Results were found
        search_type = query_details.get("search_type", "weekly")
        if search_type == "monthly_fallback":
             content_parts.append("No new relevant articles found for the past week. Displaying notable articles from the past month:\n\n")


    model_releases = []
    innovations = []
    market_trends = []
    
    for item in results: # Iterate through results from either primary or fallback
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
        content_parts.append("\n")

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

def get_previous_week_date_range():
    today = datetime.now()
    # Monday of the current week
    start_of_this_week = today - timedelta(days=today.weekday())
    # Monday of last week
    start_of_last_week = start_of_this_week - timedelta(days=7)
    # Sunday of last week
    end_of_last_week = start_of_last_week + timedelta(days=6)
    return start_of_last_week.strftime("%Y-%m-%d"), end_of_last_week.strftime("%Y-%m-%d")

def get_previous_month_date_range():
    today = datetime.now()
    # First day of current month
    first_day_current_month = today.replace(day=1)
    # Last day of previous month is one day before first day of current month
    last_day_previous_month = first_day_current_month - timedelta(days=1)
    # First day of previous month
    first_day_previous_month = last_day_previous_month.replace(day=1)
    return first_day_previous_month.strftime("%Y-%m-%d"), last_day_previous_month.strftime("%Y-%m-%d")

def main():
    print(f"Script started at {datetime.now().isoformat()}")
    search_type = "weekly" 
    news_period_label_for_readme = ""
    actual_start_date_str, actual_end_date_str = "", "" # To store dates of data actually fetched

    if not os.path.exists(NEWS_HISTORY_DIR):
        try:
            os.makedirs(NEWS_HISTORY_DIR)
            print(f"Created directory: {NEWS_HISTORY_DIR}")
        except OSError as e:
            print(f"Error creating directory {NEWS_HISTORY_DIR}: {e}")
            return

    # Primary search: Previous Week
    intended_start_week, intended_end_week = get_previous_week_date_range()
    actual_start_date_str, actual_end_date_str = intended_start_week, intended_end_week
    
    query = f'"Quantum Computing" AND "AI" AND "news" after:{actual_start_date_str} before:{actual_end_date_str}'
    print(f"Attempting primary search (previous week): {actual_start_date_str} to {actual_end_date_str}")
    raw_api_response = search_brave(query)
    
    news_period_label_for_readme = f"Week of {datetime.strptime(actual_start_date_str, '%Y-%m-%d').strftime('%B %d, %Y')}"

    # Fallback search: Previous Month (if no results from weekly)
    # Define "no results" as an empty list for 'results' key in 'web'
    results_found = raw_api_response.get('web', {}).get('results', [])
    if not results_found:
        print("No results found for the previous week. Attempting fallback to previous month.")
        search_type = "monthly_fallback"
        
        actual_start_date_str, actual_end_date_str = get_previous_month_date_range()
        query = f'"Quantum Computing" AND "AI" AND "news" after:{actual_start_date_str} before:{actual_end_date_str}'
        print(f"Attempting fallback search (previous month): {actual_start_date_str} to {actual_end_date_str}")
        raw_api_response = search_brave(query) # This will be the response used if fallback happens
        # Update label for README to reflect monthly fallback
        month_dt = datetime.strptime(actual_start_date_str, '%Y-%m-%d')
        news_period_label_for_readme = f"Month of {month_dt.strftime('%B %Y')}"
        # Re-check if fallback also has results for accurate messaging in generate_readme_content
        results_found = raw_api_response.get('web', {}).get('results', [])


    # Prepare data for saving
    # History filename is based on the script's run week, not the data's period (if fallback)
    history_file_run_date_prefix = intended_start_week 

    data_to_save = {
        "query_details": {
            "query_sent": query, 
            "intended_period_start_date": intended_start_week,
            "intended_period_end_date": intended_end_week,
            "actual_data_period_start": actual_start_date_str, # Start date of the data in api_response
            "actual_data_period_end": actual_end_date_str,     # End date of the data in api_response
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
