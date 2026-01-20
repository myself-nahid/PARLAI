from pydantic import BaseModel
from typing import List, Optional

class ExtractedBet(BaseModel):
    player_name: str
    sport: str = "NBA"
    prop_type: str = "Points"
    line: float = 0.0
    operator: str = "Over"

class GraphData(BaseModel):
    labels: List[str]
    values: List[float]
    trend_line: float

class AdvancedStats(BaseModel):
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

class MarketInsights(BaseModel):
    # 1. Best Price
    best_line: str              # "Over 20.5 (-105) @ FanDuel"
    best_book_logo: str         # "FanDuel"
    
    # 2. Market Disagreement
    market_disagreement: str    # "Low", "Medium", "High"
    books_range: str            # "20.0 - 21.5"
    
    # 3. Line Movement (Visuals)
    open_vs_current: str        # "Open 21.5 -> Now 20.5"
    movement_badge: str         # "Fast Market Move", "Stable Market"
    movement_graph: List[float] # [21.5, 21.5, 21.0, 20.5]
    
    # 4. Indicators
    vegas_edge: str             # "Good Price", "Bad Price"
    market_pressure: str        # "Money pushing the Over"
    hit_rate: str               # "Over 20.5 hits 53% historically"

class BetAnalysis(BaseModel):
    sport: str
    player_name: str
    prop_description: str
    confidence_score: int
    risk_level: str
    win_probability: str
    insights: List[str]
    
    advanced_stats: AdvancedStats
    market_insights: MarketInsights 
    last_10_graph: GraphData

class ParlayResponse(BaseModel):
    overall_parlay_score: int
    
    # New Parlay Reality Features
    win_probability: str        # "23%"
    win_label: str              # "Fragile", "Stable"
    weakest_leg: str            # "Ja Morant: Over 20.5"
    
    bets: List[BetAnalysis]