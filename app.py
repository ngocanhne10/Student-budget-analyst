"""
app.py
Trustworthy Student Budget Analyst -- Streamlit demo.

Design principle for the whole app: every answer is visibly tagged with
the tier that produced it (verified / simulated / unsupported), and the
calculation behind any verified or simulated answer is always available
via "Show calculation logic". Nothing is presented as a fact unless it
can be traced back to a pandas operation on the dataset.
"""

import streamlit as st
import plotly.express as px

from data_utils import load_data, get_students, filter_student
from question_router import (
    classify_question,
    answer_monthly_by_category,
    answer_over_budget,
    answer_new_subscription_simulation,
    UNSUPPORTED_MESSAGE,
)

st.set_page_config(
    page_title="Trustworthy Student Budget Analyst",
    page_icon="\U0001F4B6",
    layout="wide",
)

st.title("\U0001F4B6 Trustworthy Student Budget Analyst")
st.caption("Answers are calculated or verified from your data -- never invented.")

df = load_data()
students = get_students(df)

# --- Sidebar: student context -----------------------------------------
with st.sidebar:
    st.header("Student")
    student_options = students.apply(lambda r: f"{r.student_id} \u2014 {r.location}", axis=1).tolist()
    student_label = st.selectbox("Select student", options=student_options)
    student_id = student_label.split(" \u2014 ")[0]

    st.divider()
    sub_preview = filter_student(df, student_id)
    st.caption(f"{sub_preview['week_number'].nunique()} weeks of data, "
               f"{len(sub_preview)} rows for this student")
    st.caption(f"Period: {sub_preview['week_start_date'].min()} to "
               f"{sub_preview['week_start_date'].max()}")

    st.divider()
    st.markdown("**Trust legend**")
    st.markdown("\U0001F7E2 Verified -- calculated directly from data")
    st.markdown("\U0001F7E1 Simulated -- projection from a hypothetical you provide")
    st.markdown("\U0001F534 Unsupported -- can't be answered from this data")

# --- Question input -----------------------------------------------------
st.subheader("Ask a question")

preset_questions = {
    "Q1: Total spend per category": "What is my total spending per month for each category?",
    "Q2: Over budget categories": "Which category have I spent over the budget? If yes, by how much?",
    "Q3: Supermarket coupons": "Find me online coupons/discounts in the supermarket: Albert Heijn, Jumbo and Lidl",
    "Q4: New subscription what-if": "If I add one more category for subscription, how will my budget change?",
}

cols = st.columns(4)
selected_preset = None
for i, (label, q_text) in enumerate(preset_questions.items()):
    if cols[i].button(label, use_container_width=True):
        selected_preset = q_text

question = st.text_input("Or type your own question:", value=selected_preset or "")

# --- Routing + rendering -------------------------------------------------
if question:
    qtype, tier = classify_question(question)

    tier_badge = {
        "verified": "\U0001F7E2 **Verified** -- calculated directly from your recorded data",
        "simulated": "\U0001F7E1 **Simulated** -- a projection based on a hypothetical, not recorded history",
        "unsupported": "\U0001F534 **Unsupported** -- this can't be answered from your data",
    }[tier]
    st.markdown(tier_badge)

    if qtype == "monthly_by_category":
        result, calc_code = answer_monthly_by_category(df, student_id)

        st.write("### Projected monthly spend per category")
        fig = px.bar(
            result, x=result.index, y=result.values,
            labels={"x": "Category", "y": "Projected monthly (\u20ac)"},
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(result.rename("Projected monthly (\u20ac)"))

        with st.expander("Show calculation logic"):
            st.code(calc_code, language="python")

    elif qtype == "over_budget":
        grp, over, calc_code = answer_over_budget(df, student_id)

        st.write("### Target vs actual, by category")
        fig = px.bar(
            grp.reset_index(), x="category", y=["total_target", "total_actual"],
            barmode="group", labels={"value": "\u20ac", "category": "Category"},
        )
        st.plotly_chart(fig, use_container_width=True)

        if len(over) > 0:
            st.write("**Over budget:**")
            st.dataframe(over[["total_target", "total_actual", "overage"]])
        else:
            st.success("No categories are currently over budget.")

        with st.expander("Show calculation logic"):
            st.code(calc_code, language="python")

    elif qtype == "new_subscription_simulation":
        st.write("### Simulate adding a new subscription")
        new_cost = st.number_input(
            "New subscription cost (\u20ac/month)", min_value=0.0, value=12.0, step=1.0,
        )
        current_total, new_total, calc_code = answer_new_subscription_simulation(
            df, student_id, new_cost
        )

        c1, c2 = st.columns(2)
        c1.metric("Current projected monthly", f"\u20ac{current_total:.2f}")
        c2.metric("New projected monthly", f"\u20ac{new_total:.2f}", delta=f"+\u20ac{new_cost:.2f}")

        st.info(
            "This is a projection based on the hypothetical cost you entered above -- "
            "it is not a recorded transaction."
        )

        with st.expander("Show calculation logic"):
            st.code(calc_code, language="python")

    else:
        st.warning(UNSUPPORTED_MESSAGE)

else:
    st.info("Click a preset question above, or type your own, to get started.")
