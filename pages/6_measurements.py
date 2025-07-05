import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, date
import plotly.express as px
from nutrack_utils import show_sidebar_user_info, check_auth_and_profile

show_sidebar_user_info()
check_auth_and_profile()

# --- Supabase Client Initialization ---
url: str = st.secrets["supabase"]["SUPABASE_URL"]
key: str = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def set_supabase_auth():
    supabase.postgrest.auth(st.session_state.session.access_token)

def fetch_body_measurements():
    set_supabase_auth()
    response = supabase.table("body_measurements").select("*").order("measurement_date", desc=True).execute()
    return pd.DataFrame(response.data)

def fetch_custom_measurements(body_measurement_id):
    set_supabase_auth()
    response = supabase.table("custom_measurements").select("*").eq("body_measurement_id", body_measurement_id).execute()
    return pd.DataFrame(response.data)

def fetch_all_custom_measurements():
    set_supabase_auth()
    response = supabase.table("custom_measurements").select("*, body_measurements(measurement_date)").execute()
    return pd.DataFrame(response.data)

st.title("📏 Body Measurements")

# Fetch existing measurements
measurements_df = fetch_body_measurements()

# --- Add New Measurement ---
st.subheader("Record New Measurements", divider="blue")

with st.form("new_measurement_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        measurement_date = st.date_input("Date", value=date.today())
        weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1, help="Your body weight")
        body_fat = st.number_input("Body Fat %", min_value=0.0, max_value=100.0, step=0.1, help="Optional")

    with col2:
        muscle_mass = st.number_input("Muscle Mass (kg)", min_value=0.0, step=0.1, help="Optional")

        # Custom measurements
        st.markdown("**Custom Measurements (optional):**")
        custom_chest = st.number_input("Chest (cm)", min_value=0.0, step=0.1, key="chest")
        custom_waist = st.number_input("Waist (cm)", min_value=0.0, step=0.1, key="waist")
        custom_hips = st.number_input("Hips (cm)", min_value=0.0, step=0.1, key="hips")

    # Additional custom measurements
    with st.expander("More Custom Measurements"):
        col3, col4 = st.columns(2)
        with col3:
            custom_bicep_l = st.number_input("Left Bicep (cm)", min_value=0.0, step=0.1, key="bicep_l")
            custom_bicep_r = st.number_input("Right Bicep (cm)", min_value=0.0, step=0.1, key="bicep_r")
            custom_thigh_l = st.number_input("Left Thigh (cm)", min_value=0.0, step=0.1, key="thigh_l")
        with col4:
            custom_thigh_r = st.number_input("Right Thigh (cm)", min_value=0.0, step=0.1, key="thigh_r")
            custom_neck = st.number_input("Neck (cm)", min_value=0.0, step=0.1, key="neck")
            custom_forearm = st.number_input("Forearm (cm)", min_value=0.0, step=0.1, key="forearm")

    if st.form_submit_button("Save Measurements"):
        if weight > 0:
            try:
                set_supabase_auth()

                # Insert main body measurement
                new_measurement = {
                    "measurement_date": measurement_date.isoformat(),
                    "weight": weight,
                    "body_fat_percentage": body_fat if body_fat > 0 else None,
                    "muscle_mass": muscle_mass if muscle_mass > 0 else None,
                    "user_id": st.session_state.user.id
                }

                response = supabase.table("body_measurements").insert(new_measurement).execute()

                if response.data:
                    body_measurement_id = response.data[0]['measurement_id']

                    # Insert custom measurements if provided
                    custom_measurements = []

                    custom_data = {
                        "chest": custom_chest,
                        "waist": custom_waist, 
                        "hips": custom_hips,
                        "bicep_left": custom_bicep_l,
                        "bicep_right": custom_bicep_r,
                        "thigh_left": custom_thigh_l,
                        "thigh_right": custom_thigh_r,
                        "neck": custom_neck,
                        "forearm": custom_forearm
                    }

                    for measurement_name, value in custom_data.items():
                        if value > 0:
                            custom_measurements.append({
                                "body_measurement_id": body_measurement_id,
                                "measurement_name": measurement_name,
                                "measurement_value": value,
                                "unit": "cm",
                                "user_id": st.session_state.user.id
                            })

                    if custom_measurements:
                        custom_response = supabase.table("custom_measurements").insert(custom_measurements).execute()

                        if custom_response.data:
                            st.success(f"Saved measurements for {measurement_date} with {len(custom_measurements)} custom measurements!")
                        else:
                            st.warning("Main measurements saved, but custom measurements failed.")
                    else:
                        st.success(f"Saved measurements for {measurement_date}!")

                    st.rerun()
                else:
                    st.error("Failed to save measurements")

            except Exception as e:
                st.error(f"Error saving measurements: {str(e)}")
        else:
            st.error("Please enter at least your weight.")

# --- Display Recent Measurements ---
if len(measurements_df) > 0:
    st.subheader("Recent Measurements", divider="blue")

    # Display latest measurements
    latest = measurements_df.iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Latest Weight", f"{latest['weight']:.1f} kg", 
                 delta=f"{latest['weight'] - measurements_df.iloc[1]['weight']:.1f} kg" if len(measurements_df) > 1 else None)

    with col2:
        if latest['body_fat_percentage']:
            delta_bf = f"{latest['body_fat_percentage'] - measurements_df.iloc[1]['body_fat_percentage']:.1f}%" if len(measurements_df) > 1 and measurements_df.iloc[1]['body_fat_percentage'] else None
            st.metric("Body Fat", f"{latest['body_fat_percentage']:.1f}%", delta=delta_bf)
        else:
            st.metric("Body Fat", "Not recorded")

    with col3:
        if latest['muscle_mass']:
            delta_mm = f"{latest['muscle_mass'] - measurements_df.iloc[1]['muscle_mass']:.1f} kg" if len(measurements_df) > 1 and measurements_df.iloc[1]['muscle_mass'] else None
            st.metric("Muscle Mass", f"{latest['muscle_mass']:.1f} kg", delta=delta_mm)
        else:
            st.metric("Muscle Mass", "Not recorded")

    with col4:
        st.metric("Last Recorded", latest['measurement_date'])

    # --- Charts ---
    st.subheader("Progress Charts", divider="blue")

    chart_tab1, chart_tab2, chart_tab3 = st.tabs(["Weight", "Body Fat %", "Custom Measurements"])

    with chart_tab1:
        if len(measurements_df) > 1:
            fig = px.line(measurements_df, x='measurement_date', y='weight', 
                         title='Weight Progress', markers=True)
            fig.update_layout(xaxis_title="Date", yaxis_title="Weight (kg)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Need at least 2 measurements to show progress chart")

    with chart_tab2:
        body_fat_data = measurements_df[measurements_df['body_fat_percentage'].notna()]
        if len(body_fat_data) > 1:
            fig = px.line(body_fat_data, x='measurement_date', y='body_fat_percentage',
                         title='Body Fat Progress', markers=True)
            fig.update_layout(xaxis_title="Date", yaxis_title="Body Fat %")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Need at least 2 body fat measurements to show progress chart")

    with chart_tab3:
        custom_df = fetch_all_custom_measurements()
        if len(custom_df) > 0:
            # Expand the body_measurements data
            custom_df['measurement_date'] = custom_df['body_measurements'].apply(lambda x: x['measurement_date'] if x else None)

            # Let user select which measurement to chart
            available_measurements = custom_df['measurement_name'].unique()
            if len(available_measurements) > 0:
                selected_measurement = st.selectbox("Select measurement to chart:", available_measurements)

                measurement_data = custom_df[custom_df['measurement_name'] == selected_measurement]
                if len(measurement_data) > 1:
                    fig = px.line(measurement_data, x='measurement_date', y='measurement_value',
                                 title=f'{selected_measurement.replace("_", " ").title()} Progress', markers=True)
                    fig.update_layout(xaxis_title="Date", yaxis_title=f"{selected_measurement.replace('_', ' ').title()} (cm)")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"Need at least 2 {selected_measurement} measurements to show progress chart")
            else:
                st.info("No custom measurements recorded yet")
        else:
            st.info("No custom measurements recorded yet")

    # --- Measurement History ---
    st.subheader("Measurement History", divider="blue")

    for idx, measurement in measurements_df.iterrows():
        with st.expander(f"📅 {measurement['measurement_date']} - Weight: {measurement['weight']:.1f}kg"):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Weight:** {measurement['weight']:.1f} kg")
                if measurement['body_fat_percentage']:
                    st.write(f"**Body Fat:** {measurement['body_fat_percentage']:.1f}%")
                if measurement['muscle_mass']:
                    st.write(f"**Muscle Mass:** {measurement['muscle_mass']:.1f} kg")

            with col2:
                # Show custom measurements for this date
                custom_measurements = fetch_custom_measurements(measurement['measurement_id'])
                if len(custom_measurements) > 0:
                    st.write("**Custom Measurements:**")
                    for _, custom in custom_measurements.iterrows():
                        name = custom['measurement_name'].replace('_', ' ').title()
                        value = custom['measurement_value']
                        unit = custom['unit']
                        st.write(f"• {name}: {value:.1f} {unit}")
                else:
                    st.write("*No custom measurements*")

else:
    st.info("No measurements recorded yet. Add your first measurement above!")

# --- Tips ---
with st.expander("💡 Measurement Tips"):
    st.markdown("""
    **For Consistent Results:**
    - Measure at the same time of day (preferably morning)
    - Use the same scale/measuring tape
    - Take measurements before eating or drinking
    - Be consistent with clothing (or lack thereof)

    **Custom Measurements:**
    - Chest: Around the fullest part
    - Waist: Around the narrowest part
    - Hips: Around the widest part
    - Bicep: Flexed, at the largest point
    - Thigh: At the largest point
    """)
