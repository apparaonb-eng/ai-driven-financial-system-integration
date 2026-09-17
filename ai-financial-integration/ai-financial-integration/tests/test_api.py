"""
Basic smoke tests for the AI-Driven Financial System Integration base project.

Run with:  pytest
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_accounts_seeded():
    response = client.get("/accounts/")
    assert response.status_code == 200
    accounts = response.json()
    assert len(accounts) >= 2


def test_create_transaction_auto_categorized():
    accounts = client.get("/accounts/").json()
    account_id = accounts[0]["id"]

    response = client.post(
        "/transactions/",
        json={
            "account_id": account_id,
            "description": "Trader Joe's grocery run",
            "amount": -42.10,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["category"] in ("Groceries", "Uncategorized")


def test_fraud_scan():
    accounts = client.get("/accounts/").json()
    account_id = accounts[0]["id"]

    response = client.post(f"/ai/fraud-scan/{account_id}")
    assert response.status_code == 200
    data = response.json()
    assert "flagged_transactions" in data


def test_category_summary():
    accounts = client.get("/accounts/").json()
    account_id = accounts[0]["id"]

    response = client.get(f"/ai/summary/{account_id}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
