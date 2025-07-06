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

def fetch_workouts():
    """Fetch user's workouts ordered by most recent first"""
    set_supabase_auth()
    response = supabase.table("workouts").select("*").order("created_at", desc=True).execute()
    return pd.DataFrame(response.data)

def fetch_exercises():
    """Fetch available exercises"""
    set_supabase_auth()
    response = supabase.table("exercises").select("*").execute()
    return pd.DataFrame(response.data)

st.title("Workout Tracking")

# Section 1: Quick Workout Creation
st.subheader("Create New Workout", divider="blue")

with st.form("quick_workout_form", clear_on_submit=True):
    workout_name = st.text_input("Workout Name", placeholder="e.g., Push Day, Legs, Cardio")
    workout_notes = st.text_area("Notes (optional)", placeholder="Any additional notes about this workout")
    
    if st.form_submit_button("Create Workout"):
        try:
            set_supabase_auth()
            current_time = datetime.now().isoformat()
            
            new_workout = {
                "user_id": st.session_state.session.user.id,
                "workout_name": workout_name,
                "notes": workout_notes,
                "created_at": current_time,
                "updated_at": current_time
            }
            
            # Apply JSON serialization fix
            clean_workout = convert_to_json_serializable(new_workout)
            response = supabase.table("workouts").insert(clean_workout).execute()
            
            if response.data:
                st.success(f"Created workout: {workout_name}")
                st.rerun()
            else:
                st.error("Failed to create workout")
                
        except Exception as e:
            st.error(f"Error creating workout: {str(e)}")

# Section 2: Exercise Logging
st.subheader("Log Exercise", divider="blue")

workouts = fetch_workouts()
exercises = fetch_exercises()

if not workouts.empty and not exercises.empty:
    
    # Workout selection dropdown (most recent first)
    workout_options = workouts['workout_name'].tolist()
    selected_workout_name = st.selectbox(
        "Select Workout", 
        options=workout_options,
        index=0,  # Default to most recent workout
        help="Most recent workout is selected by default"
    )
    
    # Get the selected workout ID
    selected_workout_id = workouts[workouts['workout_name'] == selected_workout_name]['workout_id'].iloc[0]
    
    # Exercise logging form
    with st.form("exercise_log_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            exercise_name = st.selectbox("Exercise", exercises['exercise_name'])
            exercise_type = st.radio("Type", ["Strength", "Cardio"])
        
        with col2:
            if exercise_type == "Strength":
                sets = st.number_input("Sets", min_value=1, value=1, step=1)
                reps = st.number_input("Reps", min_value=1, value=1, step=1)
                weight = st.number_input("Weight (kg)", min_value=0.0, value=0.0, step=0.5)
                duration = None
                distance = None
            else:  # Cardio
                duration = st.number_input("Duration (minutes)", min_value=0.0, value=0.0, step=0.5)
                distance = st.number_input("Distance (km)", min_value=0.0, value=0.0, step=0.1)
                sets = None
                reps = None
                weight = None
        
        if st.form_submit_button("Log Exercise"):
            try:
                set_supabase_auth()
                
                # Get exercise ID
                exercise_id = exercises[exercises['exercise_name'] == exercise_name]['exercise_id'].iloc[0]
                
                new_exercise_log = {
                    "workout_id": selected_workout_id,
                    "exercise_id": exercise_id,
                    "user_id": st.session_state.session.user.id,
                    "sets": sets,
                    "reps": reps,
                    "weight": weight,
                    "duration": duration,
                    "distance": distance,
                    "created_at": datetime.now().isoformat()
                }
                
                # Apply JSON serialization fix
                clean_exercise_log = convert_to_json_serializable(new_exercise_log)
                response = supabase.table("workout_exercises").insert(clean_exercise_log).execute()
                
                if response.data:
                    st.success(f"Logged {exercise_name} for {selected_workout_name}")
                    st.rerun()
                else:
                    st.error("Failed to log exercise")
                    
            except Exception as e:
                st.error(f"Error logging exercise: {str(e)}")

else:
    if workouts.empty:
        st.info("Create your first workout above to start logging exercises!")
    if exercises.empty:
        st.info("Add some exercises first using the Exercise Management page!")

# Section 3: Current Workout Summary
if not workouts.empty:
    st.subheader("Recent Workouts", divider="blue")
    
    # Show expandable summaries of recent workouts
    for idx, workout in workouts.head(3).iterrows():
        with st.expander(f"{workout['workout_name']} - {workout['created_at'][:10]}"):
            # Fetch exercises for this workout
            set_supabase_auth()
            workout_exercises = supabase.table("workout_exercises").select("*, exercises(exercise_name)").eq("workout_id", workout['workout_id']).execute()
            
            if workout_exercises.data:
                for exercise in workout_exercises.data:
                    exercise_name = exercise['exercises']['exercise_name']
                    if exercise['sets'] and exercise['reps'] and exercise['weight']:
                        st.write(f"• {exercise_name}: {exercise['sets']} sets × {exercise['reps']} reps @ {exercise['weight']}kg")
                    elif exercise['duration'] and exercise['distance']:
                        st.write(f"• {exercise_name}: {exercise['duration']} min, {exercise['distance']} km")
                    elif exercise['duration']:
                        st.write(f"• {exercise_name}: {exercise['duration']} min")
            else:
                st.write("No exercises logged yet")
