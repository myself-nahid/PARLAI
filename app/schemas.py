from pydantic import BaseModel, Field
from typing import List, Optional, Any

class ExtractedBet(BaseModel):
    player_name: str
    sport: str = "Unknown"  
    prop_type: str = "Prop"
    line: float = 0.0       
    operator: str = "Over"  

class StatComparison(BaseModel):
    season_avg: float
    last_5_avg: float
    opponent_rank: int
    opponent_name: str

class BetAnalysis(BaseModel):
    player_name: str
    prop_description: str
    confidence_score: int
    risk_level: str
    insights: List[str]
    stats: StatComparison
    last_10_games: List[float]  

class ParlayResponse(BaseModel):
    overall_parlay_score: int
    bets: List[BetAnalysis]