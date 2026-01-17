from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
import time
import pandas as pd

def get_nba_real_stats(player_name: str, prop_type: str) -> dict:
    """
    Fetches LAST 10 GAMES directly from NBA.com API (Free).
    """
    print(f"NBA API: Fetching real data for {player_name}...")
    
    try:
        # 1. Find Player ID
        # nba_api does fuzzy matching well
        nba_players = players.find_players_by_full_name(player_name)
        if not nba_players:
            print(f"NBA API: Player {player_name} not found.")
            return {}
        
        player_id = nba_players[0]['id']
        
        # 2. Get Game Logs (Season 2024-25)
        # Note: 'Season' param might need updating based on current date
        gamelog = playergamelog.PlayerGameLog(player_id=player_id, season='2024-25')
        df = gamelog.get_data_frames()[0]
        
        if df.empty:
            # Try previous season if current is empty (e.g. start of season)
            gamelog = playergamelog.PlayerGameLog(player_id=player_id, season='2023-24')
            df = gamelog.get_data_frames()[0]

        # 3. Extract Last 10 Games
        last_10 = df.head(10)
        logs = []
        
        # 4. Handle Prop Logic (PRA, Pts+Ast, etc.)
        prop_clean = prop_type.lower().replace(" ", "")
        
        for _, row in last_10.iterrows():
            pts = row['PTS']
            reb = row['REB']
            ast = row['AST']
            threes = row['FG3M']
            
            val = 0
            if "pra" in prop_clean:
                val = pts + reb + ast
            elif "rebs+asts" in prop_clean or "reb+ast" in prop_clean:
                val = reb + ast
            elif "pts+rebs" in prop_clean:
                val = pts + reb
            elif "pts+asts" in prop_clean:
                val = pts + ast
            elif "assist" in prop_clean:
                val = ast
            elif "rebound" in prop_clean:
                val = reb
            elif "three" in prop_clean:
                val = threes
            else:
                val = pts # Default to points
            
            logs.append(float(val))

        '''
        # Reverse to show Oldest -> Newest for graph? 
        # Usually graphs show Game 1 (Oldest) to Game 10 (Newest)
        # NBA API returns Newest first. Let's reverse it for the graph.
        '''
        logs.reverse()

        print(f"NBA API Success: Found {len(logs)} games for {player_name}")
        return {"logs": logs}

    except Exception as e:
        print(f"NBA API Failed: {e}")
        return {}