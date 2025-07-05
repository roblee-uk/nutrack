import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, date
from nutrack_utils import show_sidebar_user_info, check_auth_and_profile

show_sidebar_user_info()
check_auth_and_profile()

# --- Supabase Client Initialization ---
url: str = st.secrets["supabase"]["SUPABASE_URL"]
key: str = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def set_supabase_auth():
    supabase.postgrest.auth(st.session_state.session.access_token)

def fetch_data(table):
    set_supabase_auth()
    response = supabase.table(table).select("*").execute()
    return pd.DataFrame(response.data)

def fetch_workout_exercises(workout_id):
    set_supabase_auth()
    response = supabase.table("workout_exercises").select('*, exercises(*)').eq("workout_id", workout_id).execute()
    df = pd.DataFrame(response.data)
    return df

def fetch_exercise_sets(workout_exercise_id):
    set_supabase_auth()
    response = supabase.table("exercise_sets").select("*").eq("workout_exercise_id", workout_exercise_id).execute()
    return pd.DataFrame(response.data)

# Fetch data
workouts = fetch_data("workouts")
exercises = fetch_data("exercises")

# Session state initialization
if "current_workout" not in st.session_state:
    st.session_state.current_workout = None
if "workout_exercises" not in st.session_state:
    st.session_state.workout_exercises = []

st.title("💪 Workouts")

# --- Create New Workout ---
st.subheader("Start New Workout", divider="blue")

with st.form("new_workout_form"):
    col1, col2 = st.columns(2)

    with col1:
        workout_name = st.text_input("Workout Name (optional)", placeholder="e.g. Push Day, Leg Day")
        workout_date = st.date_input("Workout Date", value=date.today())

    with col2:
        start_time = st.time_input("Start Time (optional)")

    if st.form_submit_button("Create Workout"):
        try:
            set_supabase_auth()

            # Combine date and time if provided
            start_timestamp = None
            if start_time:
                start_timestamp = datetime.combine(workout_date, start_time).isoformat()

            new_workout = {
                "workout_name": workout_name if workout_name else None,
                "workout_date": workout_date.isoformat(),
                "start_time": start_timestamp,
                "user_id": st.session_state.user.id
            }

            response = supabase.table("workouts").insert(new_workout).execute()

            if response.data:
                st.session_state.current_workout = response.data[0]
                st.success(f"Created workout successfully!")
                st.rerun()
            else:
                st.error("Failed to create workout")

        except Exception as e:
            st.error(f"Error creating workout: {str(e)}")

# --- Current Workout Session ---
if st.session_state.current_workout:
    workout = st.session_state.current_workout
    st.subheader(f"🎯 Current Workout: {workout.get('workout_name', 'Unnamed')} ({workout['workout_date']})", divider="green")

    # Add exercises to current workout
    with st.container(border=True):
        st.markdown("**Add Exercise to Workout**")

        if len(exercises) > 0:
            col1, col2 = st.columns([3, 1])

            with col1:
                selected_exercise = st.selectbox(
                    "Select Exercise", 
                    exercises['exercise_name'],
                    key="exercise_selector"
                )

            with col2:
                if st.button("Add Exercise"):
                    try:
                        set_supabase_auth()
                        exercise_id = exercises[exercises['exercise_name'] == selected_exercise]['exercise_id'].iloc[0]

                        # Get the order for this exercise in the workout
                        existing_exercises = fetch_workout_exercises(workout['workout_id'])
                        exercise_order = len(existing_exercises) + 1

                        new_workout_exercise = {
                            "workout_id": workout['workout_id'],
                            "exercise_id": exercise_id,
                            "exercise_order": exercise_order,
                            "user_id": st.session_state.user.id
                        }

                        response = supabase.table("workout_exercises").insert(new_workout_exercise).execute()

                        if response.data:
                            st.success(f"Added {selected_exercise} to workout!")
                            st.rerun()
                        else:
                            st.error("Failed to add exercise")

                    except Exception as e:
                        st.error(f"Error adding exercise: {str(e)}")
        else:
            st.info("No exercises available. Add some exercises first!")

    # Display current workout exercises
    workout_exercises_df = fetch_workout_exercises(workout['workout_id'])

    if len(workout_exercises_df) > 0:
        st.markdown("**Exercises in this workout:**")

        for idx, row in workout_exercises_df.iterrows():
            exercise_name = row['exercises']['exercise_name']
            exercise_type = row['exercises']['exercise_type']
            workout_exercise_id = row['workout_exercise_id']

            with st.expander(f"{row['exercise_order']}. {exercise_name} ({exercise_type})"):
                # Fetch existing sets for this exercise
                sets_df = fetch_exercise_sets(workout_exercise_id)

                if len(sets_df) > 0:
                    st.markdown("**Completed Sets:**")

                    # Display sets in a nice format
                    for _, set_row in sets_df.iterrows():
                        if exercise_type == 'strength':
                            if set_row['weight'] and set_row['reps']:
                                st.write(f"Set {set_row['set_number']}: {set_row['reps']} reps @ {set_row['weight']}kg")
                            elif set_row['reps']:
                                st.write(f"Set {set_row['set_number']}: {set_row['reps']} reps (bodyweight)")
                        else:  # cardio
                            if set_row['distance'] and set_row['duration_seconds']:
                                duration_min = set_row['duration_seconds'] // 60
                                st.write(f"Set {set_row['set_number']}: {set_row['distance']}km in {duration_min}min")
                            elif set_row['duration_seconds']:
                                duration_min = set_row['duration_seconds'] // 60
                                st.write(f"Set {set_row['set_number']}: {duration_min}min")

                # Add new set form
                st.markdown("**Add Set:**")

                with st.form(f"add_set_{workout_exercise_id}"):
                    if exercise_type == 'strength':
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            reps = st.number_input("Reps", min_value=1, step=1, key=f"reps_{workout_exercise_id}")
                        with col2:
                            weight = st.number_input("Weight (kg)", min_value=0.0, step=0.5, key=f"weight_{workout_exercise_id}")
                        with col3:
                            rest_seconds = st.number_input("Rest (sec)", min_value=0, step=15, value=60, key=f"rest_{workout_exercise_id}")

                        if st.form_submit_button("Add Set"):
                            try:
                                set_supabase_auth()
                                next_set_number = len(sets_df) + 1

                                new_set = {
                                    "workout_exercise_id": workout_exercise_id,
                                    "set_number": next_set_number,
                                    "reps": reps,
                                    "weight": weight if weight > 0 else None,
                                    "rest_seconds": rest_seconds if rest_seconds > 0 else None,
                                    "user_id": st.session_state.user.id
                                }

                                response = supabase.table("exercise_sets").insert(new_set).execute()

                                if response.data:
                                    st.success("Set added!")
                                    st.rerun()
                                else:
                                    st.error("Failed to add set")

                            except Exception as e:
                                st.error(f"Error adding set: {str(e)}")

                    else:  # cardio
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            distance = st.number_input("Distance (km)", min_value=0.0, step=0.1, key=f"distance_{workout_exercise_id}")
                        with col2:
                            duration_min = st.number_input("Duration (min)", min_value=1, step=1, key=f"duration_{workout_exercise_id}")
                        with col3:
                            rest_seconds = st.number_input("Rest (sec)", min_value=0, step=15, value=60, key=f"rest_cardio_{workout_exercise_id}")

                        if st.form_submit_button("Add Set"):
                            try:
                                set_supabase_auth()
                                next_set_number = len(sets_df) + 1

                                new_set = {
                                    "workout_exercise_id": workout_exercise_id,
                                    "set_number": next_set_number,
                                    "distance": distance if distance > 0 else None,
                                    "duration_seconds": duration_min * 60,
                                    "rest_seconds": rest_seconds if rest_seconds > 0 else None,
                                    "user_id": st.session_state.user.id
                                }

                                response = supabase.table("exercise_sets").insert(new_set).execute()

                                if response.data:
                                    st.success("Set added!")
                                    st.rerun()
                                else:
                                    st.error("Failed to add set")

                            except Exception as e:
                                st.error(f"Error adding set: {str(e)}")

    # Finish workout button
    st.markdown("---")
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("🏁 Finish Workout", type="primary"):
            try:
                set_supabase_auth()

                # Update workout with end time
                end_time = datetime.now().isoformat()
                update_data = {"end_time": end_time}

                response = supabase.table("workouts").update(update_data).eq("workout_id", workout['workout_id']).execute()

                if response.data:
                    st.success("Workout completed!")
                    st.session_state.current_workout = None
                    st.rerun()
                else:
                    st.error("Failed to finish workout")

            except Exception as e:
                st.error(f"Error finishing workout: {str(e)}")

    with col2:
        if st.button("❌ Cancel Workout"):
            st.session_state.current_workout = None
            st.rerun()

# --- Previous Workouts ---
st.subheader("Previous Workouts", divider="blue")

if len(workouts) > 0:
    # Sort by date descending
    workouts_sorted = workouts.sort_values('workout_date', ascending=False)

    for idx, workout in workouts_sorted.iterrows():
        workout_name = workout['workout_name'] or 'Unnamed Workout'
        workout_date = workout['workout_date']

        with st.expander(f"{workout_name} - {workout_date}"):
            # Show workout summary
            workout_exercises_df = fetch_workout_exercises(workout['workout_id'])

            if len(workout_exercises_df) > 0:
                for _, ex_row in workout_exercises_df.iterrows():
                    exercise_name = ex_row['exercises']['exercise_name']
                    sets_df = fetch_exercise_sets(ex_row['workout_exercise_id'])

                    st.write(f"**{exercise_name}** - {len(sets_df)} sets")

                    for _, set_row in sets_df.iterrows():
                        if ex_row['exercises']['exercise_type'] == 'strength':
                            if set_row['weight'] and set_row['reps']:
                                st.write(f"  Set {set_row['set_number']}: {set_row['reps']} reps @ {set_row['weight']}kg")
                            elif set_row['reps']:
                                st.write(f"  Set {set_row['set_number']}: {set_row['reps']} reps (bodyweight)")
                        else:
                            if set_row['distance'] and set_row['duration_seconds']:
                                duration_min = set_row['duration_seconds'] // 60
                                st.write(f"  Set {set_row['set_number']}: {set_row['distance']}km in {duration_min}min")
                            elif set_row['duration_seconds']:
                                duration_min = set_row['duration_seconds'] // 60
                                st.write(f"  Set {set_row['set_number']}: {duration_min}min")
            else:
                st.write("No exercises recorded for this workout.")
else:
    st.info("No previous workouts found. Start your first workout above!")
