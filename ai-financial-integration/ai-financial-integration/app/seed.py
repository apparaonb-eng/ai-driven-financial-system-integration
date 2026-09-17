"""
Seeds the database with a couple of sample accounts and a batch of realistic,
pre-labeled transactions so the AI categorizer and fraud detector have data
to work with immediately after startup.
"""
import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app import models

SAMPLE_TRANSACTIONS = [
    ("Whole Foods Market purchase", -54.32, "Groceries"),
    ("Kroger grocery run", -88.10, "Groceries"),
    ("Electric utility bill", -120.00, "Utilities"),
    ("Internet bill - Comcast", -75.00, "Utilities"),
    ("Payroll direct deposit", 2500.00, "Salary"),
    ("Netflix subscription", -15.99, "Entertainment"),
    ("Spotify subscription", -9.99, "Entertainment"),
    ("Starbucks coffee", -6.75, "Dining"),
    ("Local pizza diner", -22.40, "Dining"),
    ("Uber ride downtown", -18.50, "Transport"),
    ("Shell gas station fill-up", -45.00, "Transport"),
    ("Monthly rent payment", -1450.00, "Rent/Mortgage"),
    ("CVS pharmacy purchase", -32.10, "Healthcare"),
    ("Amazon.com order", -63.20, "Shopping"),
    ("Venmo transfer to roommate", -40.00, "Transfer"),
    ("Walmart supermarket trip", -71.85, "Groceries"),
    ("Water utility bill", -40.00, "Utilities"),
    ("Cinema movie tickets", -28.00, "Entertainment"),
    ("Local cafe breakfast", -12.30, "Dining"),
    ("Lyft ride to airport", -35.75, "Transport"),
]


def seed_database(db: Session) -> None:
    if db.query(models.Account).count() > 0:
        return  # already seeded

    alice = models.Account(owner_name="Alice Johnson", account_type="checking", balance=0.0)
    bob = models.Account(owner_name="Bob Smith", account_type="checking", balance=0.0)
    db.add_all([alice, bob])
    db.commit()
    db.refresh(alice)
    db.refresh(bob)

    now = datetime.utcnow()

    for account in (alice, bob):
        for i, (desc, amount, category) in enumerate(SAMPLE_TRANSACTIONS):
            jittered_amount = round(amount * random.uniform(0.9, 1.1), 2)
            tx_time = now - timedelta(days=len(SAMPLE_TRANSACTIONS) - i, hours=random.randint(0, 23))
            tx = models.Transaction(
                account_id=account.id,
                description=desc,
                amount=jittered_amount,
                timestamp=tx_time,
                category=category,
                category_source="manual",
            )
            db.add(tx)
            account.balance += jittered_amount

        # Add one deliberately unusual transaction to demonstrate fraud detection
        odd_tx = models.Transaction(
            account_id=account.id,
            description="Unrecognized large purchase - electronics retailer",
            amount=-1875.00,
            timestamp=now - timedelta(hours=2),
            category="Shopping",
            category_source="manual",
        )
        db.add(odd_tx)
        account.balance += odd_tx.amount

        db.add(account)

    db.commit()
