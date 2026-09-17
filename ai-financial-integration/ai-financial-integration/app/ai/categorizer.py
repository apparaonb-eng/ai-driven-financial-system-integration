"""
AI Transaction Categorizer
---------------------------
Classifies a transaction's free-text description into a spending category.

Strategy:
- Primary: a Multinomial Naive Bayes text classifier (scikit-learn) trained
  on previously-labeled transactions in the database.
- Fallback: simple keyword/rule matching, used when the model hasn't been
  trained yet or isn't confident, so the system is useful from day one
  even with little data.

Call `train()` whenever you want the model to (re)learn from current data
(e.g., after a batch of manually-labeled transactions is added).
"""
from __future__ import annotations

from typing import Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

# Minimum number of labeled examples (across at least 2 categories) before
# the ML model is trusted over the rule-based fallback.
MIN_TRAINING_EXAMPLES = 8

RULE_KEYWORDS = {
    "Groceries": ["grocery", "supermarket", "market", "walmart", "kroger", "foods"],
    "Utilities": ["electric", "water bill", "gas bill", "utility", "internet", "phone bill"],
    "Salary": ["salary", "payroll", "paycheck", "direct deposit"],
    "Entertainment": ["netflix", "spotify", "cinema", "movie", "game", "concert"],
    "Dining": ["restaurant", "cafe", "coffee", "starbucks", "pizza", "diner"],
    "Transport": ["uber", "lyft", "gas station", "fuel", "transit", "parking"],
    "Rent/Mortgage": ["rent", "mortgage", "landlord"],
    "Healthcare": ["pharmacy", "clinic", "hospital", "doctor", "dental"],
    "Shopping": ["amazon", "mall", "store", "shop"],
    "Transfer": ["transfer", "wire", "zelle", "venmo"],
}


def _rule_based_category(description: str) -> str:
    text = description.lower()
    for category, keywords in RULE_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "Uncategorized"


class TransactionCategorizer:
    def __init__(self) -> None:
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.model: Optional[MultinomialNB] = None
        self.is_trained: bool = False

    def train(self, descriptions: list[str], labels: list[str]) -> dict:
        """
        Train (or retrain) the Naive Bayes classifier.
        Returns a small report dict describing what happened.
        """
        usable_pairs = [
            (d, l) for d, l in zip(descriptions, labels) if l and l != "Uncategorized"
        ]

        if len(usable_pairs) < MIN_TRAINING_EXAMPLES or len({l for _, l in usable_pairs}) < 2:
            self.is_trained = False
            return {
                "trained": False,
                "reason": f"Need at least {MIN_TRAINING_EXAMPLES} labeled examples "
                          f"across 2+ categories. Currently have {len(usable_pairs)}.",
                "examples_used": len(usable_pairs),
            }

        texts = [d for d, _ in usable_pairs]
        cats = [l for _, l in usable_pairs]

        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        X = self.vectorizer.fit_transform(texts)

        self.model = MultinomialNB()
        self.model.fit(X, cats)
        self.is_trained = True

        return {"trained": True, "examples_used": len(usable_pairs)}

    def predict(self, description: str) -> tuple[str, str]:
        """
        Returns (category, source) where source is "model" or "rule".
        """
        if self.is_trained and self.model is not None and self.vectorizer is not None:
            X = self.vectorizer.transform([description])
            probs = self.model.predict_proba(X)[0]
            best_idx = probs.argmax()
            confidence = probs[best_idx]
            predicted = self.model.classes_[best_idx]

            if confidence >= 0.45:
                return predicted, "model"

        return _rule_based_category(description), "rule"


# A single shared instance used across the app (simple in-memory singleton).
categorizer = TransactionCategorizer()
