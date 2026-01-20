import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.vision import extract_bets_from_image
from app.services.analyzer import analyze_single_bet
from app.schemas import ParlayResponse

router = APIRouter()

@router.post("/analyze-slip", response_model=ParlayResponse)
async def analyze_slip(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")
    
    image_bytes = await file.read()
    
    try:
        extracted_bets = await extract_bets_from_image(image_bytes)
        
        if not extracted_bets:
            raise HTTPException(400, "Could not detect any bets.")

        # Parallel Analysis
        analysis_tasks = [analyze_single_bet(bet) for bet in extracted_bets]
        analyzed_bets = await asyncio.gather(*analysis_tasks)
        
        # 1. Overall Parlay Score
        total_score = sum(b.confidence_score for b in analyzed_bets)
        avg_score = total_score // len(analyzed_bets) if analyzed_bets else 0
        
        # 2. Weakest Leg (Min Score)
        weakest_bet = min(analyzed_bets, key=lambda x: x.confidence_score)
        weakest_str = f"{weakest_bet.player_name}: {weakest_bet.prop_description}"
        
        # 3. Win Reality Probability
        # Client Scale: 40%+ Stable, 25-39 Balanced, 15-24 Fragile, <15 Longshot
        parlay_prob_decimal = 1.0
        
        for b in analyzed_bets:
            # Map Score 0-100 to Win Prob 0.35 - 0.75 (Realistic individual prop range)
            prob = 0.35 + ((b.confidence_score / 100) * 0.40)
            parlay_prob_decimal *= prob
            
        win_pct_val = int(parlay_prob_decimal * 100)
        
        if win_pct_val >= 40: win_label = "Stable"
        elif win_pct_val >= 25: win_label = "Balanced"
        elif win_pct_val >= 15: win_label = "Fragile"
        else: win_label = "Longshot"
        
        return ParlayResponse(
            overall_parlay_score=avg_score,
            win_probability=f"{win_pct_val}%",
            win_label=win_label,
            weakest_leg=weakest_str,
            bets=analyzed_bets
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Server Error: {str(e)}")