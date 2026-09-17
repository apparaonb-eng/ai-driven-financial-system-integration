from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.ai.categorizer import categorizer
from app.ai.fraud_detector import detect_anomalies

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/fraud-scan/{account_id}", response_model=models.FraudScanResult)
def fraud_scan(account_id: int, threshold: float = -0.1, db: Session = Depends(get_db)):
    account = db.query(models.Account).get(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    transactions = (
        db.query(models.Transaction)
        .filter(models.Transaction.account_id == account_id)
        .all()
    )

    flagged_scores = detect_anomalies(transactions, threshold=threshold)

    for tx in transactions:
        if tx.id in flagged_scores:
            tx.is_flagged_fraud = True
            tx.fraud_score = flagged_scores[tx.id]
            db.add(tx)

    db.commit()

    return models.FraudScanResult(
        account_id=account_id,
        scanned_transactions=len(transactions),
        flagged_transactions=list(flagged_scores.keys()),
        threshold=threshold,
    )


@router.get("/summary/{account_id}", response_model=list[models.CategorySummary])
def category_summary(account_id: int, db: Session = Depends(get_db)):
    account = db.query(models.Account).get(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    transactions = (
        db.query(models.Transaction)
        .filter(models.Transaction.account_id == account_id)
        .all()
    )

    totals = defaultdict(lambda: [0.0, 0])
    for tx in transactions:
        if tx.amount < 0:  # only count spending, not incoming credits
            totals[tx.category][0] += abs(tx.amount)
            totals[tx.category][1] += 1

    return [
        models.CategorySummary(category=cat, total_spent=round(total, 2), transaction_count=count)
        for cat, (total, count) in sorted(totals.items(), key=lambda kv: -kv[1][0])
    ]


@router.post("/retrain")
def retrain(db: Session = Depends(get_db)):
    transactions = db.query(models.Transaction).all()
    descriptions = [t.description for t in transactions]
    labels = [t.category for t in transactions]
    report = categorizer.train(descriptions, labels)
    return report
