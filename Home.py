import streamlit as st
import pandas as pd
from datetime import date
from utils import load_data, log_progress, show_dashboard

def main():
    st.title("Time-Based Goal Tracker 🎯")
    st.write("""
    Welcome to your Goal Tracker! 🎯
    
    Use the sidebar to:
    - Create new goals
    - View and track your existing goals
    
    Get started by creating a new goal or check your progress on existing ones!
    """)
    
    # Show quick summary if there are any goals
    df = load_data()
    if not df.empty:
        st.subheader("Quick Actions")
        log_progress(df)

if __name__ == "__main__":
    main() 