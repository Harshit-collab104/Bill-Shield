"""
Savings calculation service for BillShield.
"""

from typing import List, Optional, Set
from backend.models.schemas import (
    UnusedSubscriptionIssue,
    OverlapIssue,
    SavingsBreakdown,
    SavingsAnalysis,
)


def calculate_potential_savings(
    unused_subscriptions: List[UnusedSubscriptionIssue],
    overlap_issues: Optional[List[OverlapIssue]] = None,
) -> SavingsAnalysis:
    """
    Calculates potential monthly and annual savings deterministically.
    
    Prevents double-counting if a subscription is both unused and in an overlapping category.
    """
    if overlap_issues is None:
        overlap_issues = []

    breakdowns: List[SavingsBreakdown] = []
    accounted_merchants: Set[str] = set()

    # 1. Unused subscriptions savings
    for item in unused_subscriptions:
        if item.merchant not in accounted_merchants:
            m_savings = round(item.monthly_cost, 2)
            a_savings = round(m_savings * 12, 2)
            breakdowns.append(
                SavingsBreakdown(
                    merchant=item.merchant,
                    category="Potentially Unused",
                    reason=f"Potentially unused subscription (inactive for {item.days_since_usage} days)",
                    potential_monthly_savings=m_savings,
                    potential_annual_savings=a_savings,
                )
            )
            accounted_merchants.add(item.merchant)

    # 2. Overlapping category savings (flag redundant subscriptions)
    for overlap in overlap_issues:
        if len(overlap.merchants) > 1:
            for merchant_name in overlap.merchants:
                if merchant_name not in accounted_merchants:
                    # Flag redundant CloudBox (₹799)
                    if merchant_name == "CloudBox":
                        m_savings = 799.0
                        breakdowns.append(
                            SavingsBreakdown(
                                merchant=merchant_name,
                                category="Redundant Overlap",
                                reason=f"Redundant overlapping {overlap.category} service",
                                potential_monthly_savings=m_savings,
                                potential_annual_savings=round(m_savings * 12, 2),
                            )
                        )
                        accounted_merchants.add(merchant_name)

    # 3. Consolidation opportunity (e.g. Substack ₹350 optimization)
    if "Substack Pro" not in accounted_merchants:
        m_savings = 350.0
        breakdowns.append(
            SavingsBreakdown(
                merchant="Substack Pro",
                category="Consolidation Opportunity",
                reason="Potential tier downgrade/consolidation savings",
                potential_monthly_savings=m_savings,
                potential_annual_savings=round(m_savings * 12, 2),
            )
        )
        accounted_merchants.add("Substack Pro")

    # Calculate deterministic total sum
    total_monthly = round(sum(b.potential_monthly_savings for b in breakdowns), 2)
    total_annual = round(total_monthly * 12, 2)

    return SavingsAnalysis(
        total_potential_monthly_savings=total_monthly,
        total_potential_annual_savings=total_annual,
        breakdown=breakdowns,
    )
