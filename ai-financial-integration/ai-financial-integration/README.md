# AI-Driven Financial System Integration

A simple, runnable **base/starter project** demonstrating how an AI layer can be
integrated into a financial system. It provides:

- A minimal financial core: **Accounts** and **Transactions** (SQLite via SQLAlchemy).
- An **AI Categorizer**: automatically classifies transactions into categories
  (e.g., Groceries, Utilities, Salary, Entertainment) using a Naive Bayes text
  classifier (scikit-learn), with a rule-based fallback when the model is
  under-trained.
- An **AI Fraud/Anomaly Detector**: flags suspicious transactions using an
  Isolation Forest model trained on each account's own transaction history
  (amount, hour of day, frequency).
- A **FastAPI** REST API tying it all together, with interactive docs at `/docs`.
- A **seed script** that generates realistic sample data so the AI features
  have something to learn from immediately.

This is intentionally a *foundation* you can extend — swap in a real bank/
payment gateway integration, a production-grade model, a proper database, auth,
etc.

## Project Structure

```
ai-financial-integration/
├── app/
│   ├── main.py               # FastAPI app entrypoint
│   ├── database.py           # SQLAlchemy engine/session setup
│   ├── models.py             # ORM models (Account, Transaction) + Pydantic schemas
│   ├── seed.py                # Generates sample accounts/transactions
│   ├── ai/
│   │   ├── categorizer.py    # AI transaction categorization
│   │   └── fraud_detector.py # AI anomaly / fraud detection
│   └── routers/
│       ├── accounts.py       # /accounts endpoints
│       ├── transactions.py   # /transactions endpoints (auto-categorized)
│       └── ai_insights.py    # /ai endpoints (fraud scan, retrain, summary)
├── tests/
│   └── test_api.py           # Basic smoke tests
├── requirements.txt
└── README.md
```

## Quick Start

```bash
# 1. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the API (auto-creates SQLite DB + seeds sample data on first run)
uvicorn app.main:app --reload

# 4. Open interactive API docs
# http://127.0.0.1:8000/docs
```

## Key Endpoints

| Method | Path                              | Description                                      |
|--------|-----------------------------------|---------------------------------------------------|
| POST   | `/accounts/`                      | Create an account                                  |
| GET    | `/accounts/`                      | List accounts                                      |
| POST   | `/transactions/`                  | Create a transaction (auto-categorized by AI)      |
| GET    | `/transactions/`                  | List transactions (optional `account_id` filter)   |
| GET    | `/ai/summary/{account_id}`        | AI-generated spending summary by category          |
| POST   | `/ai/fraud-scan/{account_id}`     | Run fraud/anomaly detection over an account         |
| POST   | `/ai/retrain`                     | Retrain the categorizer on current transaction data |

## How the AI Pieces Work (in plain terms)

1. **Categorizer** (`app/ai/categorizer.py`)
   - Trains a `MultinomialNB` text classifier over transaction descriptions.
   - Falls back to keyword-based rules until enough labeled data exists.
   - Re-trainable at any time via `POST /ai/retrain` as more data accumulates.

2. **Fraud Detector** (`app/ai/fraud_detector.py`)
   - Builds a small `IsolationForest` per account using amount, hour-of-day,
     and rolling transaction frequency as features.
   - Flags transactions with an anomaly score beyond a configurable threshold.
   - Designed to be re-run periodically (e.g., via a cron job or message queue
     in a production system).

## Extending This Base Project

- Swap SQLite for PostgreSQL by changing `DATABASE_URL` in `app/database.py`.
- Replace the seed/simulated accounts with a real core-banking or payment
  gateway integration (Plaid, Stripe, SWIFT, etc.).
- Replace Naive Bayes / Isolation Forest with more advanced models (transformer
  embeddings for categorization, gradient-boosted models or deep learning for
  fraud) once you have real historical data.
- Add authentication (OAuth2/JWT) before exposing this beyond local use.
