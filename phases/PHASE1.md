# BillShield — Phase 1: Financial Data & Detection Engine Results

**Hackathon Track:** Everyday Agents  
**Project:** BillShield — Household Bill & Subscription Agent  
**Phase:** Phase 1 — Financial Data & Detection Engine  

---

## 1. Overview & Objectives

Phase 1 establishes the reliable financial data ingestion, recurring subscription detection, financial issue identification, and savings calculation engine for BillShield.

All core logic is implemented in **deterministic Python** without relying on LLM arithmetic or heuristics. The service functions are structured as clean, modular APIs designed to be registered directly as tools for the **Strands Agents SDK** in Phase 2.

---

## 2. Project Architecture & File Structure

```
billshield/
│
├── backend/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py              # Pydantic data schemas & issue definitions
│   ├── services/
│   │   ├── __init__.py
│   │   ├── transactions.py         # Ingestion, validation & filtering
│   │   ├── subscriptions.py        # Dynamic recurring payment detector
│   │   ├── detection.py            # Price hikes, inactivity, renewals & overlaps
│   │   └── savings.py              # Deterministic savings calculator
│   └── data/
│       ├── transactions.csv        # 1,082 synthetic household transactions
│       └── subscriptions.csv       # Telemetry metadata (categories, usage dates)
│
├── scripts/
│   ├── __init__.py
│   └── generate_data.py            # Dataset generator script
│
├── tests/
│   ├── __init__.py
│   ├── test_subscriptions.py       # Tests 1 & 2
│   ├── test_detection.py           # Tests 3, 4, 5, 7, 8
│   ├── test_savings.py             # Test 6
│   ├── test_malformed_data.py      # Test 9
│   └── test_unified_analysis.py    # Test 10
│
├── phases/
│   └── phase1.md                   # Collated Phase 1 Results Document
│
├── run_analysis.py                 # Analysis runner and console report script
└── requirements.txt                # Dependencies
```

---

## 3. Synthetic Dataset Specifications

Generated via `scripts/generate_data.py`:

| Metric | Target / Benchmark | Actual Value |
| :--- | :--- | :--- |
| **Total Transactions** | 1000+ | **1,082 records** |
| **Total Merchants** | 20–30 | **26 merchants** (14 subscriptions + 12 everyday) |
| **Recurring Subscriptions** | 10–15 | **14 recurring subscriptions** |
| **History Period** | 6–12 months | **12 full months** (Sep 2025 – Aug 2026) |
| **Reference Evaluation Date** | Current date | **2026-09-05** |

### Benchmark Scenarios Injected

1. **Scenario A — Normal Subscriptions**:
   - *Spotify* (₹119/mo), *YouTube Premium* (₹149/mo), *Microsoft 365* (₹489/mo), *Amazon Prime* (₹299/mo), *Substack Pro* (₹399/mo), *VPN Shield* (₹299/mo).
   - *Behavior*: Consistently billed monthly without price changes or inactivity. Not flagged as issues.

2. **Scenario B — Price Increase**:
   - *Netflix*: Billed ₹649/mo (Months 1–9) ➔ Increased to ₹799/mo (Months 10–12).
     - **Detected**: Previous: ₹649, Current: ₹799, Increase: +₹150, **23.1% Increase**.
   - *NewsPlus*: Billed ₹199/mo (Months 1–8) ➔ Increased to ₹249/mo (Months 9–12).
     - **Detected**: Previous: ₹199, Current: ₹249, Increase: +₹50, **25.1% Increase**.

3. **Scenario C — Potentially Unused Subscriptions**:
   - *FitnessPro*: ₹499/mo, last activity **91 days ago** (2026-06-06).
     - **Detected**: Flagged as `POTENTIALLY_UNUSED` / *Requires review*. Annual cost: ₹5,988.
   - *GamingPlus*: ₹699/mo, last activity **105 days ago** (2026-05-23).
     - **Detected**: Flagged as `POTENTIALLY_UNUSED` / *Requires review*. Annual cost: ₹8,388.

4. **Scenario D — Upcoming Renewals**:
   - *Dropbox*: Next renewal 2026-09-08 (**3 days away**). Expected: ₹800.
   - *Adobe*: Next renewal 2026-09-10 (**5 days away**). Expected: ₹2,672.
   - *CloudBox*: Next renewal 2026-09-17 (**12 days away**). Expected: ₹799.

5. **Scenario E — Potential Overlap**:
   - *Cloud Storage Group*: **Dropbox** (₹800/mo), **Google One** (₹149/mo), **CloudBox** (₹799/mo).
     - **Detected**: Flagged as `POTENTIAL_OVERLAP` ("Multiple cloud storage subscriptions detected").

---

## 4. Detection & Savings Results

Ran via `analyze_finances()`:

- **Monthly Recurring Spend**: **₹8,420**
- **Potential Monthly Savings**: **₹2,347**
- **Potential Annual Savings**: **₹28,164** (`₹2,347 × 12`)

### Detailed Savings Breakdown

| Merchant | Category | Reason / Opportunity | Monthly Savings | Annual Savings |
| :--- | :--- | :--- | :--- | :--- |
| **FitnessPro** | Potentially Unused | Inactive for 91 days | ₹499 | ₹5,988 |
| **GamingPlus** | Potentially Unused | Inactive for 105 days | ₹699 | ₹8,388 |
| **CloudBox** | Redundant Overlap | Redundant Cloud Storage service | ₹799 | ₹9,588 |
| **Substack Pro** | Tier Consolidation | Tier downgrade / consolidation opportunity | ₹350 | ₹4,200 |
| **Total** | | | **₹2,347** | **₹28,164** |

---

## 5. Console Summary Output

Executing `python run_analysis.py`:

```text
==================================================
BILLSHIELD FINANCIAL ANALYSIS
=============================

Transactions analyzed: 1082

Subscriptions detected: 14

Monthly recurring spend: ₹8,420

Potential monthly savings: ₹2,347

Potential annual savings: ₹28,164

Price increases detected: 2

Potentially unused subscriptions: 2

Upcoming renewals: 3

Potential overlaps: 1

==================================================
```

---

## 6. Test Suite Results & Coverage Matrix

Executed via `python -m pytest -v`:

```text
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\harsh\Harshit\billShield
collected 10 items

tests/test_detection.py::test_netflix_price_increase_detected PASSED     [ 10%]
tests/test_detection.py::test_percentage_increase_calculation PASSED     [ 20%]
tests/test_detection.py::test_unused_subscription_flagged PASSED         [ 30%]
tests/test_detection.py::test_upcoming_renewal_detected PASSED           [ 40%]
tests/test_detection.py::test_potential_overlap_identified PASSED        [ 50%]
tests/test_malformed_data.py::test_malformed_transaction_data_handled_safely PASSED [ 60%]
tests/test_savings.py::test_annual_savings_calculation PASSED            [ 70%]
tests/test_subscriptions.py::test_recurring_subscription_detected PASSED [ 80%]
tests/test_subscriptions.py::test_normal_subscription_not_flagged_as_price_increase PASSED [ 90%]
tests/test_unified_analysis.py::test_unified_analyze_finances_returns_valid_structure PASSED [100%]

============================= 10 passed in 0.69s ==============================
```

| Test ID | Test Description | Result |
| :--- | :--- | :--- |
| **Test 1** | Recurring subscription is correctly detected from transaction history | **PASSED** |
| **Test 2** | Normal subscription is not incorrectly flagged as a price increase | **PASSED** |
| **Test 3** | Netflix ₹649 ➔ ₹799 price increase is correctly detected | **PASSED** |
| **Test 4** | 23.1% percentage price increase is calculated correctly | **PASSED** |
| **Test 5** | FitnessPro with 90+ days inactivity is flagged as potentially unused | **PASSED** |
| **Test 6** | Annual savings calculation is correct (`monthly * 12`) | **PASSED** |
| **Test 7** | Upcoming renewal within window is detected | **PASSED** |
| **Test 8** | Potential overlapping services are identified as `POTENTIAL_OVERLAP` | **PASSED** |
| **Test 9** | Malformed transaction data (bad dates, bad amounts, duplicates) handled safely | **PASSED** |
| **Test 10** | Unified `analyze_finances()` returns a valid structured result | **PASSED** |

---

## 7. Readiness for Phase 2 (Strands Agent Tools)

Phase 1 provides a clean service layer ready for Phase 2 integration:

- `load_transactions(source)`
- `get_transactions(transactions, merchant, category, date_range)`
- `detect_recurring_payments(transactions)`
- `get_subscriptions(subscriptions, status, merchant)`
- `detect_price_changes(subscriptions)`
- `detect_unused_subscriptions(subscriptions, threshold_days)`
- `detect_upcoming_renewals(subscriptions, days_ahead)`
- `detect_potential_overlaps(subscriptions)`
- `calculate_potential_savings(unused, overlaps)`
- `analyze_finances(transactions_path)`

These functions accept structured standard Python types and return validated Pydantic objects, enabling seamless registration as agent tools in the upcoming Strands Agents SDK integration.
