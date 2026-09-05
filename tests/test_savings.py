"""
Tests for savings calculations.
"""

from backend.models.schemas import UnusedSubscriptionIssue
from backend.services.savings import calculate_potential_savings


def test_annual_savings_calculation():
    """Test 6: Verify annual savings calculation is correct (monthly * 12)."""
    unused = [
        UnusedSubscriptionIssue(
            merchant="FitnessPro",
            monthly_cost=499.0,
            days_since_usage=91,
            estimated_annual_cost=5988.0,
            reason="91 days inactive",
        ),
        UnusedSubscriptionIssue(
            merchant="GamingPlus",
            monthly_cost=699.0,
            days_since_usage=105,
            estimated_annual_cost=8388.0,
            reason="105 days inactive",
        ),
    ]

    result = calculate_potential_savings(unused_subscriptions=unused)
    
    # 499 + 699 = 1198 monthly + 1149 consolidation = 2347 total
    assert result.total_potential_monthly_savings > 0
    assert result.total_potential_annual_savings == round(result.total_potential_monthly_savings * 12, 2)
    
    for item in result.breakdown:
        assert item.potential_annual_savings == round(item.potential_monthly_savings * 12, 2)
