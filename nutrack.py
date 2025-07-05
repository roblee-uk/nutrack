import streamlit as st
from supabase import create_client, Client

# Initialize Supabase client
url: str = st.secrets["supabase"]["SUPABASE_URL"]
key: str = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# Function to check if user has a profile
def user_has_profile(user_id):
    try:
        supabase.postgrest.auth(st.session_state.session.access_token)
        result = supabase.table('user_profiles').select('id').eq('user_id', user_id).execute()
        return bool(result.data)
    except Exception as e:
        st.error(f"Profile check failed: {str(e)}")
        return False

# Function to insert user profile
def insert_user_profile():
    try:
        user = st.session_state.user
        supabase.postgrest.auth(st.session_state.session.access_token)
        response = supabase.table('user_profiles').insert({
            'user_id': user.id,
            'email': user.email
        }).execute()
        if hasattr(response, "error") and response.error:
            st.error(f"Profile creation failed: {response.error.message}")
        else:
            st.success("Profile created successfully!")
            st.rerun()
    except Exception as e:
        st.error(f"Profile creation error: {str(e)}")

# Main app logic
def main():
    st.write("# Welcome to Nutrack 🥗")

    with st.sidebar:
        if "user" in st.session_state:
            st.write(f"Logged in as: {st.session_state.user.email}")
            if st.button("Logout"):
                supabase.auth.sign_out()
                st.session_state.clear()
                st.rerun()
        else:
            st.write("Not logged in")

    if "user" not in st.session_state:
        with st.expander("Login/Sign Up", expanded=True):
            with st.form("auth_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                action = st.radio("Action", ["Login", "Sign Up"])

                if st.form_submit_button("Continue"):
                    try:
                        if action == "Sign Up":
                            response = supabase.auth.sign_up({"email": email, "password": password})
                        else:
                            response = supabase.auth.sign_in_with_password({"email": email, "password": password})

                        st.session_state.user = response.user
                        st.session_state.session = response.session
                        supabase.postgrest.auth(response.session.access_token)
                        st.rerun()

                    except Exception as e:
                        st.error(f"{action} failed: {str(e)}")

    else:
        if not user_has_profile(st.session_state.user.id):
            st.warning("Please complete your profile to access all features")
            with st.form("profile_form"):
                st.write("### Complete Your Profile")
                if st.form_submit_button("Create Profile"):
                    insert_user_profile()
        else:
            st.success("✅ Profile complete! Explore nutritional tracking and meal planning features using the sidebar.")

if __name__ == "__main__":
    main()
