"""
AI Fraud / Anomaly Detector
----------------------------
Uses an Isolation Forest, trained per-account on that account's own
transaction history, to flag transactions that look statistically unusual.

Features used per transaction:
  - amount (absolute value; large or unusual amounts stand out)
  - hour of day (0-23; transactions at unusual hours stand out)
  - rolling count of transactions in the preceding 24h (bursts stand out)

This is deliberately simple and explainable, appropriate for a base project.
In production you'd enrich this with merchant risk data, geolocation,
device fingerprinting, velocity checks across accounts, etc.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Sequence

import numpy as np
from sklearn.ensemble import IsolationForest

MIN_TRANSACTIONS_FOR_MODEL = 10
DEFAULT_CONTAMINATION = 0.08  # assume ~8% of transactions could be anomalous


def _build_features(transactions: Sequence) -> np.ndarray:
    """
    transactions: sequence of objects with .amount and .timestamp attributes,
    sorted by timestamp ascending.
    """
    timestamps = [t.timestamp for t in transactions]
    features = []

    for i, tx in enumerate(transactions):
        amount = abs(tx.amount)
        hour = tx.timestamp.hour

        window_start = tx.timestamp - timedelta(hours=24)
        rolling_count = sum(1 for ts in timestamps[:i] if ts >= window_start)

        features.append([amount, hour, rolling_count])

    return np.array(features, dtype=float)


def detect_anomalies(transactions: Sequence, threshold: float = -0.1) -> dict:
    """
    Runs anomaly detection over a list of transactions for a single account.

    Returns a dict: {transaction_id: anomaly_score}, only for transactions
    whose score is below `threshold` (more negative = more anomalous).
    """
    if len(transactions) < MIN_TRANSACTIONS_FOR_MODEL:
        # Not enough history for a meaningful model. Fall back to a simple
        # statistical rule: flag amounts > 3 std-dev from the account's mean.
        amounts = np.array([abs(t.amount) for t in transactions], dtype=float)
        if len(amounts) < 2 or amounts.std() == 0:
            return {}
        z_scores = (amounts - amounts.mean()) / amounts.std()
        return {
            tx.id: float(z)
            for tx, z in zip(transactions, z_scores)
            if z > 3.0
        }

    ordered = sorted(transactions, key=lambda t: t.timestamp)
    X = _build_features(ordered)

    model = IsolationForest(
        contamination=DEFAULT_CONTAMINATION,
        random_state=42,
        n_estimators=100,
    )
    model.fit(X)
    scores = model.decision_function(X)  # lower = more anomalous

    flagged = {
        tx.id: float(score)
        for tx, score in zip(ordered, scores)
        if score < threshold
    }
    return flagged
