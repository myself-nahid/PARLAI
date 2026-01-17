import nfl_data_py as nfl
import pandas as pd
from datetime import datetime

# Cache the data in memory so we don't download it on every request
NFL_CACHE = {}

def get_nfl_real_stats(player_name: str, prop_type: str) -> dict:
    """
    Fetches real NFL 2024 weekly stats using nfl_data_py.
    """
    print(f"NFL DATA: Fetching real data for {player_name}...")
    
    current_year = 2024
    
    try:
        # 1. Load Data 
        if current_year not in NFL_CACHE:
            print("Downloading NFL 2024 Weekly Data (This happens once)...")
            NFL_CACHE[current_year] = nfl.import_weekly_data([current_year])
        
        df = NFL_CACHE[current_year]
        '''
        # 2. Filter by Player Name
        # nfl_data_py names are usually "J.Jennings". We need to match loosely.
        # Create a 'full_name' column if not exists or search 'player_display_name'
        '''
        target = player_name.lower().replace(".", "").replace(" ", "")
        
        # Fuzzy match logic
        # We look for rows where the cleaned name matches
        def name_match(row_name):
            if not isinstance(row_name, str): return False
            clean_row = row_name.lower().replace(".", "").replace(" ", "")
            return target in clean_row or clean_row in target

        player_df = df[df['player_display_name'].apply(name_match)]
        
        if player_df.empty:
            print(f"NFL Player {player_name} not found in 2024 data.")
            return {}

        # 3. Sort by Week (Latest first) and take last 10
        player_df = player_df.sort_values(by='week', ascending=False).head(10)
        
        # 4. Extract Prop Data
        prop_clean = prop_type.lower().replace(" ", "")
        logs = []
        
        for _, row in player_df.iterrows():
            val = 0.0
            
            # --- PROP MAPPING ---
            if "targets" in prop_clean:
                val = row['targets']
            elif "rush+rec" in prop_clean or "yards" in prop_clean:
                val = row['rushing_yards'] + row['receiving_yards']
            elif "rec" in prop_clean and "yds" in prop_clean:
                val = row['receiving_yards']
            elif "rush" in prop_clean and "yds" in prop_clean:
                val = row['rushing_yards']
            elif "fantasy" in prop_clean:
                # Standard Fantasy Scoring: 
                # 0.1 per rush/rec yard, 6 per TD, 1 per Rec (PPR), -2 fumble
                pts = (row['rushing_yards'] * 0.1) + \
                      (row['receiving_yards'] * 0.1) + \
                      (row['rushing_tds'] * 6) + \
                      (row['receiving_tds'] * 6) + \
                      (row['receptions'] * 1.0)
                val = round(pts, 1)
            elif "touchdown" in prop_clean or "td" in prop_clean:
                val = row['rushing_tds'] + row['receiving_tds']
            elif "reception" in prop_clean:
                val = row['receptions']
            
            # Handle NaNs
            if pd.isna(val): val = 0.0
            logs.append(float(val))
            
        # Reverse list to show G1 -> G10
        logs.reverse()
        
        print(f"NFL Success: Found {len(logs)} games for {player_name}")
        return {"logs": logs}

    except Exception as e:
        print(f"NFL Data Error: {e}")
        return {}