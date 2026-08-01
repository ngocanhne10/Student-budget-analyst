# Trustworthy Student Budget Analyst

Secure AI Hackathon (Seattle Data AI & Security Community) — Data Analyst track.

A Streamlit dashboard that answers questions about a student's weekly budget
using calculations run directly against a dataset — every answer is either
**verified** against recorded data, **simulated** from a hypothetical the user
enters, or explicitly flagged as **unsupported** when the data can't back it
up. Nothing is presented as fact unless it can be traced back to an actual
calculation on the dataset.


## Challenge

Build an AI assistant or dashboard that lets users ask questions about a
dataset and get answers that are calculated or verified from the data,
rather than invented by the model.

## Problem this solves

Helping students track and control a weekly budget across fixed and variable
spending categories, without either (a) a black-box chatbot that hallucinates
numbers, or (b) a dashboard so rigid it can't handle a question outside its
exact intended scope.

---

## Setup

**Requirements:** Python 3.9+ and pip.

```bash
git clone: https://github.com/ngocanhne10/Student-budget-analyst
cd student-budget-analyst

## Installation

```bash
pip install -r requirements.txt
```

Installs: `streamlit`, `pandas`, `plotly` — all open source, no accounts or
API keys required.

## Execution

```bash
streamlit run app.py
```

## Demo instructions

1. In the sidebar, pick a student — `STU001 (Amsterdam)` or
   `STU002 (Rotterdam)`.
2. Click any of the four preset question buttons, or type a free-text
   question into the box:
   - **Q1** "What is my total spending per month for each category?" →
     🟢 Verified — bar chart + calculation code shown in an expander.
   - **Q2** "Which category have I spent over the budget? If yes, by how
     much?" → 🟢 Verified — target vs. actual chart, overage table.
   - **Q3** "Find me online coupons/discounts in the supermarket: Albert
     Heijn, Jumbo and Lidl" → 🔴 Unsupported — the app explains it has no
     data source for live retailer promotions and declines rather than
     inventing a coupon code.
   - **Q4** "If I add one more category for subscription, how will my
     budget change?" → 🟡 Simulated — enter a hypothetical monthly cost,
     see the projected new total, clearly labeled as a projection rather
     than recorded history.
3. Try a question that isn't any of the four (e.g. "what's the weather
   today?") to see the unsupported fallback trigger on an unrecognized
   question too — the router never silently guesses.

## Project structure

```
student-budget-analyst/
├── app.py                      # Streamlit UI
├── question_router.py          # trust-tier classification + calculation logic
├── data_utils.py                # dataset loading/filtering
├── student_budget_dataset.csv   # 2 students × 7 categories × 5 weeks
├── requirements.txt
└── README.md
```

## Trust tiers (the core design)

| Tier | Meaning | Example |
|---|---|---|
| 🟢 Verified | Pure calculation on recorded data | "Total spend per category" |
| 🟡 Simulated | Calculation on a user-supplied hypothetical, clearly labeled | "What if I add a subscription?" |
| 🔴 Unsupported | No data exists to answer this — declines rather than guesses | "Find me supermarket coupons" |

Classification (`classify_question` in `question_router.py`) is deliberate,
inspectable keyword matching rather than a black-box model call — the
component deciding *how* to answer needs to be as verifiable as the answers
themselves.

## Dataset, API, and third-party disclosures

- **Dataset**: fully synthetic data created for this hackathon submission.
  It does not represent a real person, and contains no real financial
  records, account numbers, or personally identifiable information.
- **APIs / third-party services**: none. The app runs entirely on the local
  CSV file; no network calls, no external accounts, no API keys.
- **Third-party libraries**: `streamlit`, `pandas`, `plotly` — all
  open-source, installed via `requirements.txt`.
- **Credentials/secrets**: none used or required anywhere in this project.

## Extending this

- **More questions**: add a rule to `INTENT_RULES` in `question_router.py`
  plus a matching `answer_*` function.
- **Free-text robustness**: current router is keyword-based on purpose. To
  handle more varied phrasing, swap `classify_question` for an LLM call
  constrained to return one of the known `type` values — keep the
  unsupported fallback either way.
- **Weekly push notification / budget score**: not built in this version.
  Could be added as a scheduled job that runs `answer_over_budget` at the
  end of each week and scores the result (e.g. % of categories on-budget).
