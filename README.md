# Travel Planner Assistant

A small FastAPI + Streamlit travel assistant that uses OpenAI tool-calling with weather-based chains:

- Current weather lookup
- Weather risk alerts
- Outfit advice
- Live LLM logs streamed to UI (then collapsed in an accordion)

## Tech Stack

- Backend: FastAPI
- UI: Streamlit
- LLM: OpenAI Chat Completions API
- Weather data: WeatherAPI
- Package manager: `uv`

## Project Structure

```text
.
├── app/
│   ├── agent.py           # LLM loop, tool routing, log callbacks
│   ├── config.py          # Environment-based settings
│   └── main.py            # FastAPI app + /chat and /chat/stream
├── prompt/
│   └── prompt.py          # System prompt + tool instructions
├── schema/
│   └── weather.py         # Pydantic schemas for weather/tool responses
├── tools/
│   ├── tools.py           # Primitive weather API tool
│   └── chains.py          # Risk alert and outfit chain functions
├── ui/
│   └── app.py             # Streamlit chat UI with quick actions/log accordion
└── pyproject.toml
```

## Prerequisites

1. Python 3.9+
2. `uv` installed

Install `uv` if needed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Setup

1. Install dependencies:

```bash
uv sync
```

2. Create `.env` in project root:

```bash
OPENAI_API_KEY=your_openai_key
WEATHER_API_KEY=your_weatherapi_key
```

Optional:

```bash
OPENAI_MODEL=gpt-4o-mini
```

## Run Locally

Start backend:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Start UI in another terminal:

```bash
uv run streamlit run ui/app.py
```

Open:

- UI: [http://localhost:8501](http://localhost:8501)
- Backend docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## API Endpoints

- `GET /` - Basic welcome response
- `POST /chat` - Standard chat response
  - Input: `{"message":"..."}`
  - Output: `{"answer":"...","used_tools":[...],"weather_location":"..."}`
- `POST /chat/stream` - SSE stream for live LLM logs + final result

## Current Behavior

- Quick-action pills appear only when backend confirms `get_current_weather` was used.
- Assistant logs are streamed live in UI, then shown under an accordion:
  - Label format: `Worked for X.X seconds`
- LLM/tool logs are also printed in backend terminal.

## Useful Dev Commands

```bash
# Lint
uv run ruff check .

# Format
uv run ruff format .

# Compile sanity check
uv run python -m compileall app ui tools schema prompt
```
