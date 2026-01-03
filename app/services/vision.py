import base64
import json
import re
from openai import AsyncOpenAI
from app.config import settings
from app.schemas import ExtractedBet

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def extract_bets_from_image(image_bytes: bytes) -> list[ExtractedBet]:
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    prompt = """
    Extract betting props from this image.
    Return JSON: {"bets": [{"player_name": "...", "sport": "NBA", "prop_type": "Points", "line": 22.5, "operator": "Over"}]}
    If line is missing, use 0.0. If operator is arrow up, use "Over".
    """

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        # Simple cleanup
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
            
        data = json.loads(content)
        return [ExtractedBet(**b) for b in data.get('bets', [])]
    except:
        return []