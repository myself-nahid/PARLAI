from app.schemas import ExtractedBet, BetAnalysis, AdvancedStats, GraphData, MarketInsights
from app.services.sgo_client import get_player_data

async def analyze_single_bet(bet: ExtractedBet) -> BetAnalysis:
    data = await get_player_data(bet.player_name, bet.sport, bet.line, bet.prop_type)
    
    if not data.get('found'):
        return BetAnalysis(
            sport=bet.sport,
            player_name=bet.player_name,
            prop_description=f"{bet.prop_type} {bet.operator} {bet.line}",
            confidence_score=50,
            risk_level="High Risk",
            win_probability="55%",
            insights=["Player data unavailable."],
            advanced_stats=AdvancedStats(
                expected_minutes="-", avg_vs_opponent=0.0, usage_rate_change="-",
                matchup_difficulty="-", home_away_split="-", injury_status="-",
                days_rest="-", game_tempo="-", opponent_defense_rank="-", line_movement="-"
            ),
            market_insights=MarketInsights(
                best_line="-", best_book_logo="-", market_disagreement="-", books_range="-",
                open_vs_current="-", movement_badge="-", movement_graph=[],
                vegas_edge="-", market_pressure="-", hit_rate="-"
            ),
            last_10_graph=GraphData(labels=[], values=[], trend_line=bet.line)
        )

    adv_raw = data['advanced']
    logs = data['graph_data']
    season_avg = data['season_avg']
    market_raw = data['market']
    
    score = 70 
    last_5_avg = sum(logs[-5:]) / 5 if logs else 0
    
    # 1. Performance
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

    # 2. Context
    if adv_raw.get('matchup_difficulty') == "Great": score += 10
    elif adv_raw.get('matchup_difficulty') == "Poor": score -= 15
    
    # 3. Injury
    inj_status = adv_raw.get('injury_status', '').lower()
    injury_warning = None
    if "out" in inj_status or "ir" in inj_status or "inactive" in inj_status:
        score = 10 
        injury_warning = "WARNING: Player is reported as OUT."
    elif "questionable" in inj_status or "doubtful" in inj_status:
        score -= 25
        injury_warning = "Player status is Questionable/Doubtful."

    score = min(99, max(10, score))

    if score >= 90: risk = "Amazing"
    elif score >= 80: risk = "Strong"
    elif score >= 70: risk = "Moderate"
    elif score >= 60: risk = "Risky"
    else: risk = "High Risk"

    '''
    # CALCULATE INDIVIDUAL WIN PROBABILITY 
    # Formula: Base 35% + (Score scaled to 40%)
    # Score 99 -> 75% Win Prob
    # Score 50 -> 55% Win Prob
    # Score 10 -> 39% Win Prob
    '''
    prob_decimal = 0.35 + ((score / 100) * 0.40)
    prob_str = f"{int(prob_decimal * 100)}%"

    insights = []
    if injury_warning: insights.append(injury_warning)
    
    if "35+" in adv_raw.get('expected_minutes', ''):
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

    rank_str = ''.join(filter(str.isdigit, adv_raw.get('opponent_defense_rank', '')))
    if rank_str and int(rank_str) > 20:
        insights.append("Facing a team with a below average defense.")
    elif rank_str and int(rank_str) < 10:
        insights.append("Facing a top-tier defense (Tough Matchup).")

    return BetAnalysis(
        sport=bet.sport,
        player_name=data['name'],
        prop_description=f"{bet.prop_type} {bet.operator} {bet.line}",
        confidence_score=score,
        risk_level=risk,
        win_probability=prob_str,
        insights=insights,
        advanced_stats=AdvancedStats(**adv_raw),
        market_insights=MarketInsights(**market_raw),
        last_10_graph=GraphData(
            labels=[f"G{i+1}" for i in range(len(logs))],
            values=logs,
            trend_line=bet.line
        )
    )