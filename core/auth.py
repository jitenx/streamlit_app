import streamlit as st


def init_auth():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False


def is_authenticated():
    return st.session_state.get("authenticated", False)


def require_auth():
    if not is_authenticated():
        st.switch_page("app.py")


def login_success(token):
    st.session_state["access_token"] = token
    st.session_state["authenticated"] = True


def logout():
    st.session_state.clear()
    st.switch_page("app.py")


def auth_header():
    token = st.session_state.get("access_token")
    if not token:
        st.error("Please login again.")
        st.stop()
    return {"Authorization": f"Bearer {token}"}
