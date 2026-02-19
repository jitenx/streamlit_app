import streamlit as st
import requests
from core.config import API_BASE_URL, USERS_ENDPOINT
from core.validators import valid_email, check_password_strength
from core.auth import is_authenticated


if is_authenticated():
    st.switch_page("pages/1_All_Posts.py")
else:
    st.title("Sign Up")

    with st.form("signup"):
        first = st.text_input("First Name")
        last = st.text_input("Last Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Create Account")

    if submit:
        if not all([first, last, email, password, confirm_password]):
            st.error("All fields are required")

        elif not valid_email(email):
            st.error("Invalid email")

        elif password != confirm_password:
            st.error("Passwords do not match")

        else:
            strength_errors = check_password_strength(password)

            if strength_errors:
                st.error("Password must contain:\n- " + "\n- ".join(strength_errors))
            else:
                response = requests.post(
                    f"{API_BASE_URL}{USERS_ENDPOINT}",
                    json={
                        "first_name": first,
                        "last_name": last,
                        "email": email,
                        "password": password,
                    },
                )

                if response.status_code == 201:
                    st.success("Account created 🎉")
                    st.switch_page("app.py")
                else:
                    try:
                        data = response.json()
                        error_message = data.get("detail", "Signup failed")
                    except ValueError:
                        error_message = (
                            f"Signup failed. Server returned: {response.text}"
                        )

                    st.error(error_message)
    st.write("Existing User?")
    if st.button("Login"):
        st.switch_page("app.py")
