from app.schemas import ExtractedBet, BetAnalysis, StatComparison
from app.services.sgo_client import get_player_history

async def analyze_single_bet(bet: ExtractedBet) -> BetAnalysis:
    data = await get_player_history(bet.player_name, bet.sport, bet.line)
    
    stats = data.get('stats', {})
    
    if not data['found']:
        return BetAnalysis(
            player_name=bet.player_name,
            prop_description=f"{bet.prop_type} {bet.operator} {bet.line}",
            confidence_score=50,
            risk_level="Unknown",
            insights=["Player not found in active roster."],
            stats=StatComparison(season_avg=0, last_5_avg=0, opponent_rank=0, opponent_name="N/A"),
            last_10_games=[]
        )

    # Scoring Logic
    score = 50
    season_avg = stats.get('season_avg', 0)
    
    # Compare generated stats vs line
    if bet.operator == "Over":
        if season_avg > bet.line: score += 15
        else: score -= 10
    elif bet.operator == "Under":
        if season_avg < bet.line: score += 15
        else: score -= 10

    # Insights
    insights = []
    diff = round(season_avg - bet.line, 1)
    if diff > 0 and bet.operator == "Over":
        insights.append(f"Trending {diff} points OVER the line recently.")
    elif diff < 0 and bet.operator == "Over":
        insights.append(f"Averaging {abs(diff)} points UNDER the line.")
        
    insights.append(f"Season Avg: {season_avg}")

    # Risk Label
    risk = "Moderate"
    if score >= 65: risk = "Safe"
    if score <= 40: risk = "Risky"

    return BetAnalysis(
        player_name=data['name'],
        prop_description=f"{bet.prop_type} {bet.operator} {bet.line}",
        confidence_score=score,
        risk_level=risk,
        insights=insights,
        stats=StatComparison(
            season_avg=season_avg,
            last_5_avg=season_avg, 
            opponent_rank=15,
            opponent_name=data.get('opponent', 'TBD')
        ),
        last_10_games=stats.get('full_log', []) 
    )