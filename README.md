# Sheikh Haseeb — AI/ML Engineer Portfolio

Python portfolio built with **FastAPI**, **Jinja2**, **Tailwind CSS**, and **LangChain RAG** chatbot.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-ai.txt
bash scripts/copy_assets.sh
cp .env.example .env   # add GOOGLE_API_KEY + GROQ_API_KEY or set LLM_PROVIDER=gemini
PYTHONPATH=. python scripts/build_index.py
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000

## Health check

http://localhost:8000/api/health

## Project structure

See [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) for architecture and phases.

## Content updates

Edit `app/data/portfolio.json` then restart the dev server.

## Deploy

Render configuration is in `render.yaml`. Set `GROQ_API_KEY` or `GOOGLE_API_KEY` in Render environment variables.

## License

Personal portfolio — © Sheikh Haseeb
