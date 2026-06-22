from app.database import SessionLocal ,engine,Base
from app.models import Quote

SEED_DATA=[
        {"text": "Talk is cheap. Show me the code.", "author": "Linus Torvalds", "category": "programming"},
    {"text": "Premature optimization is the root of all evil.", "author": "Donald Knuth", "category": "programming"},
    {"text": "The only way to do great work is to love what you do.", "author": "Steve Jobs", "category": "motivation"},
    {"text": "Simplicity is the soul of efficiency.", "author": "Austin Freeman", "category": "design"},
    {"text": "Make it work, make it right, make it fast.", "author": "Kent Beck", "category": "programming"},

]


def seed():
    Base.metadata.create_all(bind=engine)
    db=SessionLocal()
    try:
        existing_count=db.query(Quote).count()
        if existing_count > 0 :
            print(f"Database already has {existing_count} quotes - skippo,g seed.")
            return
        for entry in SEED_DATA:
            db.add(Quote(**entry))
        db.commit()
        print(f"seeded{len(SEED_DATA)} quotes.")
    finally:
        db.close()


if __name__== "__main__":
    seed()