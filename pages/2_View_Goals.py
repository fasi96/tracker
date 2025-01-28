import streamlit as st
from utils import load_data, show_dashboard

st.title("View Goals 📊")

df = load_data()

if df.empty:
    st.info("No goals created yet. Create your first goal in the 'Create Goal' page!")
else:
    show_dashboard(df) 