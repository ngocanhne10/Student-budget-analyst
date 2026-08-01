"""
data_utils.py
Loading and filtering helpers for the student budget dataset.
Keeping this separate from app.py so the data layer stays testable
independent of Streamlit.
"""

import pandas as pd

# Calendar-accurate weeks-per-month, used everywhere we project
# weekly figures into a monthly estimate. Using 4.348 instead of a
# flat "4" avoids silently understating monthly totals.
WEEKS_PER_MONTH = 365.25 / 12 / 7  # ~4.348

DATA_PATH = "student_budget_dataset.csv"


def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df


def get_students(df: pd.DataFrame) -> pd.DataFrame:
    """Distinct student_id/location pairs, for the student picker."""
    return df[["student_id", "location"]].drop_duplicates().reset_index(drop=True)


def filter_student(df: pd.DataFrame, student_id: str) -> pd.DataFrame:
    return df[df.student_id == student_id].copy()


def num_weeks(df: pd.DataFrame) -> int:
    """How many distinct weeks are in the (already student-filtered) data.
    Used instead of hardcoding '5' so the app keeps working if you extend
    the dataset with more weeks later.
    """
    return df["week_number"].nunique()
