import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
from nutrack_utils import show_sidebar_user_info, check_auth_and_profile

show_sidebar_user_info()
check_auth_and_profile()

# Supabase setup
url: str = st.secrets["supabase"]["SUPABASE_URL"]
key: str = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def set_supabase_auth():
    supabase.postgrest.auth(st.session_state.session.access_token)

def convert_to_json_serializable(data):
    """Convert numpy/pandas types to JSON serializable types"""
    if isinstance(data, dict):
        return {key: convert_to_json_serializable(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_to_json_serializable(item) for item in data]
    elif hasattr(data, 'dtype'):  # numpy/pandas types
        if hasattr(data, 'item'):  # scalar types
            return data.item()
        else:
            return int(data)
    else:
        return data

def filter_null_values(data):
    """Remove keys with None/NULL values from dictionary"""
    return {key: value for key, value in data.items() if value is not None}

def fetch_workouts():
    """Fetch user's workouts ordered by most recent first"""
    try:
        set_supabase_auth()
        response = supabase.table("workouts").select("*").order("created_at", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching workouts: {str(e)}")
        return pd.DataFrame()

def fetch_exercises():
    """Fetch available exercises"""
    try:
        set_supabase_auth()
        response = supabase.table("exercises").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching exercises: {str(e)}")
        return pd.DataFrame()

def fetch_workout_exercises(workout_id):
    """Fetch exercises for a specific workout with exercise details"""
    try:
        set_supabase_auth()
        response = supabase.table("workout_exercises").select("*, exercises(exercise_name)").eq("workout_id", workout
