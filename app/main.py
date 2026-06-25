from fastapi import FastAPI,Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import random
import socket 


from app.database import get_db
from app.models import Quote
from app.schemas import QuoteCreate, QuoteRead


app = FastAPI(title="Quote API", description="A simple API to manage quotes", version="1.0.0")



@app.get("/health")
def health_check(db:Session=Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status=f"database connection failed: {e}"

    return{
        "status":"ok" if db_status=="ok" else "degraded",
        "database":db_status,
        "hostname":socket.gethostname()
    }



@app.get("/quote/random", response_model=QuoteRead)
def get_random_quote(db:Session = Depends(get_db)):
    count = db.query(Quote).count()
    if count == 0:
        raise HTTPException(status_code=404, detail="No quotes found")
    random_offset = random.randint(0, count - 1)
    quote = db.query(Quote).offset(random_offset).first()
    return quote
    


@app.get("/quote/{quote_id}", response_model=QuoteRead)
def get_quote(quote_id:int, db:Session=Depends(get_db)):
    quote= db.query(Quote).filter(Quote.id==quote_id).first()
    if quote is None:
        raise HTTPException(status_code=404,
                            detail=f"Quote with id {quote_id} not found")
    return quote


@app.post('/quote', response_model=QuoteRead , status_code=201)
def create_quote(quote_in:QuoteCreate,db:Session=Depends(get_db)):
    quote = Quote(**quote_in.model_dump())
    db.add(quote)
    db.commit()
    db.refresh(quote)
    return quote


@app.delete("/quote/{quote_id}" ,status_code=204)
def delete_quote(quote_id:int, db:Session=Depends(get_db)):
    quote= db.query(Quote).filter(Quote.id==quote_id).first()
    if quote is None:
        raise HTTPException(status_code=404, detail=f"Quote with id {quote_id} not found")
    
    db.delete(quote)
    db.commit()# another comment
