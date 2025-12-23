from pydantic import BaseModel
from typing import List, Optional

class ExtractedBet(BaseModel):
    player_name: str
    team: Optional[str] = None
    sport: str              # NBA, NFL, etc.
    prop_type: str          # Points, Assists, Rebounds
    line: float             # The betting line (e.g., 22.5)
    operator: str           # "Over" or "Under"

class StatComparison(BaseModel):
    season_avg: float
    last_5_avg: float
    opponent_rank: int      # e.g., 28 (28th best defense = bad defense)
    opponent_name: str

class BetAnalysis(BaseModel):
    # Original Data
    player_name: str
    prop_description: str   # "Points Over 22.5"
    
    # AI Calculated Data
    confidence_score: int   # 0-100
    risk_level: str         # "Safe", "Moderate", "Risky"
    
    # UI Bullets
    insights: List[str]     # ["Averaging 24.5 PPG", "Facing weak defense"]
    
    # Chart Data
    stats: StatComparison
    last_10_games: List[int] # For the graph on Detail Screen

class ParlayResponse(BaseModel):
    overall_parlay_score: int
    bets: List[BetAnalysis]