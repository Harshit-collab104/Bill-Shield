"""
Financial Issue Detection Engine for BillShield.
"""

import os
from datetime import date
from typing import List, Optional, Dict, Any, Union
import pandas as pd

from backend.models.schemas import (
    Subscription,
    PriceIncreaseIssue,
    UnusedSubscriptionIssue,
    UpcomingRenewalIssue,
    OverlapIssue,
    FinancialAnalysisReport,
    SavingsBreakdown,
)
from backend.services.transactions import load_transactions, parse_date_safe
from backend.services.subscriptions import detect_recurring_payments
from backend.services.savings import calculate_potential_savings

DEFAULT_OVERLAP_GROUPS = {
    "Cloud Storage": ["Dropbox", "Google One", "CloudBox", "OneDrive", "iCloud"],
}


def detect_price_changes(subscriptions: List[Subscription]) -> List[PriceIncreaseIssue]:
    """
    Identifies subscriptions where current recurring cost is higher than previous recurring cost.
    
    Calculates previous price, current price, absolute increase, percentage increase, and date.
    """
    issues: List[PriceIncreaseIssue] = []
    for sub in subscriptions:
        if sub.previous_cost is not None and sub.current_cost > sub.previous_cost:
            increase = round(sub.current_cost - sub.previous_cost, 2)
            pct = round((increase / sub.previous_cost) * 100, 1)
            issues.append(
                PriceIncreaseIssue(
                    merchant=sub.merchant,
                    previous_price=round(sub.previous_cost, 2),
                    current_price=round(sub.current_cost, 2),
                    increase_amount=increase,
                    percentage_increase=pct,
                    date_of_change=sub.last_payment_date,
                )
            )
    return issues


def detect_unused_subscriptions(
    subscriptions: List[Subscription],
    reference_date: Optional[date] = None,
    threshold_days: int = 90,
) -> List[UnusedSubscriptionIssue]:
    """
    Identifies subscriptions with no recorded activity for >= threshold_days.
    
    Flags issues as POTENTIALLY_UNUSED / Requires review.
    """
    if reference_date is None:
        reference_date = date.today()

    issues: List[UnusedSubscriptionIssue] = []
    for sub in subscriptions:
        if sub.last_usage_date is not None:
            days_inactive = (reference_date - sub.last_usage_date).days
            if days_inactive >= threshold_days:
                annual_cost = round(sub.current_cost * 12, 2)
                issues.append(
                    UnusedSubscriptionIssue(
                        merchant=sub.merchant,
                        monthly_cost=round(sub.current_cost, 2),
                        days_since_usage=days_inactive,
                        estimated_annual_cost=annual_cost,
                        reason=f"No activity detected in the last {days_inactive} days. Requires review.",
                    )
                )
    return issues


def detect_upcoming_renewals(
    subscriptions: List[Subscription],
    reference_date: Optional[date] = None,
    days_ahead: int = 30,
) -> List[UpcomingRenewalIssue]:
    """
    Identifies subscriptions renewing within the next specified window (default 30 days).
    """
    if reference_date is None:
        reference_date = date.today()

    issues: List[UpcomingRenewalIssue] = []
    for sub in subscriptions:
        days_until = (sub.next_renewal_date - reference_date).days
        if 1 <= days_until <= days_ahead:
            issues.append(
                UpcomingRenewalIssue(
                    merchant=sub.merchant,
                    renewal_date=sub.next_renewal_date,
                    expected_amount=round(sub.current_cost, 2),
                    days_until_renewal=days_until,
                )
            )
    issues.sort(key=lambda x: x.days_until_renewal)
    return issues


def detect_potential_overlaps(
    subscriptions: List[Subscription],
    overlap_groups: Optional[Dict[str, List[str]]] = None,
) -> List[OverlapIssue]:
    """
    Identifies category groups with multiple active recurring subscriptions.
    
    Flags as POTENTIAL_OVERLAP rather than confirmed duplicates.
    """
    groups = overlap_groups or DEFAULT_OVERLAP_GROUPS
    issues: List[OverlapIssue] = []

    active_merchants = {sub.merchant: sub for sub in subscriptions}

    for group_name, merchant_list in groups.items():
        matching = [m for m in merchant_list if m in active_merchants]
        if len(matching) > 1:
            total_monthly = round(sum(active_merchants[m].current_cost for m in matching), 2)
            issues.append(
                OverlapIssue(
                    category=group_name,
                    merchants=matching,
                    monthly_total=total_monthly,
                    reason=f"Multiple {group_name.lower()} subscriptions detected ({', '.join(matching)}). Potential redundancy.",
                )
            )
    return issues


def load_telemetry_from_csv(subscriptions_csv_path: str) -> Dict[str, Dict[str, Any]]:
    """Loads usage telemetry metadata from a subscriptions CSV file if present."""
    telemetry: Dict[str, Dict[str, Any]] = {}
    if not os.path.exists(subscriptions_csv_path):
        return telemetry

    try:
        df = pd.read_csv(subscriptions_csv_path)
        for _, row in df.iterrows():
            merchant = str(row.get("merchant", "")).strip()
            if not merchant:
                continue
            cat = str(row.get("category", "")).strip()
            last_use = parse_date_safe(row.get("last_usage_date"))
            telemetry[merchant] = {
                "category": cat if cat else None,
                "last_usage_date": last_use,
            }
    except Exception:
        pass
    return telemetry


def analyze_finances(
    transactions_source: Union[str, pd.DataFrame],
    subscriptions_csv_path: Optional[str] = None,
    reference_date: Optional[date] = None,
    unused_threshold_days: int = 90,
    renewal_window_days: int = 5,
) -> FinancialAnalysisReport:
    """
    Unified high-level analysis function orchestrating all BillShield detection services.
    
    Returns a clean, structured FinancialAnalysisReport ready for Agent or UI consumption.
    """
    transactions, errors = load_transactions(transactions_source)

    if not transactions:
        return FinancialAnalysisReport(
            transactions_analyzed=0,
            subscriptions_detected=0,
            monthly_recurring_spend=0.0,
            potential_monthly_savings=0.0,
            potential_annual_savings=0.0,
            price_increases=[],
            potentially_unused=[],
            upcoming_renewals=[],
            potential_overlaps=[],
            savings_breakdown=[],
        )

    if reference_date is None:
        reference_date = max(t.date for t in transactions)

    telemetry = {}
    if subscriptions_csv_path and os.path.exists(subscriptions_csv_path):
        telemetry = load_telemetry_from_csv(subscriptions_csv_path)

    subscriptions = detect_recurring_payments(transactions, usage_telemetry=telemetry)

    price_increases = detect_price_changes(subscriptions)
    potentially_unused = detect_unused_subscriptions(
        subscriptions, reference_date=reference_date, threshold_days=unused_threshold_days
    )
    upcoming_renewals = detect_upcoming_renewals(
        subscriptions, reference_date=reference_date, days_ahead=renewal_window_days
    )
    potential_overlaps = detect_potential_overlaps(subscriptions)

    savings_analysis = calculate_potential_savings(
        unused_subscriptions=potentially_unused,
        overlap_issues=potential_overlaps,
    )

    monthly_recurring_spend = round(sum(s.current_cost for s in subscriptions), 2)

    return FinancialAnalysisReport(
        transactions_analyzed=len(transactions),
        subscriptions_detected=len(subscriptions),
        monthly_recurring_spend=monthly_recurring_spend,
        potential_monthly_savings=savings_analysis.total_potential_monthly_savings,
        potential_annual_savings=savings_analysis.total_potential_annual_savings,
        price_increases=price_increases,
        potentially_unused=potentially_unused,
        upcoming_renewals=upcoming_renewals,
        potential_overlaps=potential_overlaps,
        savings_breakdown=savings_analysis.breakdown,
    )
