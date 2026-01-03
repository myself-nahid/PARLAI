from pydantic import BaseModel
from typing import List, Optional

class ExtractedBet(BaseModel):
    player_name: str
    sport: str = "NBA"
    prop_type: str = "Points"
    line: float = 0.0
    operator: str = "Over"

class AdvancedMetrics(BaseModel):
    usage_rate: float        
    matchup_difficulty: str  
    home_away_split: float   
    expected_minutes: str    
    injury_status: str       
    days_rest: int           
    game_tempo: str          
    opponent_rank: str       

class StatComparison(BaseModel):
    season_avg: float
    last_5_avg: float
    opponent_name: str

class BetAnalysis(BaseModel):
    player_name: str
    prop_description: str
    confidence_score: int
    risk_level: str  
    insights: List[str]
    stats: StatComparison
    advanced: AdvancedMetrics
    last_10_games: List[int] 

class ParlayResponse(BaseModel):
    overall_parlay_score: int
    bets: List[BetAnalysis]