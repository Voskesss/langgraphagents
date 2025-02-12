# LangChain Agents Project

Dit project gebruikt LangChain voor het opzetten van AI agents. Het project draait volledig lokaal en maakt gebruik van de open-source versie van LangChain.

## Setup

1. Activeer de virtual environment:
```bash
source venv/bin/activate
```

2. Installeer de dependencies:
```bash
pip install -r requirements.txt
```

3. Maak een `.env` file aan met je API keys:
```bash
OPENAI_API_KEY=your_api_key_here
```

## Project Structuur
- `agents/`: Directory met agent implementaties
- `tools/`: Custom tools voor de agents
- `.env`: Environment variables (niet in git)
- `requirements.txt`: Project dependencies
