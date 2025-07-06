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
        response = supabase.table("workout_exercises").select("*, exercises(exercise_name)").eq("workout_id", workout_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching workout exercises: {str(e)}")
        return []

st.title("Workout Tracking")

# Section 1: Quick Workout Creation
st.subheader("Create New Workout", divider="blue")

with st.form("quick_workout_form", clear_on_submit=True):
    workout_name = st.text_input("Workout Name", placeholder="e.g., Push Day, Legs, Cardio")
    workout_notes = st.text_area("Notes (optional)", placeholder="Any additional notes about this workout")
    
    if st.form_submit_button("Create Workout"):
        if not workout_name.strip():
            st.error("Please enter a workout name")
        else:
            try:
                set_supabase_auth()
                current_time = datetime.now().isoformat()
                
                new_workout = {
                    "user_id": st.session_state.session.user.id,
                    "workout_name": workout_name.strip(),
                    "notes": workout_notes.strip() if workout_notes.strip() else None,
                    "created_at": current_time,
                    "updated_at": current_time
                }
                
                # Filter out None values and apply JSON serialization fix
                clean_workout = convert_to_json_serializable(filter_null_values(new_workout))
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
                
                # Create exercise log data - only include non-None values
                new_exercise_log = {
                    "workout_id": selected_workout_id,
                    "exercise_id": exercise_id,
                    "user_id": st.session_state.session.user.id,
                    "created_at": datetime.now().isoformat()
                }
                
                # Add exercise-specific fields only if they have values
                if sets is not None:
                    new_exercise_log["sets"] = sets
                if reps is not None:
                    new_exercise_log["reps"] = reps
                if weight is not None and weight > 0:
                    new_exercise_log["weight"] = weight
                if duration is not None and duration > 0:
                    new_exercise_log["duration"] = duration
                if distance is not None and distance > 0:
                    new_exercise_log["distance"] = distance
                
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
    for idx, workout in workouts.head(5).iterrows():
        workout_exercises = fetch_workout_exercises(workout['workout_id'])
        
        with st.expander(f"{workout['workout_name']} - {workout['created_at'][:10]} ({len(workout_exercises)} exercises)"):
            if workout_exercises:
                for exercise in workout_exercises:
                    exercise_name = exercise['exercises']['exercise_name']
                    details = []
                    
                    # Build exercise details string based on available data
                    if exercise.get('sets') and exercise.get('reps') and exercise.get('weight'):
                        details.append(f"{exercise['sets']} sets × {exercise['reps']} reps @ {exercise['weight']}kg")
                    elif exercise.get('sets') and exercise.get('reps'):
                        details.append(f"{exercise['sets']} sets × {exercise['reps']} reps")
                    
                    if exercise.get('duration'):
                        details.append(f"{exercise['duration']} min")
                    
                    if exercise.get('distance'):
                        details.append(f"{exercise['distance']} km")
                    
                    detail_text = " | ".join(details) if details else "No details recorded"
                    st.write(f"• {exercise_name}: {detail_text}")
            else:
                st.write("No exercises logged yet")
            
            # Show notes if available
            if workout.get('notes'):
                st.write(f"**Notes:** {workout['notes']}")

# Section 4: Quick Stats
if not workouts.empty:
    st.subheader("Quick Stats", divider="blue")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Workouts", len(workouts))
    
    with col2:
        # Count total exercises across all workouts
        total_exercises = 0
        for _, workout in workouts.iterrows():
            workout_exercises = fetch_workout_exercises(workout['workout_id'])
            total_exercises += len(workout_exercises)
        st.metric("Total Exercises Logged", total_exercises)
    
    with col3:
        # Show most recent workout date
        if not workouts.empty:
            latest_workout = workouts.iloc[0]
            latest_date = latest_workout['created_at'][:10]
            st.metric("Last Workout", latest_date)

# Help Section
with st.expander("ℹ️ Help & Tips"):
    st.write("""
    **How to use this page:**
    
    1. **Create a workout** - Enter a name and any notes, then click "Create Workout"
    2. **Log exercises** - Select your workout (most recent is selected by default), choose an exercise, enter your details
    3. **View history** - Expand recent workouts to see what exercises you've logged
    
    **Tips:**
    - Workouts are automatically ordered by most recent first
    - You can mix strength and cardio exercises in the same workout
    - Only non-zero values are saved (empty fields are ignored)
    - Your workout history shows a summary of each session
    """)
