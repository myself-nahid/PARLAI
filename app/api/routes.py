import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.vision import extract_bets_from_image
from app.services.analyzer import analyze_single_bet
from app.schemas import ParlayResponse

router = APIRouter()

@router.post("/analyze-slip", response_model=ParlayResponse)
async def analyze_slip(file: UploadFile = File(...)):
    print(f"Received file: {file.filename}, type: {file.content_type}")
    
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")
    
    image_bytes = await file.read()
    
    try:
        extracted_bets = await extract_bets_from_image(image_bytes)
        
        print(f"Extracted Bets: {extracted_bets}")

        if not extracted_bets:
            raise HTTPException(400, "Could not detect any bets. Try a clearer image.")

        analysis_tasks = [analyze_single_bet(bet) for bet in extracted_bets]
        analyzed_bets = await asyncio.gather(*analysis_tasks)
        
        avg_score = sum(b.confidence_score for b in analyzed_bets) // len(analyzed_bets) if analyzed_bets else 0
        
        return ParlayResponse(
            overall_parlay_score=avg_score,
            bets=analyzed_bets
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc() 
        raise HTTPException(500, f"Server Error: {str(e)}")