"""
question_router.py

The core "trust" layer of the app. Every question is classified into one
of three tiers BEFORE any answer is computed:

  - verified    : fully answerable from recorded data via calculation
  - simulated   : answerable, but only as a projection built on a
                   hypothetical input the user supplies (must be labeled
                   clearly so it's never mistaken for recorded fact)
  - unsupported : cannot be answered from this dataset at all -> the
                   system explains why and declines, instead of guessing

Classification here is deliberately simple keyword matching rather than
a black-box model call. For a "verified, not invented" system, the
router itself needs to be inspectable and predictable -- if the router
were an opaque LLM call, you'd have no guarantee *it* isn't hallucinating
which tier a question belongs to.
"""

import pandas as pd
from data_utils import WEEKS_PER_MONTH, num_weeks

# ---------------------------------------------------------------------
# 1. Classification
# ---------------------------------------------------------------------

INTENT_RULES = [
    {
        "type": "monthly_by_category",
        "tier": "verified",
        "keywords": [
            "total spend", "total spending", "spending per month",
            "per category", "how much do i spend", "monthly spend",
        ],
    },
    {
        "type": "over_budget",
        "tier": "verified",
        "keywords": [
            "over budget", "over the budget", "overspend", "overspent",
            "which category have i spent over",
        ],
    },
    {
        "type": "new_subscription_simulation",
        "tier": "simulated",
        "keywords": [
            "add one more", "add a subscription", "new subscription",
            "what if", "if i add",
        ],
    },
    {
        "type": "coupon_lookup",
        "tier": "unsupported",
        "keywords": [
            "coupon", "discount", "promo", "deal",
            "albert heijn", "jumbo", "lidl",
        ],
    },
]


def classify_question(text: str):
    """Returns (question_type, tier). Falls back to unsupported if no
    rule matches -- an unrecognized question should never silently fall
    through to a guessed answer.
    """
    text_l = text.lower()
    for rule in INTENT_RULES:
        if any(kw in text_l for kw in rule["keywords"]):
            return rule["type"], rule["tier"]
    return "unknown", "unsupported"


# ---------------------------------------------------------------------
# 2. Verified answers (Q1, Q2)
# ---------------------------------------------------------------------

def answer_monthly_by_category(df: pd.DataFrame, student_id: str):
    sub = df[df.student_id == student_id]
    weeks = num_weeks(sub)
    result = sub.groupby("category")["actual_spend"].sum() / weeks * WEEKS_PER_MONTH
    result = result.round(2).sort_values(ascending=False)

    calc_code = (
        f"weeks = df[df.student_id == '{student_id}']['week_number'].nunique()  # = {weeks}\n"
        f"monthly_by_category = df[df.student_id == '{student_id}']\\\n"
        f"    .groupby('category')['actual_spend'].sum() / weeks * (365.25/12/7)"
    )
    return result, calc_code


def answer_over_budget(df: pd.DataFrame, student_id: str):
    sub = df[df.student_id == student_id]
    grp = sub.groupby("category").agg(
        total_target=("weekly_target", "sum"),
        total_actual=("actual_spend", "sum"),
    )
    grp["overage"] = (grp["total_actual"] - grp["total_target"]).round(2)
    over = grp[grp["overage"] > 0].sort_values("overage", ascending=False)

    calc_code = (
        "grp = df.groupby('category').agg(\n"
        "    total_target=('weekly_target', 'sum'),\n"
        "    total_actual=('actual_spend', 'sum'),\n"
        ")\n"
        "grp['overage'] = grp['total_actual'] - grp['total_target']\n"
        "over = grp[grp['overage'] > 0]"
    )
    return grp, over, calc_code


# ---------------------------------------------------------------------
# 3. Simulated answer (Q4)
# ---------------------------------------------------------------------

def answer_new_subscription_simulation(df: pd.DataFrame, student_id: str, new_monthly_cost: float):
    monthly_by_cat, _ = answer_monthly_by_category(df, student_id)
    current_total = float(monthly_by_cat.sum())
    new_total = current_total + new_monthly_cost

    calc_code = (
        "current_total = monthly_by_category.sum()  # sum of the Q1 result\n"
        "new_total = current_total + new_subscription_monthly_cost  # user-supplied input"
    )
    return current_total, new_total, calc_code


# ---------------------------------------------------------------------
# 4. Unsupported (Q3)
# ---------------------------------------------------------------------

UNSUPPORTED_MESSAGE = (
    "I can only answer questions based on your recorded budget data. This dataset "
    "tracks your own spending across categories like Rent, Grocery, and Entertainment "
    "-- it doesn't contain live discount, coupon, or promotion information from any "
    "retailer. I won't guess at coupon codes or deals, since I have no way to verify "
    "them against your data. Check the retailer's own app or website for current offers."
)
