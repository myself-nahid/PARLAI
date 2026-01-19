import nfl_data_py as nfl
import pandas as pd
from datetime import datetime

# Caches to prevent re-downloading large datasets
NFL_CACHE = {}
INJURY_CACHE = {"data": None, "timestamp": None}

def preload_nfl_data():
    """Downloads heavy datasets into RAM on startup."""
    current_year = 2024
    try:
        if current_year not in NFL_CACHE:
            print("(Background) Downloading NFL Weekly Stats...")
            NFL_CACHE[current_year] = nfl.import_weekly_data([current_year])
            
        if INJURY_CACHE["data"] is None:
            print("(Background) Downloading NFL Injury Report...")
            INJURY_CACHE["data"] = nfl.import_injuries([current_year])
            INJURY_CACHE["timestamp"] = datetime.now()
    except Exception as e:
        print(f"Preload Warning: {e}")

def get_nfl_injury_status(player_name: str) -> str:
    """
    Fetches the latest official injury report for the player.
    """
    current_year = 2024 
    
    try:
        # "if not df" raises ValueError in Pandas. Must use "is None".
        if INJURY_CACHE["data"] is None or (datetime.now() - INJURY_CACHE["timestamp"]).total_seconds() > 3600:
            print("Downloading NFL Injury Report...")
            INJURY_CACHE["data"] = nfl.import_injuries([current_year])
            INJURY_CACHE["timestamp"] = datetime.now()
        
        df = INJURY_CACHE["data"]
        
        # nfl_data_py uses 'full_name' for injuries, not 'player'
        name_col = 'full_name'
        if 'full_name' not in df.columns:
            # Fallbacks just in case schema changes
            if 'player' in df.columns: name_col = 'player'
            elif 'name' in df.columns: name_col = 'name'
            else:
                print("Injury DB Column 'full_name' missing.")
                return "Active"

        # Normalize Name for matching
        target = player_name.lower().replace(".", "").replace(" ", "")
        
        def name_match(row_name):
            if not isinstance(row_name, str): return False
            clean = row_name.lower().replace(".", "").replace(" ", "")
            return target in clean or clean in target

        # Find Player using the correct column
        player_df = df[df[name_col].apply(name_match)].copy()
        
        if player_df.empty:
            return "Fully Healthy" # Not on the report = Healthy

        # Get most recent report (sort by week desc)
        # Ensure 'week' is numeric for sorting
        if 'week' in player_df.columns:
            player_df['week'] = pd.to_numeric(player_df['week'], errors='coerce')
            latest = player_df.sort_values(by='week', ascending=False).iloc[0]
        else:
            latest = player_df.iloc[0]
        
        # 'report_status' contains "Questionable", "Out", etc.
        status = latest.get('report_status')
        
        if pd.isna(status): return "Active"
        return str(status)

    except Exception as e:
        print(f"Injury Fetch Error: {e}")
        return "Active"

def get_nfl_real_stats(player_name: str, prop_type: str) -> dict:
    """
    Fetches real NFL 2024 weekly stats.
    """
    print(f"NFL DATA: Fetching real data for {player_name}...")
    current_year = 2024
    
    try:
        if current_year not in NFL_CACHE:
            print("Downloading NFL Weekly Data...")
            NFL_CACHE[current_year] = nfl.import_weekly_data([current_year])
        
        df = NFL_CACHE[current_year]
        target = player_name.lower().replace(".", "").replace(" ", "")
        
        def name_match(row_name):
            if not isinstance(row_name, str): return False
            clean = row_name.lower().replace(".", "").replace(" ", "")
            return target in clean or clean in target

        # Use 'player_display_name' for stats data
        player_df = df[df['player_display_name'].apply(name_match)]
        
        if player_df.empty:
            return {}

        # Sort by Week (Latest first) and take last 10
        player_df = player_df.sort_values(by='week', ascending=False).head(10)
        
        logs = []
        venues_list = []
        
        prop_clean = prop_type.lower().replace(" ", "")
        
        for _, row in player_df.iterrows():
            val = 0.0
            
            # Prop Mapping
            if "targets" in prop_clean: val = row['targets']
            elif "rush+rec" in prop_clean: val = row['rushing_yards'] + row['receiving_yards']
            elif "rec" in prop_clean and "yds" in prop_clean: val = row['receiving_yards']
            elif "rush" in prop_clean and "yds" in prop_clean: val = row['rushing_yards']
            elif "fantasy" in prop_clean:
                # Standard Fantasy Scoring
                pts = (row['rushing_yards'] * 0.1) + \
                      (row['receiving_yards'] * 0.1) + \
                      (row['rushing_tds'] * 6) + \
                      (row['receiving_tds'] * 6) + \
                      (row['receptions'] * 1.0)
                val = round(pts, 1)
            elif "touchdown" in prop_clean: val = row['rushing_tds'] + row['receiving_tds']
            elif "reception" in prop_clean: val = row['receptions']
            
            if pd.isna(val): val = 0.0
            logs.append(float(val))
            
            # Location metadata
            venues_list.append("Home" if row.get('location') == 'Home' else "Away")
            
        logs.reverse()
        venues_list.reverse()
        
        return {
            "logs": logs,
            "venues": venues_list,
            "minutes": [], 
            "dates": []
        }

    except Exception as e:
        print(f"NFL Data Error: {e}")
        return {}