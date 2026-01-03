# import httpx
# import asyncio
# from typing import Optional, Tuple, Dict, Any, List
# from app.config import settings

# # 1. Sport -> League ID Map
# SPORT_MAP = {
#     "NBA": "NBA", "Basketball": "NBA",
#     "NFL": "NFL", "Football": "NFL",
#     "NHL": "NHL", "Hockey": "NHL", 
#     "MLB": "MLB", "Baseball": "MLB"
# }

# # 2. Prop Name -> statID (used in Odds object)
# # These keys match the 'statID' field in the API response
# STAT_KEY_MAP = {
#     "points": ["points", "score"],
#     "rebounds": ["rebounds"],
#     "assists": ["assists"],
#     "pra": ["points", "rebounds", "assists"], # Requires summing multiple odds
#     "threes": ["threePointFieldGoalsMade"],
#     "fantasy": ["fantasyPoints"]
# }

# BASE_URL = "https://api.sportsgameodds.com/v2"
# HEADERS = {"X-API-Key": settings.SGO_API_KEY}

# # Cache to prevent fetching full player list multiple times
# PLAYER_CACHE: Dict[str, list] = {} 

# async def fetch_all_active_players(client: httpx.AsyncClient, league_id: str) -> list:
#     """Fetches ALL pages of active players for the league."""
#     if league_id in PLAYER_CACHE: return PLAYER_CACHE[league_id]

#     all_players = []
#     cursor = None
    
#     # Safety limit: NBA usually has ~600 active players
#     for _ in range(15): 
#         params = {"leagueID": league_id, "active": "true", "limit": 100}
#         if cursor: params["cursor"] = cursor

#         try:
#             res = await client.get(f"{BASE_URL}/players", params=params)
#             if res.status_code != 200: break
            
#             data = res.json()
#             batch = data.get('data', []) if isinstance(data, dict) else data
#             if not batch: break
            
#             all_players.extend(batch)
#             cursor = data.get('nextCursor') if isinstance(data, dict) else None
#             if not cursor: break
            
#         except Exception: break
    
#     PLAYER_CACHE[league_id] = all_players
#     return all_players

# async def fetch_player_metadata(client: httpx.AsyncClient, player_name: str, league_id: str) -> Tuple[Optional[str], Optional[str]]:
#     """Finds (playerID, teamID) using full list search."""
#     try:
#         players = await fetch_all_active_players(client, league_id)
#         target = player_name.lower().replace(".", "").strip()
        
#         for p in players:
#             names = p.get('names', {})
#             d_name = names.get('display', '').lower().replace(".", "")
#             f_name = names.get('firstName', '').lower()
#             l_name = names.get('lastName', '').lower()
#             full = f"{f_name} {l_name}".strip()
            
#             if target == d_name or target == full:
#                 return p['playerID'], p.get('teamID')
#             if len(target) > 3 and target == l_name:
#                 return p['playerID'], p.get('teamID')
                
#     except Exception as e:
#         print(f"Lookup Error: {e}")
#     return None, None

# async def fetch_game_logs(client: httpx.AsyncClient, player_id: str, team_id: str, league_id: str, stat_keys: list) -> list:
#     """
#     Fetches finalized events and extracts stats from the ODDS 'score' field.
#     """
#     if not team_id: return []
    
#     logs = []
#     try:
#         params = {
#             "leagueID": league_id,
#             "teamID": team_id,
#             "status": "finalized", 
#             "limit": 10,
#             # CRITICAL FLAGS FOR V2
#             "includeProps": "true", 
#             "oddsAvailable": "false"  # Must be false to see expired odds (which have the scores)
#         }
        
#         res = await client.get(f"{BASE_URL}/events", params=params)
#         if res.status_code != 200: return []
        
#         data = res.json()
#         events = data.get('data', []) if isinstance(data, dict) else data
        
#         for event in events:
#             # We look for the 'score' inside the ODDS for this player
#             odds = event.get('odds', [])
            
#             game_total = 0.0
#             found_any = False
            
#             # Since a player might have multiple odds (Points, Rebounds), we find the ones matching our stat_keys
#             for key in stat_keys:
#                 for odd in odds:
#                     if odd.get('playerID') == player_id:
#                         # Check if this odd is for the stat we want (e.g. statID="points")
#                         # Some APIs use 'statID', some use 'type' or 'name'. 
#                         # We check strictly against statID or loosely in description.
#                         stat_id = odd.get('statID', '').lower()
#                         desc = odd.get('description', '').lower()
                        
#                         if key == stat_id or key in desc:
#                             # The score is often in 'score' or 'result'
#                             score = odd.get('score')
#                             if score is not None:
#                                 try:
#                                     game_total += float(score)
#                                     found_any = True
#                                     # Break inner loop to avoid double counting same stat (e.g. multiple bookmakers)
#                                     break 
#                                 except: pass
            
#             if found_any:
#                 logs.append(game_total)

#     except Exception as e:
#         print(f"Log Fetch Error: {e}")
        
#     return logs

# async def fetch_player_stats(player_name: str, sport: str, prop_description: str) -> dict:
#     league_id = SPORT_MAP.get(sport, "NBA")
#     prop_clean = prop_description.lower()
    
#     needed_keys = ["points"] 
#     for k, v in STAT_KEY_MAP.items():
#         if k in prop_clean:
#             needed_keys = v
#             break
            
#     main_player = player_name.split('+')[0].strip()

#     async with httpx.AsyncClient(headers=HEADERS, timeout=25.0) as client:
#         # 1. Get ID & Team
#         pid, tid = await fetch_player_metadata(client, main_player, league_id)
        
#         if not pid or not tid:
#              # Return valid empty structure to avoid "Risk" calculation errors
#             return {"season_avg": 0, "last_5_avg": 0, "opponent_rank": 15, "last_10_games": []}

#         # 2. Get Logs
#         logs = await fetch_game_logs(client, pid, tid, league_id, needed_keys)
        
#         if not logs:
#             return {"season_avg": 0, "last_5_avg": 0, "opponent_rank": 15, "last_10_games": []}

#         return {
#             "season_avg": round(sum(logs)/len(logs), 1),
#             "last_5_avg": round(sum(logs[:5])/len(logs[:5]), 1),
#             "last_10_games": logs,
#             "opponent_rank": 15,
#             "opponent_name": "N/A"
#         }