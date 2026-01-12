from app.schemas import ExtractedBet, BetAnalysis, AdvancedStats, GraphData
from app.services.sgo_client import get_player_data

async def analyze_single_bet(bet: ExtractedBet) -> BetAnalysis:
    data = await get_player_data(bet.player_name, bet.sport, bet.line)
    
    if not data.get('found'):
        return BetAnalysis(
            player_name=bet.player_name,
            prop_description=f"{bet.prop_type} {bet.operator} {bet.line}",
            confidence_score=50,
            risk_level="High Risk",
            insights=["Player data unavailable."],
            advanced_stats=AdvancedStats(
                expected_minutes="-", avg_vs_opponent=0.0, usage_rate_change="-",
                matchup_difficulty="-", home_away_split="-", injury_status="-",
                days_rest="-", game_tempo="-", opponent_defense_rank="-", line_movement="-"
            ),
            last_10_graph=GraphData(labels=[], values=[], trend_line=bet.line)
        )

    adv_raw = data['advanced']
    logs = data['graph_data']
    season_avg = data['season_avg']
    
    score = 70 
    last_5_avg = sum(logs[-5:]) / 5
    
    if bet.operator == "Over":
        if season_avg > bet.line: score += 10
        else: score -= 10
        if last_5_avg > bet.line: score += 15
        else: score -= 15
    else: 
        if season_avg < bet.line: score += 10
        else: score -= 10
        if last_5_avg < bet.line: score += 15
        else: score -= 15

    if adv_raw['matchup_difficulty'] == "Great": score += 10
    elif adv_raw['matchup_difficulty'] == "Poor": score -= 15
    if "Fast pace" in adv_raw['game_tempo'] and bet.operator == "Over": score += 5
    if "Slow pace" in adv_raw['game_tempo'] and bet.operator == "Under": score += 5

    score = min(99, max(10, score))

    if score >= 90: risk = "Amazing"
    elif score >= 80: risk = "Strong"
    elif score >= 70: risk = "Moderate"
    elif score >= 60: risk = "Risky"
    else: risk = "High Risk"

    insights = []
    if "35+" in adv_raw['expected_minutes']:
        insights.append("Projected to contribute as main scoring option.")
    else:
        insights.append("Rotation player, minutes may vary.")

    diff = round(season_avg - bet.line, 1)
    if diff > 0 and bet.operator == "Over":
        insights.append(f"Averaging {season_avg} over the season (+{diff} vs line).")
    elif diff < 0 and bet.operator == "Under":
        insights.append(f"Averaging {season_avg} over the season (Below line).")
    else:
        insights.append(f"Averaging {season_avg} PPG over the last 10 games.")

    rank_num = int(''.join(filter(str.isdigit, adv_raw['opponent_defense_rank'])))
    if rank_num > 20:
        insights.append("Facing a team with a below average defense.")
    elif rank_num < 10:
        insights.append("Facing a top-tier defense (Tough Matchup).")
    else:
        insights.append("Facing a team with an average defensive rating.")

    insights.append(f"Expected to play {adv_raw['expected_minutes']} in close-fought contest.")

    return BetAnalysis(
        player_name=data['name'],
        prop_description=f"{bet.prop_type} {bet.operator} {bet.line}",
        confidence_score=score,
        risk_level=risk,
        insights=insights,
        advanced_stats=AdvancedStats(**adv_raw),
        last_10_graph=GraphData(
            labels=[f"G{i+1}" for i in range(10)],
            values=logs,
            trend_line=bet.line
        )
    )