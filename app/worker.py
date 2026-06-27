import os
import random

from celery import Celery
from app.database import SessionLocal
from app.models import Quote

celery_app= Celery(
    "quote_worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
)



@celery_app.task
def generate_digest(num_quotes: int=5):
    db=SessionLocal()
    try:
        quotes=db.query(Quote).all()
        if not quotes:
            return[]
        sample_size= min(num_quotes, len(quotes))
        sample=random.sample(quotes,sample_size)
        return [
            {"id":q.id, "text": q.text, "author": q.author}
            for q in sample
        ]
    finally:
        db.close()