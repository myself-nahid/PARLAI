from app.schemas import ExtractedBet, BetAnalysis, StatComparison, AdvancedMetrics
from app.services.sgo_client import get_player_history

async def analyze_single_bet(bet: ExtractedBet) -> BetAnalysis:
    data = await get_player_history(bet.player_name, bet.sport, bet.line)
    
    if not data.get('found'):
        return BetAnalysis(
            player_name=bet.player_name,
            prop_description=f"{bet.prop_type} {bet.operator} {bet.line}",
            confidence_score=50,
            risk_level="Moderate",
            insights=["Player data unavailable."],
            stats=StatComparison(season_avg=0, last_5_avg=0, opponent_name="N/A"),
            advanced=AdvancedMetrics(usage_rate=0, matchup_difficulty="-", home_away_split=0, expected_minutes="-", injury_status="-", days_rest=0, game_tempo="-", opponent_rank="-"),
            last_10_games=[]
        )

    stats = data['stats']
    adv = data['advanced']
    season_avg = stats['season_avg']
    last_5_avg = round(sum(stats['full_log'][-5:]) / 5, 1)

    score = 50
    
    # 1. Performance vs Line
    if bet.operator == "Over":
        if season_avg > bet.line: score += 10
        if last_5_avg > bet.line: score += 10
    else: # Under
        if season_avg < bet.line: score += 10
        if last_5_avg < bet.line: score += 10

    # 2. Matchup Impact
    if adv['matchup_difficulty'] == "Great": score += 10
    elif adv['matchup_difficulty'] == "Poor": score -= 10
    
    # 3. Usage Impact
    if adv['usage_rate'] > 25.0: score += 5

    # Cap Score
    score = min(98, max(25, score))

    insights = []
    
    # "Main Scoring Option"
    if adv['usage_rate'] > 25.0:
        insights.append("Projected to contribute as main scoring option.")
    
    # "Performance vs Line"
    diff = round(season_avg - bet.line, 1)
    if diff > 0 and bet.operator == "Over":
        insights.append(f"Averaging {season_avg} over the season (+{diff} vs line).")
    
    # "Defense"
    rank_num = int(''.join(filter(str.isdigit, adv['opponent_rank'])))
    if rank_num > 20:
        insights.append("Facing a team with a below average defense.")
    elif rank_num < 10:
        insights.append("Facing a top-tier defense (Tough Matchup).")
        
    # "Minutes"
    insights.append(f"Expected to play {adv['expected_minutes']} minutes in close contest.")

    # Risk Label
    risk = "Moderate" # Yellow
    if score >= 75: risk = "Safe" # Green
    if score <= 45: risk = "Risky" # Red

    return BetAnalysis(
        player_name=data['name'],
        prop_description=f"{bet.prop_type} {bet.operator} {bet.line}",
        confidence_score=score,
        risk_level=risk,
        insights=insights,
        stats=StatComparison(
            season_avg=season_avg,
            last_5_avg=last_5_avg,
            opponent_name="TBD"
        ),
        advanced=AdvancedMetrics(**adv),
        last_10_games=stats['full_log']
    )