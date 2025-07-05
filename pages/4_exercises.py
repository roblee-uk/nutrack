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
def fetch_and_display_exercises():
    try:
        set_supabase_auth()
        response = supabase.table("exercises").select("*").execute()
        df = pd.DataFrame(response.data)

        if len(df) > 0:
            # Display relevant columns
            display_columns = ['exercise_name', 'exercise_type', 'muscle_groups', 'equipment']
            df_visible = df[display_columns]
            st.dataframe(df_visible, hide_index=True, use_container_width=True)
        else:
            st.info("No exercises found. Add some exercises below!")

    except Exception as e:
        st.error(f"Data fetch failed: {str(e)}")

st.title("🏋️ Exercise Database")

fetch_and_display_exercises()

# --- Exercise Submission Form ---
st.subheader("Add New Exercise", divider="blue")

with st.form("new_exercise_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Exercise Name", placeholder="e.g. Bench Press")
        exercise_type = st.selectbox("Exercise Type", ["strength", "cardio"])
        equipment = st.text_input("Equipment", placeholder="e.g. barbell, dumbbell, none")

    with col2:
        # Muscle groups as multiselect
        muscle_options = [
            "chest", "back", "shoulders", "biceps", "triceps", 
            "quadriceps", "hamstrings", "glutes", "calves", 
            "core", "cardiovascular"
        ]
        muscle_groups = st.multiselect("Muscle Groups", muscle_options)

    instructions = st.text_area("Instructions (optional)", 
                               placeholder="Describe how to perform this exercise...")

    if st.form_submit_button("Add Exercise"):
        if name and exercise_type:
            try:
                set_supabase_auth()
                new_exercise = {
                    "exercise_name": name,
                    "exercise_type": exercise_type,
                    "muscle_groups": muscle_groups,
                    "equipment": equipment if equipment else None,
                    "instructions": instructions if instructions else None,
                    "user_id": st.session_state.user.id
                }

                response = supabase.table("exercises").insert(new_exercise).execute()

                if response.data:
                    st.success(f"Added {name} successfully!")
                    st.rerun()
                else:
                    st.error("Insert failed. Check RLS policies.")

            except Exception as e:
                st.error(f"Insert error: {str(e)}")
        else:
            st.error("Please fill in at least the exercise name and type.")

# --- Tips and Help ---
with st.expander("💡 Tips for Adding Exercises"):
    st.markdown("""
    **Exercise Types:**
    - **Strength**: Weight training exercises (bench press, squats, etc.)
    - **Cardio**: Endurance exercises (running, cycling, etc.)

    **Muscle Groups:**
    - Select all muscle groups that the exercise targets
    - This helps with filtering and workout planning

    **Equipment:**
    - Be specific (e.g., "barbell" vs "dumbbell")
    - Use "bodyweight" for exercises requiring no equipment
    """)
