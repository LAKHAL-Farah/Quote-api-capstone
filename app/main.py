from fastapi import FastAPI,Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import random
import socket 
from app.cache import get_cached_quote, set_cached_quote, invalidate_quote_cache

from app.database import get_db
from app.models import Quote
from app.schemas import QuoteCreate, QuoteRead
from app.cache import r as redis_client
from app.worker import generate_digest
from celery.result import AsyncResult
from app.worker import celery_app


app = FastAPI(title="Quote API", description="A simple API to manage quotes", version="1.0.0")


def serialize_quote(quote: Quote):
    return {
        "id": quote.id,
        "text": quote.text,
        "author": quote.author,
        "category": quote.category,
        "created_at": quote.created_at.isoformat(),
    }


@app.get("/health")
def health_check(db:Session=Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status=f"database connection failed: {e}"


    try:
        redis_client.ping()
        redis_status="ok"
    except Exception as e:
        redis_status= f"error: {e}"


    overall_status= "ok" if db_status == "ok" and redis_status=="ok" else "degraded"

    return{
        "status":overall_status,
        "database":db_status,
        "redis": redis_status,
        "hostname":socket.gethostname()
    }



@app.get("/quote/random", response_model=QuoteRead)
def get_random_quote(db: Session = Depends(get_db)):
    count = db.query(Quote).count()

    if count == 0:
        raise HTTPException(status_code=404, detail="No quotes found")

    random_offset = random.randint(0, count - 1)

    quote = (
        db.query(Quote)
        .order_by(Quote.id)   
        .offset(random_offset)
        .first()
    )

    return quote


@app.get("/quote/{quote_id}", response_model=QuoteRead)
def get_quote(quote_id: int, db: Session = Depends(get_db)):

    cached = get_cached_quote(quote_id)
    if cached:
        return cached

    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if quote is None:
        raise HTTPException(status_code=404, detail=f"Quote with id {quote_id} not found")

    quote_dict = serialize_quote(quote)

    set_cached_quote(quote_id, quote_dict)

    return quote_dict


@app.post('/quote', response_model=QuoteRead, status_code=201)
def create_quote(quote_in: QuoteCreate, db: Session = Depends(get_db)):

    quote = Quote(**quote_in.model_dump())
    db.add(quote)
    db.commit()
    db.refresh(quote)
    db.expire_all()

    return serialize_quote(quote)

@app.delete("/quote/{quote_id}" ,status_code=204)
def delete_quote(quote_id:int, db:Session=Depends(get_db)):
    quote= db.query(Quote).filter(Quote.id==quote_id).first()
    if quote is None:
        raise HTTPException(status_code=404, detail=f"Quote with id {quote_id} not found")
    
    db.delete(quote)
    db.commit()# another comment
    invalidate_quote_cache(quote_id)



@app.put("/quote/{quote_id}", response_model=QuoteRead)
def update_quote(quote_id:int, quote_in: QuoteCreate, db: Session=Depends(get_db)):
    quote= db.query(Quote).filter(Quote.id== quote_id).first()

    if quote is None:
        raise HTTPException(status_code=404, detail=f"Quote {quote_id} not found")
    quote.text= quote_in.text
    quote.author=quote_in.author
    quote.category= quote_in.category
    db.commit()
    db.refresh(quote)
    invalidate_quote_cache(quote_id)
    return quote



@app.post("/digest/trigger")
def trigger_digest(num_quotes: int = 5):
    task = generate_digest.delay(num_quotes)
    return {
        "task_id": task.id,
        "status": "queued"
    }


@app.get("/digest/status/{task_id}")
def digest_status(task_id: str):
    task = AsyncResult(task_id, app=celery_app)

    if task.ready():
        return {
            "status": task.status,
            "result": task.result
        }

    return {
        "status": task.status,
        "result": None
    }