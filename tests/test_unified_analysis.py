"""
Tests for unified analyze_finances function.
"""

from datetime import date
from backend.models.schemas import FinancialAnalysisReport
from backend.services.detection import analyze_finances


def test_unified_analyze_finances_returns_valid_structure():
    """Test 10: Verify unified analyze_finances() returns a valid structured report."""
    tx_path = "backend/data/transactions.csv"
    sub_path = "backend/data/subscriptions.csv"
    ref_date = date(2026, 9, 5)

    report = analyze_finances(
        transactions_source=tx_path,
        subscriptions_csv_path=sub_path,
        reference_date=ref_date,
        unused_threshold_days=90,
        renewal_window_days=5,
    )

    assert isinstance(report, FinancialAnalysisReport)
    assert report.transactions_analyzed >= 1000
    assert report.subscriptions_detected == 14
    assert report.monthly_recurring_spend == 8420.0
    assert report.potential_monthly_savings == 2347.0
    assert report.potential_annual_savings == 28164.0
    assert len(report.price_increases) == 2
    assert len(report.potentially_unused) == 2
    assert len(report.upcoming_renewals) == 3
    assert len(report.potential_overlaps) == 1
