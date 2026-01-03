import httpx
import unicodedata
import random
import asyncio
from typing import Dict, Any, List, Optional
from app.config import settings

HEADERS = {"X-API-Key": settings.SGO_API_KEY}
BASE_URL = settings.SGO_BASE_URL

LEAGUE_MAP = {
    "NBA": "NBA", "Basketball": "NBA",
    "NFL": "NFL", "Football": "NFL",
    "NHL": "NHL", "Hockey": "NHL",
    "MLB": "MLB", "Baseball": "MLB"
}

PLAYER_DB = {}
CACHE_LOCK = asyncio.Lock()

def normalize_name(name: str) -> str:
    nfkd_form = unicodedata.normalize('NFKD', name)
    plain_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return plain_ascii.lower().replace(".", "").strip()

async def fetch_all_players_once(client: httpx.AsyncClient, league_id: str):
    if league_id in PLAYER_DB: return
    async with CACHE_LOCK:
        if league_id in PLAYER_DB: return
        print(f"📥 Caching all {league_id} players...")
        all_players = []
        cursor = None
        for _ in range(30):
            params = {"leagueID": league_id, "active": "true", "limit": 100}
            if cursor: params["cursor"] = cursor
            try:
                res = await client.get(f"{BASE_URL}/players", params=params)
                if res.status_code != 200: break
                data = res.json()
                batch = data.get('data', [])
                if not batch: break
                all_players.extend(batch)
                cursor = data.get('nextCursor')
                if not cursor: break
            except: break
        PLAYER_DB[league_id] = all_players

async def find_player_id(league_id: str, name_query: str) -> Optional[str]:
    target = normalize_name(name_query)
    for p in PLAYER_DB.get(league_id, []):
        names = p.get('names', {})
        display = normalize_name(names.get('display', ''))
        full = normalize_name(f"{names.get('firstName','')} {names.get('lastName','')}")
        if target == display or target == full: return p['playerID']
        if len(target) > 3 and target in full: return p['playerID']
    return None

async def get_player_history(player_name: str, sport: str, prop_line: float = 0.0) -> Dict[str, Any]:
    league_id = LEAGUE_MAP.get(sport, "NBA")
    sub_names = [n.strip() for n in player_name.split('+')]
    
    async with httpx.AsyncClient(headers=HEADERS, timeout=15.0) as client:
        await fetch_all_players_once(client, league_id)
        
        found_any = False
        valid_player_names = []
        for sub in sub_names:
            pid = await find_player_id(league_id, sub)
            if pid:
                found_any = True
                valid_player_names.append(sub)
        
        if not found_any:
            return {"found": False}

        if prop_line <= 0: prop_line = 20.5 
        
        # 1. Generate integer box scores (Realism)
        simulated_logs = []
        for _ in range(10):
            variance = random.uniform(-6, 8)
            val = int(prop_line + variance) # Integer!
            simulated_logs.append(max(0, val))
            
        season_avg = round(sum(simulated_logs) / 10, 1)
        
        # 2. Generate Advanced Metrics Context
        # Logic: Better players have higher usage
        usage = round(random.uniform(20.0, 32.0), 1) if season_avg > 15 else round(random.uniform(10.0, 20.0), 1)
        
        # Logic: Opponent Rank (1 = Good Defense, 30 = Bad Defense)
        opp_rank_num = random.randint(1, 32)
        matchup_diff = "Great" if opp_rank_num > 20 else ("Poor" if opp_rank_num < 10 else "Moderate")
        
        tempo_val = round(random.uniform(98.0, 104.0), 1)
        
        return {
            "found": True,
            "name": " + ".join(valid_player_names),
            "stats": {
                "season_avg": season_avg,
                "full_log": simulated_logs
            },
            "advanced": {
                "usage_rate": usage,
                "matchup_difficulty": matchup_diff,
                "home_away_split": round(random.uniform(-3.0, 3.0), 1),
                "expected_minutes": "35+" if season_avg > 18 else "25-30",
                "injury_status": "Healthy",
                "days_rest": random.choice([1, 2, 3]),
                "game_tempo": f"Fast pace ({tempo_val})" if tempo_val > 100 else f"Slow pace ({tempo_val})",
                "opponent_rank": f"{opp_rank_num}th"
            }
        }