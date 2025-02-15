import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# Initialize Supabase client
url: str = st.secrets["supabase"]["SUPABASE_URL"]
key: str = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# Function to fetch and display data
def fetch_and_display_data():
    response = supabase.table("foods").select("*").execute()
    df = pd.DataFrame(response.data)
    st.dataframe(df)

# Display existing data
st.title("Foods Database")
fetch_and_display_data()

# Form for new food entry
st.subheader("Add New Food")
with st.form("new_food_form", clear_on_submit=True,):
    name = st.text_input("Food Name")
    protein = st.number_input("Protein Content (g)", min_value=0.0, step=0.1)
    carbs = st.number_input("Carbohydrate Content (g)", min_value=0.0, step=0.1)
    sugars = st.number_input("of which sugars (g)", min_value=0.0, step=0.1)
    fat = st.number_input("Fat Content (g)", min_value=0.0, step=0.1)
    sats = st.number_input("of which saturates (g)", min_value=0.0, step=0.1)
    fiber = st.number_input("Fiber Content (g)", min_value=0.0, step=0.1)
    
    submitted = st.form_submit_button("Add Food")
    
    if submitted:
        current_time = datetime.now().isoformat()
        new_food = {
            "food_name": name,
            "protein": protein,
            "carbohydrates": carbs,
            "sugars": sugars,
            "fat": fat,
            "saturates": sats,
            "fiber": fiber,
            "created_at": current_time,
            "updated_at": current_time
        }
        
        response = supabase.table("foods").insert(new_food).execute()
        
        if response.data:
            st.success(f"Successfully added {name} to the database!")
            st.rerun()
        else:
            st.error("Failed to add food to the database. Please try again.")