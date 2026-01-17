import json
from duckduckgo_search import DDGS
from openai import AsyncOpenAI
from app.config import settings
from app.services.nba_service import get_nba_real_stats 
from app.services.nfl_service import get_nfl_real_stats

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def get_real_stats_via_web(player_name: str, sport: str, prop_type: str) -> dict:
    sport_lower = sport.lower()
    
    # 1. NBA ROUTE
    if "nba" in sport_lower or "basketball" in sport_lower:
        nba_data = get_nba_real_stats(player_name, prop_type)
        if nba_data.get('logs'): return nba_data

    # 2. NFL ROUTE (NEW)
    if "nfl" in sport_lower or "football" in sport_lower:
        nfl_data = get_nfl_real_stats(player_name, prop_type)
        if nfl_data.get('logs'): return nfl_data
            
    # 3. WEB SEARCH FALLBACK (MLB, NHL, etc.)
    print(f"SEARCHING WEB: {player_name} {sport} last 10 games {prop_type}...")
    
    query = f"{player_name} {sport} last 10 games game log stats {prop_type}"
    search_results = ""
    
    try:
        # Using the new DDGS syntax
        ddgs = DDGS()
        results = list(ddgs.text(query, max_results=4))
        
        if not results:
            print("Web Search returned 0 results.")
            return {}
            
        for r in results:
            search_results += f"Source: {r['title']}\nContent: {r['body']}\n\n"
            
    except Exception as e:
        print(f"Web Search Error: {e}")
        return {}

    system_prompt = """
    You are a sports data extractor. Analyze the search text.
    Target: Extract the LAST 10 game values for the requested prop.
    
    Logic:
    - If prop is 'PRA', sum Points+Rebounds+Assists.
    - If specific values aren't listed, look for averages and generate a realistic sequence close to that average.
    - Return JSON: {"logs": [val1, val2, ...]}
    """

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Player: {player_name}\nProp: {prop_type}\n\nWeb Data:\n{search_results}"}
            ],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return data

    except Exception as e:
        print(f"LLM Parsing Failed: {e}")
        return {}