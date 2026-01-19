import pandas as pd
from datetime import datetime
import asyncio

from nba_api.stats.endpoints import leaguestandingsv3
import nfl_data_py as nfl

# Cache Storage
RANK_CACHE = {
    "NBA": {"timestamp": None, "data": {}},
    "NFL": {"timestamp": None, "data": {}}
}

def get_nba_defense_ranks():
    """Fetches NBA Team Defensive Rankings (Points Allowed Per Game)"""
    try:
        # Check Cache (Valid for 24 hours)
        cached = RANK_CACHE["NBA"]
        if cached["timestamp"] and (datetime.now() - cached["timestamp"]).total_seconds() < 86400:
            return cached["data"]

        print("UPDATING NBA DEFENSIVE RANKINGS...")
        # Get Standings
        standings = leaguestandingsv3.LeagueStandingsV3(season='2024-25')
        df = standings.get_data_frames()[0]
        
        # Sort by Points Allowed (OppPointsPG) - Lower is Better Defense
        # Note: API keys might differ, looking for 'OppPointsPG' or 'OPP_PTS'
        # Taking 'OppPointsPG' usually in column 57 or by name
        if 'OppPointsPG' in df.columns:
            df = df.sort_values(by='OppPointsPG', ascending=True) # 1st = Lowest Points Allowed
        else:
            # Fallback column name check needed? usually LeagueStandings has it.
            return {}

        rank_map = {}
        for rank, row in enumerate(df.itertuples(), 1):
            # Map Team Name & ID to Rank
            team_name = str(row.TeamName).lower()
            city = str(row.TeamCity).lower()
            rank_map[team_name] = rank
            rank_map[city] = rank
            rank_map[f"{city} {team_name}"] = rank # "Los Angeles Lakers"

        RANK_CACHE["NBA"] = {"timestamp": datetime.now(), "data": rank_map}
        return rank_map
    except Exception as e:
        print(f"NBA Rank Error: {e}")
        return {}

def get_nfl_defense_ranks():
    """Fetches NFL Team Defensive Rankings (Points Allowed)"""
    try:
        cached = RANK_CACHE["NFL"]
        if cached["timestamp"] and (datetime.now() - cached["timestamp"]).total_seconds() < 86400:
            return cached["data"]

        print("UPDATING NFL DEFENSIVE RANKINGS...")
        df = nfl.import_seasonal_data([2024])
        
        # Sort by points allowed ('points_allowed')
        if 'points_allowed' in df.columns:
            df = df.sort_values(by='points_allowed', ascending=True)
        else:
            return {}

        rank_map = {}
        for rank, row in enumerate(df.itertuples(), 1):
            # nfl_data_py uses abbreviations usually (SEA, SF)
            team_abbr = str(row.team).lower()
            rank_map[team_abbr] = rank

        RANK_CACHE["NFL"] = {"timestamp": datetime.now(), "data": rank_map}
        return rank_map
    except Exception as e:
        print(f"NFL Rank Error: {e}")
        return {}

async def get_opponent_rank(league: str, opponent_name: str) -> str:
    """Returns '5th', '28th', or 'N/A'"""
    if not opponent_name or opponent_name == "TBD":
        return "N/A"
        
    ranks = {}
    if league == "NBA":
        ranks = get_nba_defense_ranks()
    elif league == "NFL":
        ranks = get_nfl_defense_ranks()
    
    # Fuzzy Lookup
    opp_clean = opponent_name.lower().replace(".", "")
    
    # 1. Exact Match
    if opp_clean in ranks:
        r = ranks[opp_clean]
        return f"{r}th"
        
    # 2. Partial Match (e.g. "Lakers" in "Los Angeles Lakers")
    for team_key, rank_val in ranks.items():
        if team_key in opp_clean or opp_clean in team_key:
            return f"{rank_val}th"
            
    return "N/A"