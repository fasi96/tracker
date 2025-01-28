import streamlit as st
import pandas as pd
import os
import ast
from datetime import datetime, date, timedelta
from streamlit_calendar import calendar


def migrate_data():
    data_dir = "data"
    csv_path = os.path.join(data_dir, "goals.csv")
    
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            if "notes" not in df.columns:
                df["notes"] = ["{}" for _ in range(len(df))]
                df.to_csv(csv_path, index=False)
                st.success("Data file updated successfully!")
        except Exception as e:
            st.error(f"Error migrating data: {str(e)}")

def initialize_data():
    data_dir = "data"
    csv_path = os.path.join(data_dir, "goals.csv")
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    if not os.path.exists(csv_path):
        pd.DataFrame(columns=[
            "goal_id", "title", "target_value", "tracking_type",
            "start_date", "end_date", "progress_logs", "notes"
        ]).to_csv(csv_path, index=False)
    
    migrate_data()

def load_data():
    initialize_data()
    try:
        df = pd.read_csv("data/goals.csv")
        
        if df.empty:
            return df
        
        df["start_date"] = pd.to_datetime(df["start_date"]).dt.date
        df["end_date"] = pd.to_datetime(df["end_date"]).dt.date
        
        # Convert progress_logs from string to dict
        df["progress_logs"] = df["progress_logs"].apply(
            lambda x: {datetime.strptime(d, "%Y-%m-%d").date(): v 
                      for d, v in ast.literal_eval(x).items()}
            if pd.notnull(x) and x != "{}" else {}
        )
        
        # Convert notes from string to dict
        df["notes"] = df["notes"].apply(
            lambda x: ast.literal_eval(x) if pd.notnull(x) and x != "{}" else {}
        )
        
        return df
    
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame(columns=[
            "goal_id", "title", "target_value", "tracking_type",
            "start_date", "end_date", "progress_logs", "notes"
        ])

def save_data(df):
    df_copy = df.copy()
    df_copy["start_date"] = df_copy["start_date"].astype(str)
    df_copy["end_date"] = df_copy["end_date"].astype(str)
    df_copy["progress_logs"] = df_copy["progress_logs"].apply(
        lambda x: {d.isoformat(): v for d, v in x.items()} if x else {}
    )
    df_copy.to_csv("data/goals.csv", index=False)

def create_goal():
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
            st.success("Goal saved!")

def log_progress(df):
    st.subheader("Log Progress")
    if not df.empty:
        selected_goal = st.selectbox("Select Goal", df["title"].unique())
        goal_idx = df[df["title"] == selected_goal].index[0]
        goal = df.iloc[goal_idx]
        
        session_date = st.date_input("Date", date.today())
        note = st.text_area("Notes (How did it go? How do you feel?)", 
                           help="Add any thoughts, reflections, or details about today's progress")
        
        if goal["tracking_type"] == "hours":
            hours = st.number_input("Hours", min_value=0.0, max_value=24.0, step=0.5)
            if st.button("Log Hours"):
                current_hours = goal["progress_logs"].get(session_date, 0)
                df.at[goal_idx, "progress_logs"][session_date] = current_hours + hours
                # Store the note
                if "notes" not in df.columns:
                    df["notes"] = [{} for _ in range(len(df))]
                if note.strip():  # Only save if note isn't empty
                    df.at[goal_idx, "notes"][session_date.isoformat()] = note
                save_data(df)
                st.success("Progress and notes logged!")
                st.rerun()
        else:  # sessions
            if st.button("Log Session"):
                if session_date not in goal["progress_logs"]:
                    df.at[goal_idx, "progress_logs"][session_date] = 1
                    # Store the note
                    if "notes" not in df.columns:
                        df["notes"] = [{} for _ in range(len(df))]
                    if note.strip():  # Only save if note isn't empty
                        df.at[goal_idx, "notes"][session_date.isoformat()] = note
                    save_data(df)
                    st.success("Progress and notes logged!")
                    st.rerun()
                else:
                    st.warning("Session already logged for this date!")

def calculate_required_pace(goal):
    today = date.today()
    total_days = (goal["end_date"] - goal["start_date"]).days
    days_passed = (today - goal["start_date"]).days
    current_progress = sum(goal["progress_logs"].values())
    remaining = goal["target_value"] - current_progress
    days_left = total_days - days_passed
    
    if days_left <= 0 or remaining <= 0:
        return 0
    return remaining / days_left * 7  # Per week needed

def generate_calendar_events(goal):
    events = []
    for log_date, value in goal["progress_logs"].items():
        note = goal.get("notes", {}).get(log_date.isoformat(), "")
        title = f"{value} {'session' if goal['tracking_type'] == 'sessions' else 'hours'}"
        if note:
            title += f"\n📝 {note[:50]}..." if len(note) > 50 else f"\n📝 {note}"
        
        event = {
            "title": title,
            "start": log_date.isoformat(),
            "end": log_date.isoformat(),
            "backgroundColor": "#28a745" if goal["tracking_type"] == "sessions" else "#007bff",
            "textColor": "#ffffff",
            "display": "block"
        }
        events.append(event)
    return events

def show_dashboard(df):
    st.subheader("Dashboard")
    for idx, goal in df.iterrows():
        with st.expander(f"{goal['title']} - {goal['tracking_type'].title()}"):
            # Add management buttons in a row
            manage_col1, manage_col2, manage_col3 = st.columns([1, 1, 2])
            
            with manage_col1:
                if st.button("🗑️ Delete Goal", key=f"delete_{goal['goal_id']}"):
                    if st.warning("Are you sure you want to delete this goal?"):
                        df.drop(idx, inplace=True)
                        save_data(df)
                        st.rerun()
            
            with manage_col2:
                if st.button("✏️ Edit Goal", key=f"edit_{goal['goal_id']}"):
                    st.session_state[f"editing_{goal['goal_id']}"] = True
            
            # Show edit form if editing is active
            if st.session_state.get(f"editing_{goal['goal_id']}", False):
                with st.form(key=f"edit_form_{goal['goal_id']}"):
                    new_title = st.text_input("Goal Title", value=goal['title'])
                    new_target = st.number_input(
                        f"Target {goal['tracking_type'].title()}/Year",
                        value=goal['target_value'],
                        min_value=1,
                        step=1
                    )
                    new_end_date = st.date_input("End Date", value=goal['end_date'])
                    
                    if st.form_submit_button("Save Changes"):
                        df.at[idx, 'title'] = new_title
                        df.at[idx, 'target_value'] = new_target
                        df.at[idx, 'end_date'] = new_end_date
                        save_data(df)
                        st.session_state[f"editing_{goal['goal_id']}"] = False
                        st.rerun()
                    
                    if st.form_submit_button("Cancel"):
                        st.session_state[f"editing_{goal['goal_id']}"] = False
                        st.rerun()
            
            # Progress
            current_progress = sum(goal["progress_logs"].values())
            progress = min(1.0, current_progress / goal["target_value"])
            st.progress(progress)
            unit = "sessions" if goal["tracking_type"] == "sessions" else "hours"
            st.write(f"**{current_progress}/{goal['target_value']} {unit}**")
            
            # Catch-up alerts
            required_pace = calculate_required_pace(goal)
            expected_pace = goal["target_value"] / ((goal["end_date"] - goal["start_date"]).days / 7)
            if required_pace > expected_pace * 1.1:  # 10% tolerance
                st.error(f"Speed up! Target **{required_pace:.1f} {unit}/week** (originally {expected_pace:.1f}).")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Time-based progress chart
                if goal["progress_logs"]:
                    progress_df = pd.DataFrame(
                        {"value": goal["progress_logs"].values()},
                        index=pd.to_datetime(list(goal["progress_logs"].keys()))
                    )
                    progress_df["cumulative"] = progress_df["value"].cumsum()
                    st.line_chart(progress_df["cumulative"], use_container_width=True)
            
            with col2:
                # Calendar view
                calendar_options = {
                    "headerToolbar": {
                        "left": "prev,next",
                        "center": "title",
                        "right": "today"
                    },
                    "initialView": "dayGridMonth",
                    "selectable": True,
                    "height": 350,
                }
                
                events = generate_calendar_events(goal)
                calendar(events=events, options=calendar_options)