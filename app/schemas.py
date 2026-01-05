from pydantic import BaseModel
from typing import List, Optional

class ExtractedBet(BaseModel):
    player_name: str
    sport: str = "NBA"
    prop_type: str = "Points"
    line: float = 0.0
    operator: str = "Over"

class GraphData(BaseModel):
    """Data for the 'Last 10 Games' Line Graph"""
    labels: List[str]       
    values: List[int]       
    trend_line: float       

class AdvancedStats(BaseModel):
    """Fields for 'Full Analysis' and 'More' screens"""
    expected_minutes: str       
    avg_vs_opponent: float      
    usage_rate_change: str      
    matchup_difficulty: str     
    home_away_split: str        
    injury_status: str          
    days_rest: str              
    game_tempo: str             
    opponent_defense_rank: str  
    line_movement: str          

class BetAnalysis(BaseModel):
    """Main object for each player card"""
    player_name: str
    prop_description: str
    player_point: float      
    confidence_score: int       
    risk_level: str    
    insights: List[str]         
    advanced_stats: AdvancedStats
    last_10_graph: GraphData

class ParlayResponse(BaseModel):
    overall_parlay_score: int
    bets: List[BetAnalysis]