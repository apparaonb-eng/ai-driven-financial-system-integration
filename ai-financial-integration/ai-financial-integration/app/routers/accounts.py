from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/", response_model=models.AccountOut)
def create_account(payload: models.AccountCreate, db: Session = Depends(get_db)):
    account = models.Account(**payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/", response_model=list[models.AccountOut])
def list_accounts(db: Session = Depends(get_db)):
    return db.query(models.Account).all()


@router.get("/{account_id}", response_model=models.AccountOut)
def get_account(account_id: int, db: Session = Depends(get_db)):
    account = db.query(models.Account).get(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account
