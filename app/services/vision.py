import base64
import json
from openai import AsyncOpenAI
from app.config import settings
from app.schemas import ExtractedBet

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def extract_bets_from_image(image_bytes: bytes) -> list[ExtractedBet]:
    # Encode image
    base64_image = base64.b64encode(image_bytes).decode('utf-8')

    system_prompt = """
    You are a sports betting OCR engine. Analyze the betting slip image.
    Extract every player prop bet.
    Return a STRICT JSON object with a key 'bets' containing a list.
    Each item must have: 
    - player_name (string)
    - sport (guess based on context, e.g. NBA, NFL)
    - prop_type (Points, Rebounds, Assists, etc.)
    - line (number, e.g. 22.5)
    - operator (Over or Under. If 'Higher' use Over, if 'Lower' use Under).
    """

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user", 
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        response_format={"type": "json_object"}
    )

    data = json.loads(response.choices[0].message.content)
    # Convert raw dicts to Pydantic models
    return [ExtractedBet(**bet) for bet in data.get("bets", [])]