from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog, commonplayerinfo
import pandas as pd

def get_nba_status(player_name: str) -> str:
    """Checks if player is Active or Inactive on the roster."""
    try:
        nba_players = players.find_players_by_full_name(player_name)
        if not nba_players: return "Active"
        pid = nba_players[0]['id']
        
        # Fetch Info
        info = commonplayerinfo.CommonPlayerInfo(player_id=pid)
        df = info.get_data_frames()[0]
        
        if df.empty: return "Active"
        
        # 'ROSTERSTATUS' usually contains "Active" or "Inactive"
        status = df.iloc[0]['ROSTERSTATUS']
        return str(status).title() # "Active"
    except:
        return "Active"

def get_nba_real_stats(player_name: str, prop_type: str) -> dict:
    """
    Fetches stats + metadata (minutes, dates, home/away).
    """
    print(f"NBA API: Fetching deep data for {player_name}...")
    
    try:
        # 1. Find Player
        nba_players = players.find_players_by_full_name(player_name)
        if not nba_players: return {}
        player_id = nba_players[0]['id']
        
        # 2. Get Logs
        gamelog = playergamelog.PlayerGameLog(player_id=player_id, season='2024-25')
        df = gamelog.get_data_frames()[0]
        if df.empty:
            gamelog = playergamelog.PlayerGameLog(player_id=player_id, season='2023-24')
            df = gamelog.get_data_frames()[0]

        # 3. Process Data
        logs = []
        minutes_list = []
        dates_list = []
        venues_list = []
        
        prop_clean = prop_type.lower().replace(" ", "")
        
        last_10 = df.head(10)
        
        for _, row in last_10.iterrows():
            pts, reb, ast, threes = row['PTS'], row['REB'], row['AST'], row['FG3M']
            
            if "pra" in prop_clean: val = pts + reb + ast
            elif "rebs+asts" in prop_clean: val = reb + ast
            elif "pts+rebs" in prop_clean: val = pts + reb
            elif "assist" in prop_clean: val = ast
            elif "rebound" in prop_clean: val = reb
            elif "three" in prop_clean: val = threes
            else: val = pts
            
            logs.append(float(val))
            minutes_list.append(row['MIN']) 
            dates_list.append(row['GAME_DATE']) 
            venues_list.append("Home" if "vs." in str(row['MATCHUP']) else "Away")

        # Reverse lists 
        logs.reverse()
        minutes_list.reverse()
        dates_list.reverse()
        venues_list.reverse()

        return {
            "logs": logs,
            "minutes": minutes_list,
            "dates": dates_list,
            "venues": venues_list
        }

    except Exception as e:
        print(f"NBA API Failed: {e}")
        return {}