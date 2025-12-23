from app.schemas import ExtractedBet, BetAnalysis, StatComparison
from app.services.stats import fetch_player_stats

async def analyze_single_bet(bet: ExtractedBet) -> BetAnalysis:
    # 1. Get Real Data
    stats_data = await fetch_player_stats(bet.player_name, bet.sport, bet.prop_type)
    
    # 2. The SCORING ALGORITHM
    # Start at neutral 50
    score = 50 
    
    # Weight 1: Season Average vs Line
    if bet.operator == "Over":
        if stats_data['season_avg'] > bet.line: score += 10
        else: score -= 10
    elif bet.operator == "Under":
        if stats_data['season_avg'] < bet.line: score += 10
        else: score -= 10
        
    # Weight 2: Recent Form (Last 5) - Heavier Weight
    if bet.operator == "Over":
        if stats_data['last_5_avg'] > bet.line: score += 15
    elif bet.operator == "Under":
        if stats_data['last_5_avg'] < bet.line: score += 15
        
    # Weight 3: Matchup
    # If taking OVER, we want a BAD defense (High rank number, e.g. 28th)
    if bet.operator == "Over" and stats_data['opponent_rank'] > 20:
        score += 10
    # If taking UNDER, we want a GOOD defense (Low rank number, e.g. 3rd)
    if bet.operator == "Under" and stats_data['opponent_rank'] < 10:
        score += 10

    # Cap Score
    score = min(99, max(1, score))
    
    # 3. Generate Insights (Rule-based for speed, or use LLM for variety)
    insights = []
    
    diff = round(stats_data['season_avg'] - bet.line, 1)
    if diff > 0 and bet.operator == "Over":
        insights.append(f"Averaging {diff} points above the line.")
    
    if stats_data['opponent_rank'] > 25:
        insights.append(f"Facing the {stats_data['opponent_rank']}th ranked defense (Favorable).")
    elif stats_data['opponent_rank'] < 5:
        insights.append(f"Facing a top 5 defense (Tough Matchup).")
        
    insights.append(f"Last 5 Game Avg: {stats_data['last_5_avg']}")

    # 4. Determine Risk Label
    risk = "Moderate"
    if score >= 80: risk = "Safe"
    if score <= 40: risk = "Risky"

    return BetAnalysis(
        player_name=bet.player_name,
        prop_description=f"{bet.prop_type} {bet.operator} {bet.line}",
        confidence_score=score,
        risk_level=risk,
        insights=insights,
        stats=StatComparison(
            season_avg=stats_data['season_avg'],
            last_5_avg=stats_data['last_5_avg'],
            opponent_rank=stats_data['opponent_rank'],
            opponent_name=stats_data['opponent_name']
        ),
        last_10_games=stats_data['last_10_games']
    )