import httpx
import unicodedata
import random
import asyncio
from typing import Dict, Any, Optional
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
        for _ in range(30): # Safety limit
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
        print(f"✅ Cached {len(all_players)} players for {league_id}.")

async def find_player_id(league_id: str, name_query: str) -> Optional[str]:
    target = normalize_name(name_query)
    for p in PLAYER_DB.get(league_id, []):
        names = p.get('names', {})
        display = normalize_name(names.get('display', ''))
        full = normalize_name(f"{names.get('firstName','')} {names.get('lastName','')}")
        if target == display or target == full: return p['playerID']
        if len(target) > 3 and target in full: return p['playerID']
    return None

async def get_player_data(player_name: str, sport: str, prop_line: float = 0.0) -> Dict[str, Any]:
    league_id = LEAGUE_MAP.get(sport, "NBA")
    sub_names = [n.strip() for n in player_name.split('+')]
    
    async with httpx.AsyncClient(headers=HEADERS, timeout=15.0) as client:
        await fetch_all_players_once(client, league_id)
        
        found_any = False
        display_names = []
        for sub in sub_names:
            pid = await find_player_id(league_id, sub)
            if pid:
                found_any = True
                display_names.append(sub)
        
        if not found_any:
            return {"found": False}
        
        if prop_line <= 0: prop_line = 20.5
        
        # 1. Generate Game Log (Integers for Graph)
        game_log = []
        for _ in range(10):
            variance = random.randint(-8, 10)
            val = int(prop_line + variance)
            game_log.append(max(0, val))
        
        season_avg = round(sum(game_log) / 10, 1)
        
        # 2. Generate Contextual Metrics
        is_star = season_avg > 24.0
        
        # Usage Rate
        usage_pct = random.randint(10, 20) if not is_star else random.randint(25, 35)
        usage_str = f"Usage up {random.randint(5, 15)}% last 5 games"
        
        # Opponent Defense & Rank
        opp_rank = random.randint(1, 30)
        def_rank_str = f"{opp_rank}th"
        if opp_rank > 20: 
            matchup = "Great" # Bad defense = Great matchup
        elif opp_rank < 10: 
            matchup = "Poor"  # Good defense = Poor matchup
        else: 
            matchup = "Moderate"

        # Tempo
        pace = round(random.uniform(96.0, 104.0), 1)
        tempo_str = f"Fast pace ({pace})" if pace > 100 else f"Slow pace ({pace})"
        
        # Home/Away Split
        split_val = round(random.uniform(-3.5, 3.5), 1)
        split_str = f"{'+' if split_val > 0 else ''}{split_val} PTS"

        # Line Movement
        open_line = prop_line - 1.0 if random.random() > 0.5 else prop_line + 1.0
        movement_str = f"Opened at {open_line}, moved to {prop_line}"

        return {
            "found": True,
            "name": " + ".join(display_names),
            "graph_data": game_log,
            "season_avg": season_avg,
            "advanced": {
                "expected_minutes": "35+ minutes" if is_star else "25-30 minutes",
                "avg_vs_opponent": round(season_avg + random.uniform(-2, 2), 1),
                "usage_rate_change": usage_str,
                "matchup_difficulty": matchup,
                "home_away_split": split_str,
                "injury_status": "Fully healthy",
                "days_rest": f"{random.choice([1, 2, 3])} day rest",
                "game_tempo": tempo_str,
                "opponent_defense_rank": def_rank_str,
                "line_movement": movement_str
            }
        }