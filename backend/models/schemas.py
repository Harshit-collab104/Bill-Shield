"""
Data schemas for BillShield financial analysis engine.
"""

from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field


class Transaction(BaseModel):
    """Represents an individual bank or card transaction."""

    transaction_id: str
    date: date
    merchant: str
    amount: float
    category: str
    payment_method: str
    description: str


class SubscriptionStatus:
    ACTIVE = "ACTIVE"
    POTENTIALLY_UNUSED = "POTENTIALLY_UNUSED"
    CANCELLED = "CANCELLED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class Subscription(BaseModel):
    """Represents a detected or managed recurring subscription."""

    subscription_id: str
    merchant: str
    category: str = "Subscription"
    frequency: str = "monthly"
    current_cost: float
    previous_cost: Optional[float] = None
    last_payment_date: date
    next_renewal_date: date
    status: str = SubscriptionStatus.ACTIVE
    last_usage_date: Optional[date] = None


class PriceIncreaseIssue(BaseModel):
    """Represents a price increase detected on a recurring payment."""

    merchant: str
    previous_price: float
    current_price: float
    increase_amount: float
    percentage_increase: float
    date_of_change: date
    issue_type: str = "PRICE_INCREASE"


class UnusedSubscriptionIssue(BaseModel):
    """Represents a subscription flagged as potentially unused based on inactivity."""

    merchant: str
    monthly_cost: float
    days_since_usage: int
    estimated_annual_cost: float
    reason: str
    issue_type: str = "POTENTIALLY_UNUSED"


class UpcomingRenewalIssue(BaseModel):
    """Represents a subscription with an upcoming renewal date."""

    merchant: str
    renewal_date: date
    expected_amount: float
    days_until_renewal: int
    issue_type: str = "UPCOMING_RENEWAL"


class OverlapIssue(BaseModel):
    """Represents multiple subscriptions in the same functional category (potential duplication)."""

    category: str
    merchants: List[str]
    monthly_total: float
    reason: str
    issue_type: str = "POTENTIAL_OVERLAP"


class SavingsBreakdown(BaseModel):
    """Individual savings opportunity breakdown."""

    merchant: str
    category: str
    reason: str
    potential_monthly_savings: float
    potential_annual_savings: float


class SavingsAnalysis(BaseModel):
    """Overall financial savings analysis."""

    total_potential_monthly_savings: float
    total_potential_annual_savings: float
    breakdown: List[SavingsBreakdown]


class FinancialAnalysisReport(BaseModel):
    """Unified financial analysis report for consumption by UI or future Strands agents."""

    transactions_analyzed: int
    subscriptions_detected: int
    monthly_recurring_spend: float
    potential_monthly_savings: float
    potential_annual_savings: float
    price_increases: List[PriceIncreaseIssue]
    potentially_unused: List[UnusedSubscriptionIssue]
    upcoming_renewals: List[UpcomingRenewalIssue]
    potential_overlaps: List[OverlapIssue]
    savings_breakdown: List[SavingsBreakdown]
