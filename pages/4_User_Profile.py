import streamlit as st
import time
from core.auth import require_auth, logout
from core.api import get, patch, delete
from ui.sidebar import render_sidebar
from core.validators import valid_email, check_password_strength


require_auth()
render_sidebar()

st.title("👤 User Profile")

# -------------------- TAB STATE --------------------
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Profile"

# Fetch user data
user = get("/users/profile/me")

# -------------------- TABS --------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Profile", "Edit Profile", "Update Email", "Update Password", "Delete Account"]
)

# -------------------- PROFILE --------------------
with tab1:
    st.info(f"""
**Name:** {user["first_name"]} {user["last_name"]}  
**Email:** {user["email"]}
""")

# -------------------- EDIT PROFILE --------------------
with tab2:
    st.subheader("✏️ Edit Profile")
    with st.form("update_user"):
        first_name = st.text_input("First Name", user["first_name"])
        last_name = st.text_input("Last Name", user["last_name"])

        col1, col2 = st.columns(2)
        save = col1.form_submit_button("💾 Save")
        # cancel = col2.form_submit_button("❌ Cancel")

    # if cancel:
    #     st.session_state.active_tab = "Profile"
    #     st.rerun()

    if save:
        if not all([first_name, last_name]):
            st.error("All fields are required")
        else:
            patch(
                f"/users/{user['id']}",
                {
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
            st.success("✅ Profile updated")


with tab3:
    st.subheader("📧 Update Email")
    with st.form("update_email"):
        email = st.text_input("Email", user["email"])

        col1, col2 = st.columns(2)
        save = col1.form_submit_button("💾 Save")

    if save:
        if not email:
            st.error("Email is required")
        elif not valid_email(email):
            st.error("Invalid email")
        else:
            result = patch(
                f"/users/{user['id']}",
                {"email": email},
            )
            if result:  # Only if patch succeeded
                st.success("✅ Email updated — please login again")
                time.sleep(2)
                logout()


with tab4:
    st.subheader("🔐 Change Password")

    with st.form("change_password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")

        col1, col2 = st.columns(2)
        save = col1.form_submit_button("💾 Save")

    if save:
        # 1️⃣ Check all fields filled
        if not all([current_password, new_password, confirm_password]):
            st.error("All fields are required")
        # 2️⃣ Confirm new passwords match
        elif new_password != confirm_password:
            st.error("New passwords do not match")
        else:
            # 3️⃣ Validate password strength
            strength_errors = check_password_strength(new_password)
            if strength_errors:
                st.error("Password must contain:\n- " + "\n- ".join(strength_errors))
            else:
                # 4️⃣ Attempt to update password via API
                try:
                    response = patch(
                        f"/users/{user['id']}",
                        {
                            "password": new_password,
                            "current_password": current_password,
                        },
                    )
                    # Only show success if patch returned successfully
                    if (
                        response
                    ):  # or response status check if your patch returns more info
                        st.success(
                            "✅ Password updated successfully — please login again"
                        )
                        time.sleep(2)
                        logout()
                    else:
                        st.error("❌ Password update failed")

                except Exception as e:
                    # Handle specific backend errors
                    err_msg = str(e)
                    if "Current password is incorrect" in err_msg:
                        st.error("❌ Current password is incorrect")
                    else:
                        st.error(f"❌ Failed to update password: {err_msg}")


# -------------------- DELETE ACCOUNT --------------------
with tab5:
    st.error("🛑 This will permanently delete your account!")
    # st.warning("This action cannot be undone")

    password = st.text_input("Confirm your password", type="password")
    confirm = st.checkbox("I understand this action is irreversible")

    col1, col2 = st.columns(2)
    # if col2.button("❌ Cancel"):
    #     st.session_state.active_tab = "Profile"
    #     st.rerun()

    if col1.button("🗑️ Yes, delete my account", disabled=not (confirm and password)):
        response = delete(f"/users/{user['id']}", {"password": password})
        if response.status_code == 204:
            st.success("✅ Account deleted")
            time.sleep(2)
            logout()
        else:
            st.error("❌ Incorrect password")
