# ParlAi Backend 🚀

ParlAi is an intelligent sports betting assistant API. It uses Computer Vision (OCR) to extract bets from user screenshots and leverages real-time NBA and NFL data to generate confidence scores, risk analysis, and deep statistical insights.

The system is optimized for speed, reliability, and accuracy, with a fail-safe architecture that guarantees valid responses even when real-world data is unavailable.

---

## 🌟 Key Features

### 📷 AI Vision Extraction
- Uses **GPT-4o Vision** to parse betting slips (PrizePicks, FanDuel, etc.)
- Handles:
  - Complex layouts
  - Combo bets ("Luka + Kyrie")
  - Multi-prop slips
  - Diverse sportsbook formats

### 🏀 Real-Time NBA Data
- Direct integration with `nba_api`
- Fetches:
  - Game logs
  - Home/away splits
  - Roster & injury status
  - Defensive rankings

### 🏈 Real-Time NFL Data
- Powered by `nfl_data_py`
- Fetches:
  - Weekly stats
  - Fantasy scores
  - Injury reports
  - Player usage metrics

### ⚡ High Performance
- Warm Startup: Preloads sports databases on boot
- Parallel execution using `asyncio` and `ThreadPoolExecutor`
- Response time optimized from ~40s → ~5–8s

### 🛡️ Fail-Safe Architecture
- Sanity checks for corrupted or misleading data
- Automatic simulation fallback for rookies or missing stats
- Guarantees API never returns broken or empty responses

### 🚑 Smart Injury Logic
- Automatically penalizes confidence score for:
  - Questionable players
  - Out players
- Prevents unsafe betting recommendations

---

## 🛠️ Tech Stack

| Component | Technology |
|---------|------------|
| Framework | FastAPI (Python 3.10+) |
| AI Vision | OpenAI GPT-4o |
| NBA Data | nba_api |
| NFL Data | nfl_data_py |
| Odds Data | SportsGameOdds |
| Search Fallback | DuckDuckGo |
| Data Processing | Pandas, NumPy |
| Async Engine | asyncio, concurrent.futures |

---

## 📂 Project Structure

```
parlai_backend/
├── .env # API Keys (OpenAI, SGO)
├── requirements.txt # Python Dependencies
├── README.md # Documentation
├── app/
│ ├── init.py
│ ├── main.py # App Entry Point & Startup Logic
│ ├── config.py # Configuration Settings
│ ├── schemas.py # Pydantic Response Models
│ ├── api/
│ │ ├── init.py
│ │ └── routes.py # API Endpoints
│ └── services/
│ ├── init.py
│ ├── vision.py # OCR Agent (Image → JSON)
│ ├── sgo_client.py # Data Orchestrator
│ ├── nba_service.py # NBA Official Data Fetcher
│ ├── nfl_service.py # NFL Official Data Fetcher
│ ├── rank_service.py # Defensive Rankings
│ ├── search_agent.py # Web Search Fallback
│ └── analyzer.py # Scoring Engine
```


---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.9+
- OpenAI API Key
- SportsGameOdds API Key

---

### 2. Installation

```bash
# Clone repository
git clone https://github.com/your-username/parlai-backend.git
cd parlai-backend

# Create virtual environment
python -m venv .venv

# Activate environment
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a .env file in the root directory:
```
OPENAI_API_KEY=sk-proj-your-openai-key-here
SPORTSGAMEODDS_API_KEY=your-sgo-key-here
```
4. Run the Server
uvicorn app.main:app --reload


Server will start at:
```
http://127.0.0.1:8000
```
⚠️ First startup may take 10–15 seconds due to NFL dataset download. Subsequent requests are fast.