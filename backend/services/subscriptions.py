"""
Subscription detection and management service for BillShield.
"""

import collections
from datetime import date, timedelta
from typing import List, Optional, Dict, Any
from dateutil.relativedelta import relativedelta

from backend.models.schemas import Subscription, Transaction, SubscriptionStatus


def detect_recurring_payments(
    transactions: List[Transaction],
    usage_telemetry: Optional[Dict[str, Dict[str, Any]]] = None
) -> List[Subscription]:
    """
    Analyzes transaction history to identify recurring merchants and payments.
    
    Derives frequency, current cost, previous cost, last payment date, and estimated next renewal.
    Optionally merges usage telemetry (last_usage_date, category) if provided.
    """
    if usage_telemetry is None:
        usage_telemetry = {}

    # Group transactions by normalized merchant name
    merchant_txs: Dict[str, List[Transaction]] = collections.defaultdict(list)
    for tx in transactions:
        merchant_txs[tx.merchant.strip()].append(tx)

    detected_subscriptions: List[Subscription] = []
    sub_counter = 1

    for merchant_name, tx_list in merchant_txs.items():
        # Sort transactions chronologically
        sorted_txs = sorted(tx_list, key=lambda x: x.date)

        # Must have at least 2 transactions to establish a recurring pattern, or category explicit
        telemetry = usage_telemetry.get(merchant_name, {})
        category = telemetry.get("category") or sorted_txs[-1].category

        # Check if category or description indicates subscription or if >= 2 repeated transactions
        if len(sorted_txs) < 2 and category.lower() != "subscription":
            continue

        if len(sorted_txs) >= 2:
            # Calculate date intervals between consecutive transactions
            intervals = []
            for i in range(1, len(sorted_txs)):
                delta = (sorted_txs[i].date - sorted_txs[i - 1].date).days
                intervals.append(delta)

            avg_interval = sum(intervals) / len(intervals)

            # Check if interval corresponds to monthly (approx 20 - 45 days) or annual (approx 330 - 400 days)
            if 15 <= avg_interval <= 45:
                frequency = "monthly"
                renewal_delta = relativedelta(months=1)
            elif 330 <= avg_interval <= 400:
                frequency = "annual"
                renewal_delta = relativedelta(years=1)
            else:
                # If transaction category is explicitly 'Subscription', assume monthly
                if category.lower() == "subscription":
                    frequency = "monthly"
                    renewal_delta = relativedelta(months=1)
                else:
                    # Non-recurring erratic purchases
                    continue
        else:
            # Single transaction under 'Subscription' category
            frequency = "monthly"
            renewal_delta = relativedelta(months=1)

        # Latest transaction details
        latest_tx = sorted_txs[-1]
        current_cost = round(latest_tx.amount, 2)
        last_payment_date = latest_tx.date
        next_renewal_date = last_payment_date + renewal_delta

        # Determine previous recurring cost if price changed over history
        previous_cost: Optional[float] = None
        amounts = [round(t.amount, 2) for t in sorted_txs]
        
        # Look backwards for a distinct earlier recurring amount
        for amt in reversed(amounts[:-1]):
            if abs(amt - current_cost) > 0.01:
                previous_cost = amt
                break

        # Extract last usage date from telemetry if present
        last_usage_raw = telemetry.get("last_usage_date")
        last_usage_date: Optional[date] = None
        if isinstance(last_usage_raw, date):
            last_usage_date = last_usage_raw
        elif isinstance(last_usage_raw, str):
            from backend.services.transactions import parse_date_safe
            last_usage_date = parse_date_safe(last_usage_raw)

        sub_id = f"SUB-{sub_counter:03d}"
        sub_counter += 1

        subscription = Subscription(
            subscription_id=sub_id,
            merchant=merchant_name,
            category=category,
            frequency=frequency,
            current_cost=current_cost,
            previous_cost=previous_cost,
            last_payment_date=last_payment_date,
            next_renewal_date=next_renewal_date,
            status=SubscriptionStatus.ACTIVE,
            last_usage_date=last_usage_date,
        )
        detected_subscriptions.append(subscription)

    # Sort subscriptions deterministically by merchant name
    detected_subscriptions.sort(key=lambda s: s.merchant)
    return detected_subscriptions


def get_subscriptions(
    subscriptions: List[Subscription],
    status: Optional[str] = None,
    merchant: Optional[str] = None,
) -> List[Subscription]:
    """Filters detected subscriptions."""
    filtered = subscriptions
    if status:
        filtered = [s for s in filtered if s.status.upper() == status.upper()]
    if merchant:
        filtered = [s for s in filtered if merchant.lower() in s.merchant.lower()]
    return filtered
