import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    SGO_API_KEY = os.getenv("SPORTSGAMEODDS_API_KEY")
    SGO_BASE_URL = "https://api.sportsgameodds.com/v2"

settings = Settings()