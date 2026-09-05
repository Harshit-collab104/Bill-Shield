"""
Tests for subscription detection and normal subscription scenarios.
"""

from datetime import date
from backend.models.schemas import Transaction
from backend.services.subscriptions import detect_recurring_payments
from backend.services.detection import detect_price_changes


def test_recurring_subscription_detected():
    """Test 1: Verify recurring subscription is correctly detected from transaction history."""
    txs = [
        Transaction(
            transaction_id="T001",
            date=date(2026, 1, 5),
            merchant="Spotify",
            amount=119.0,
            category="Subscription",
            payment_method="AutoPay",
            description="Monthly fee",
        ),
        Transaction(
            transaction_id="T002",
            date=date(2026, 2, 5),
            merchant="Spotify",
            amount=119.0,
            category="Subscription",
            payment_method="AutoPay",
            description="Monthly fee",
        ),
        Transaction(
            transaction_id="T003",
            date=date(2026, 3, 5),
            merchant="Spotify",
            amount=119.0,
            category="Subscription",
            payment_method="AutoPay",
            description="Monthly fee",
        ),
    ]

    subs = detect_recurring_payments(txs)
    assert len(subs) == 1
    sub = subs[0]
    assert sub.merchant == "Spotify"
    assert sub.frequency == "monthly"
    assert sub.current_cost == 119.0
    assert sub.previous_cost is None
    assert sub.last_payment_date == date(2026, 3, 5)


def test_normal_subscription_not_flagged_as_price_increase():
    """Test 2: Verify normal consistent subscription is not incorrectly flagged as a price increase."""
    txs = [
        Transaction(
            transaction_id="T101",
            date=date(2026, 1, 10),
            merchant="Spotify",
            amount=119.0,
            category="Subscription",
            payment_method="AutoPay",
            description="Monthly fee",
        ),
        Transaction(
            transaction_id="T102",
            date=date(2026, 2, 10),
            merchant="Spotify",
            amount=119.0,
            category="Subscription",
            payment_method="AutoPay",
            description="Monthly fee",
        ),
        Transaction(
            transaction_id="T103",
            date=date(2026, 3, 10),
            merchant="Spotify",
            amount=119.0,
            category="Subscription",
            payment_method="AutoPay",
            description="Monthly fee",
        ),
    ]

    subs = detect_recurring_payments(txs)
    price_increases = detect_price_changes(subs)

    assert len(price_increases) == 0
