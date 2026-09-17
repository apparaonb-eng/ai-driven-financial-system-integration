"""
AI-Driven Financial System Integration - FastAPI entrypoint.

On startup:
  1. Creates database tables if they don't exist.
  2. Seeds sample accounts/transactions if the DB is empty.
  3. Trains the AI categorizer on whatever labeled data is available.

Run with:  uvicorn app.main:app --reload
Docs at:   http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI

from app.database import Base, engine, SessionLocal
from app import models, seed
from app.ai.categorizer import categorizer
from app.routers import accounts, transactions, ai_insights

app = FastAPI(
    title="AI-Driven Financial System Integration",
    description="A base project integrating AI-powered categorization and "
                "fraud detection into a simple financial system.",
    version="0.1.0",
)

app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(ai_insights.router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed.seed_database(db)

        all_tx = db.query(models.Transaction).all()
        descriptions = [t.description for t in all_tx]
        labels = [t.category for t in all_tx]
        categorizer.train(descriptions, labels)
    finally:
        db.close()


@app.get("/", tags=["health"])
def root():
    return {
        "status": "ok",
        "message": "AI-Driven Financial System Integration is running.",
        "docs": "/docs",
    }
