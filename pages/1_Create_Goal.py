import streamlit as st
from datetime import date
import uuid
from utils import load_data, save_data
import pandas as pd

st.title("Create New Goal ✨")

with st.form("Create Goal"):
    title = st.text_input("Goal Title (e.g., Gym Sessions, Learn Django)")
    tracking_type = st.selectbox(
        "Tracking Type",
        options=["sessions", "hours"],
        help="'sessions' allows 1 per day, 'hours' allows multiple entries per day"
    )
    target_label = f"Target {'Sessions' if tracking_type == 'sessions' else 'Hours'}/Year"
    target = st.number_input(target_label, min_value=1, step=1)
    start_date = st.date_input("Start Date", date.today())
    end_date = st.date_input("End Date", date(date.today().year, 12, 31))
    
    if st.form_submit_button("Save Goal"):
        new_goal = {
            "goal_id": str(uuid.uuid4()),
            "title": title,
            "target_value": target,
            "tracking_type": tracking_type,
            "start_date": start_date,
            "end_date": end_date,
            "progress_logs": {}
        }
        df = load_data()
        df = pd.concat([df, pd.DataFrame([new_goal])], ignore_index=True)
        save_data(df)
        st.success("Goal saved successfully! 🎉") 