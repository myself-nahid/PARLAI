import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    # For MVP, we will mock the stats, but ready for expansion
    USE_MOCK_STATS = True 

settings = Settings()