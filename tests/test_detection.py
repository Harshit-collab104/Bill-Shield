"""
Tests for price increases, unused subscriptions, upcoming renewals, and potential overlaps.
"""

from datetime import date
from backend.models.schemas import Transaction, Subscription
from backend.services.subscriptions import detect_recurring_payments
from backend.services.detection import (
    detect_price_changes,
    detect_unused_subscriptions,
    detect_upcoming_renewals,
    detect_potential_overlaps,
)


def test_netflix_price_increase_detected():
    """Test 3: Verify Netflix price increase from 649 to 799 is correctly detected."""
    txs = [
        Transaction(
            transaction_id="T201",
            date=date(2026, 4, 12),
            merchant="Netflix",
            amount=649.0,
            category="Subscription",
            payment_method="AutoPay",
            description="Monthly subscription",
        ),
        Transaction(
            transaction_id="T202",
            date=date(2026, 5, 12),
            merchant="Netflix",
            amount=649.0,
            category="Subscription",
            payment_method="AutoPay",
            description="Monthly subscription",
        ),
        Transaction(
            transaction_id="T203",
            date=date(2026, 6, 12),
            merchant="Netflix",
            amount=799.0,
            category="Subscription",
            payment_method="AutoPay",
            description="Monthly subscription",
        ),
    ]

    subs = detect_recurring_payments(txs)
    price_issues = detect_price_changes(subs)

    assert len(price_issues) == 1
    issue = price_issues[0]
    assert issue.merchant == "Netflix"
    assert issue.previous_price == 649.0
    assert issue.current_price == 799.0
    assert issue.increase_amount == 150.0


def test_percentage_increase_calculation():
    """Test 4: Verify 23.1% percentage increase calculation for Netflix (649 -> 799)."""
    sub = Subscription(
        subscription_id="SUB-99",
        merchant="Netflix",
        category="Streaming Video",
        frequency="monthly",
        current_cost=799.0,
        previous_cost=649.0,
        last_payment_date=date(2026, 6, 12),
        next_renewal_date=date(2026, 7, 12),
    )

    issues = detect_price_changes([sub])
    assert len(issues) == 1
    assert issues[0].percentage_increase == 23.1


def test_unused_subscription_flagged():
    """Test 5: Verify FitnessPro with 90+ days inactivity is flagged as potentially unused."""
    ref_date = date(2026, 9, 5)
    last_use = date(2026, 6, 6)  # 91 days ago

    sub = Subscription(
        subscription_id="SUB-05",
        merchant="FitnessPro",
        category="Fitness",
        frequency="monthly",
        current_cost=499.0,
        last_payment_date=date(2026, 8, 20),
        next_renewal_date=date(2026, 9, 20),
        last_usage_date=last_use,
    )

    unused = detect_unused_subscriptions([sub], reference_date=ref_date, threshold_days=90)
    assert len(unused) == 1
    issue = unused[0]
    assert issue.merchant == "FitnessPro"
    assert issue.monthly_cost == 499.0
    assert issue.days_since_usage == 91
    assert issue.estimated_annual_cost == 5988.0
    assert "UNUSED" in issue.issue_type.upper()


def test_upcoming_renewal_detected():
    """Test 7: Verify upcoming renewal within window is correctly identified."""
    ref_date = date(2026, 9, 5)

    sub = Subscription(
        subscription_id="SUB-10",
        merchant="Adobe",
        category="Design",
        frequency="monthly",
        current_cost=2672.0,
        last_payment_date=date(2026, 8, 10),
        next_renewal_date=date(2026, 9, 10),  # 5 days from ref_date
    )

    renewals = detect_upcoming_renewals([sub], reference_date=ref_date, days_ahead=7)
    assert len(renewals) == 1
    item = renewals[0]
    assert item.merchant == "Adobe"
    assert item.expected_amount == 2672.0
    assert item.days_until_renewal == 5


def test_potential_overlap_identified():
    """Test 8: Verify potential overlapping services are identified as POTENTIAL_OVERLAP."""
    subs = [
        Subscription(
            subscription_id="SUB-01",
            merchant="Dropbox",
            category="Cloud Storage",
            frequency="monthly",
            current_cost=800.0,
            last_payment_date=date(2026, 8, 8),
            next_renewal_date=date(2026, 9, 8),
        ),
        Subscription(
            subscription_id="SUB-02",
            merchant="Google One",
            category="Cloud Storage",
            frequency="monthly",
            current_cost=149.0,
            last_payment_date=date(2026, 9, 3),
            next_renewal_date=date(2026, 10, 3),
        ),
        Subscription(
            subscription_id="SUB-03",
            merchant="CloudBox",
            category="Cloud Storage",
            frequency="monthly",
            current_cost=799.0,
            last_payment_date=date(2026, 8, 17),
            next_renewal_date=date(2026, 9, 17),
        ),
    ]

    overlaps = detect_potential_overlaps(subs)
    assert len(overlaps) == 1
    issue = overlaps[0]
    assert issue.issue_type == "POTENTIAL_OVERLAP"
    assert issue.category == "Cloud Storage"
    assert set(issue.merchants) == {"Dropbox", "Google One", "CloudBox"}
