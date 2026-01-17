import base64
import json
import re
from openai import AsyncOpenAI
from app.config import settings
from app.schemas import ExtractedBet

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

def clean_json_string(json_str: str) -> str:
    pattern = r"^```json\s*(.*?)\s*```$"
    match = re.search(pattern, json_str, re.DOTALL)
    if match: return match.group(1)
    return json_str

async def extract_bets_from_image(image_bytes: bytes) -> list[ExtractedBet]:
    base64_image = base64.b64encode(image_bytes).decode('utf-8')

    system_prompt = """
    You are a sports betting data extractor.
    Your job is to extract EVERY SINGLE BET visible in the image.
    
    CRITICAL RULES:
    1. Scan the image from Top to Bottom.
    2. Do NOT summarize. Do NOT skip any rows.
    3. If there are 5 players listed, you must return 5 extracted bets.
    4. For "Combo Bets" (e.g., "Player A + Player B"), keep the names together in 'player_name'.
    
    Extraction Fields:
    - player_name: Exact name(s) shown.
    - sport: "NBA", "NFL", "NHL", "MLB" (Guess based on stat type if not shown).
    - prop_type: The stat category (e.g. "Points", "Rebounds", "PRA", "Fantasy Score").
    - line: The number (e.g. 22.5). Convert to float.
    - operator: "Over" or "Under". (Arrows Up/Green = Over, Arrows Down/Red = Under).
    
    Return STRICT JSON format:
    {
      "bets": [
        {"player_name": "...", "sport": "...", "prop_type": "...", "line": 0.0, "operator": "..."}
      ]
    }
    """

    try:
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
            response_format={"type": "json_object"},
            temperature=0.0 
        )

        raw_content = response.choices[0].message.content
        cleaned_content = clean_json_string(raw_content)
        data = json.loads(cleaned_content)
        bets_data = data.get("bets", [])
        
        extracted = []
        for b in bets_data:
            # Data cleaning
            line_val = b.get('line', 0.0)
            if isinstance(line_val, str):
                clean_num = re.sub(r"[^0-9.]", "", line_val)
                line_val = float(clean_num) if clean_num else 0.0
                
            extracted.append(ExtractedBet(
                player_name=b.get('player_name', 'Unknown'),
                sport=b.get('sport', 'NBA'),
                prop_type=b.get('prop_type', 'Points'),
                line=line_val,
                operator=b.get('operator', 'Over')
            ))
            
        return extracted

    except Exception as e:
        print(f"Vision Service Error: {e}")
        return []