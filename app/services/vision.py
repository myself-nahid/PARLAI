import base64
import json
import re
from openai import AsyncOpenAI
from app.config import settings
from app.schemas import ExtractedBet

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

def clean_json_string(json_str: str) -> str:
    """Removes Markdown code formatting."""
    pattern = r"^```json\s*(.*?)\s*```$"
    match = re.search(pattern, json_str, re.DOTALL)
    if match: return match.group(1)
    return json_str

async def extract_bets_from_image(image_bytes: bytes) -> list[ExtractedBet]:
    print("--- 1. Processing Image ---")
    
    with open("debug_received_image.png", "wb") as f:
        f.write(image_bytes)
    print("-> Saved debug_received_image.png to project root. Check this file!")

    base64_image = base64.b64encode(image_bytes).decode('utf-8')

    system_prompt = """
    You are an AI that reads sports betting slips and stats screens. 
    Your goal is to extract a list of Player Props.
    
    LOOK FOR:
    - Player Names (e.g., "LeBron James", "G. Limon")
    - Numbers (e.g., "22.5", "10.5")
    - Indicators (Arrows, "Higher", "Lower", "Over", "Under", "More", "Less")

    INSTRUCTIONS:
    1. If you see a player name and a number near it, extract it as a bet.
    2. Infer 'operator': 
       - "Higher", "More", "Over", or Up Arrow (⬆) -> "Over"
       - "Lower", "Less", "Under", or Down Arrow (⬇) -> "Under"
       - If ambiguous, default to "Over".
    3. Infer 'sport': If unknown, guess based on the stats (e.g. Points -> NBA, Yards -> NFL).
    4. Return STRICT JSON: {"bets": [{ "player_name": "...", "sport": "...", "prop_type": "...", "line": 0.0, "operator": "..." }]}
    
    Even if the image is just a stats list, treat them as potential bets.
    """

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )

        raw_content = response.choices[0].message.content
        print(f"--- 2. Raw AI Response: {raw_content} ---")

        cleaned_content = clean_json_string(raw_content)
        data = json.loads(cleaned_content)
        bets_data = data.get("bets", [])
        
        extracted = []
        for b in bets_data:
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
        print(f"!!! Vision Service Error: {e}")
        return []