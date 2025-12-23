import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.vision import extract_bets_from_image
from app.services.analyzer import analyze_single_bet
from app.schemas import ParlayResponse

router = APIRouter()

@router.post("/analyze-slip", response_model=ParlayResponse)
async def analyze_slip(file: UploadFile = File(...)):
    # 1. Validate File
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")
    
    image_bytes = await file.read()
    
    try:
        # 2. AI Vision Extraction
        extracted_bets = await extract_bets_from_image(image_bytes)
        
        if not extracted_bets:
            raise HTTPException(400, "Could not detect any bets in the image.")

        # 3. Parallel Processing (Fast!)
        # We analyze all bets in the slip at the same time
        analysis_tasks = [analyze_single_bet(bet) for bet in extracted_bets]
        analyzed_bets = await asyncio.gather(*analysis_tasks)
        
        # 4. Calculate Overall Score
        avg_score = sum(b.confidence_score for b in analyzed_bets) // len(analyzed_bets)
        
        return ParlayResponse(
            overall_parlay_score=avg_score,
            bets=analyzed_bets
        )

    except Exception as e:
        # Log error in production
        print(f"Error: {e}")
        raise HTTPException(500, f"Analysis failed: {str(e)}")