import streamlit as st
from supabase import create_client

# Always initialize the client here
url = st.secrets["supabase"]["SUPABASE_URL"]
key = st.secrets["supabase"]["SUPABASE_KEY"]
supabase = create_client(url, key)

def show_sidebar_user_info():
    with st.sidebar:
        if "user" in st.session_state and "session" in st.session_state:
            st.write(f"**Logged in as:** {st.session_state.user.email}")
            if st.button("Logout"):
                supabase.auth.sign_out()
                st.session_state.clear()
                st.rerun()
        else:
            st.markdown('<a href="/" target="_self">Back to Login</a>', unsafe_allow_html=True)

def user_has_profile(user_id):
    try:
        supabase.postgrest.auth(st.session_state.session.access_token)
        result = supabase.table('user_profiles').select('id').eq('user_id', user_id).execute()
        return bool(result.data)
    except Exception as e:
        st.error(f"Profile check failed: {str(e)}")
        return False

def check_auth_and_profile():
    if "user" not in st.session_state or "session" not in st.session_state:
        st.markdown(
    "<div style='background-color:#fff3cd;padding:10px;border-radius:5px;border:1px solid #ffeeba;'>"
    "⚠️ You must be <a href='/' target='_self'>logged in</a> to access this page."
    "</div>",
    unsafe_allow_html=True
)

        st.stop()
    supabase.postgrest.auth(st.session_state.session.access_token)
    if not user_has_profile(st.session_state.user.id):
        st.warning("You must complete your profile to access this page.")
        st.stop()
