from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.ai.categorizer import categorizer

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", response_model=models.TransactionOut)
def create_transaction(payload: models.TransactionCreate, db: Session = Depends(get_db)):
    account = db.query(models.Account).get(payload.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if payload.category:
        # Manually labeled transaction -- trust the user, useful as future
        # training data for the categorizer.
        category, source = payload.category, "manual"
    else:
        category, source = categorizer.predict(payload.description)

    tx = models.Transaction(
        account_id=payload.account_id,
        description=payload.description,
        amount=payload.amount,
        timestamp=payload.timestamp or datetime.utcnow(),
        category=category,
        category_source=source,
    )
    db.add(tx)

    account.balance += payload.amount
    db.add(account)

    db.commit()
    db.refresh(tx)
    return tx


@router.get("/", response_model=list[models.TransactionOut])
def list_transactions(
    account_id: Optional[int] = None, db: Session = Depends(get_db)
):
    query = db.query(models.Transaction)
    if account_id is not None:
        query = query.filter(models.Transaction.account_id == account_id)
    return query.order_by(models.Transaction.timestamp.desc()).all()
