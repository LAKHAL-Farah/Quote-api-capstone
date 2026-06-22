import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


DATABASE_URL = os.getenv("DATABASE_URL", 
    "postgresql://quoteuser:quotepass@localhost:5432/quotes")

# Object that knows how to connect to the db
engine = create_engine(DATABASE_URL)
# Session = singld conversation with db
# this does not create a session but it makes a factory for creating new sessions
SessionLocal= sessionmaker(autocommit=False, autoflush=False, bind=engine)
# every table = class that inherits from Base
Base = declarative_base()

# generator function that will create a new db session for each request and then close it when the request is done

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
