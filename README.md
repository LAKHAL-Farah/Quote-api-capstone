# Quote API

A FastAPI + PostgreSQL REST API for storing and retrieving quotes.

## Setup
1. python3 -m venv venv && source venv/bin/activate
2. pip install -r requirements-dev.txt
3. Create a Postgres database and user, set DATABASE_URL in .env (see .env.example)
4. python -m app.seed_quotes
5. uvicorn app.main:app --reload

## Endpoints
- GET /health
- GET /quote/random
- GET /quote/{id}
- POST /quote
- DELETE /quote/{id}

## Tests
pytest tests/ -v
