import random
import asyncio
from app.schemas import StatComparison

# Mock data generator to simulate an external API (like TheRundown or SportRadar)
async def fetch_player_stats(player_name: str, sport: str, prop: str) -> dict:
    # Simulate network delay
    await asyncio.sleep(0.5) 
    
    # Generate realistic looking data for the demo
    # In production, use httpx.get("https://api.sportsdata.io/...")
    
    base_val = random.randint(15, 30) # Random base stat
    
    last_10 = [max(0, base_val + random.randint(-8, 8)) for _ in range(10)]
    season_avg = round(sum(last_10) / 10, 1)
    last_5_avg = round(sum(last_10[-5:]) / 5, 1)
    
    return {
        "season_avg": season_avg,
        "last_5_avg": last_5_avg,
        "last_10_games": last_10,
        "opponent_rank": random.randint(1, 30), # 1 is good defense, 30 is bad
        "opponent_name": "MIA"
    }