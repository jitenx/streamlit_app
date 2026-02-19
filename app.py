import streamlit as st
import requests
from core.auth import init_auth, login_success, is_authenticated
from core.config import API_BASE_URL, LOGIN_ENDPOINT
from core.validators import valid_email

if is_authenticated():
    st.switch_page("pages/1_All_Posts.py")
else:
    init_auth()
    st.title("Login")

    def login(email, password):
        payload = {"grant_type": "password", "username": email, "password": password}

        try:
            response = requests.post(
                f"{API_BASE_URL}{LOGIN_ENDPOINT}",
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 201:
                token = response.json()["access_token"]
                login_success(token)
                st.success("Login successful")
                st.switch_page("pages/1_All_Posts.py")
            else:
                st.error(response.json().get("detail", "Login failed"))
        except requests.RequestException:
            st.error("Unable to connect to server")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        if not email or not password:
            st.error("Email and password required")
        elif not valid_email(email):
            st.error("Invalid email format")
        else:
            login(email, password)
    st.write("Don't have an account?")
    if st.button("Create account"):
        st.switch_page("pages/5_Signup.py")
