import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
from nutrack_utils import show_sidebar_user_info, check_auth_and_profile

show_sidebar_user_info()
check_auth_and_profile()

# --- Supabase Client Initialization ---
url: str = st.secrets["supabase"]["SUPABASE_URL"]
key: str = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- Always set the access token before any DB operation ---
def set_supabase_auth():
    # This ensures all subsequent queries use the logged-in user's session
    supabase.postgrest.auth(st.session_state.session.access_token)

# --- Main Page Content ---
def fetch_and_display_data():
    try:
        set_supabase_auth()
        response = supabase.table("foods").select("*").execute()
        df = pd.DataFrame(response.data)
        # Drop the last 3 columns
        df_visible = df.iloc[:, 1:-3]

        # Identify numeric columns and round them to 2 decimal places
        numeric_cols = df_visible.select_dtypes(include="number").columns
        for col in df_visible.select_dtypes(include="number").columns:
            df_visible[col] = df_visible[col].map("{:.2f}".format)
        
        st.table(df_visible)
    except Exception as e:
        st.error(f"Data fetch failed: {str(e)}")

st.title("Foods Database")
fetch_and_display_data()

# --- Food Submission Form ---
with st.form("new_food_form", clear_on_submit=True):
    name = st.text_input("Food Name")
    protein = st.number_input("Protein Content (g)", min_value=0.0, step=0.1)
    carbs = st.number_input("Carbohydrate Content (g)", min_value=0.0, step=0.1)
    sugars = st.number_input("of which sugars (g)", min_value=0.0, step=0.1)
    fat = st.number_input("Fat Content (g)", min_value=0.0, step=0.1)
    sats = st.number_input("of which saturates (g)", min_value=0.0, step=0.1)
    fiber = st.number_input("Fiber Content (g)", min_value=0.0, step=0.1)
    
    if st.form_submit_button("Add Food"):
        try:
            set_supabase_auth()
            new_food = {
                "food_name": name,
                "protein": protein,
                "carbohydrates": carbs,
                "sugars": sugars,
                "fat": fat,
                "saturates": sats,
                "fiber": fiber,
                "user_id": st.session_state.user.id  # Add user ownership
            }
            response = supabase.table("foods").insert(new_food).execute()
            if response.data:
                st.success(f"Added {name} successfully!")
                st.rerun()
            else:
                st.error("Insert failed. Check RLS policies.")
        except Exception as e:
            st.error(f"Insert error: {str(e)}")
