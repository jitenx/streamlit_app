import streamlit as st
import time
from core.auth import require_auth, logout
from core.api import get, patch, delete
from ui.sidebar import render_sidebar
from core.validators import valid_email, check_password_strength
from core.post_utils import handle_create_post


require_auth()
# -------------------- SIDEBAR QUICK POST --------------------
with st.sidebar.expander("➕ Quick Post", expanded=False):
    with st.form("sidebar_create_form", clear_on_submit=True):
        sidebar_title = st.text_input("Title").strip()
        sidebar_content = st.text_area("Content").strip()
        sidebar_published = st.checkbox("Publish now?", value=True)
        submitted_sidebar = st.form_submit_button("Create")

    if submitted_sidebar:
        error = handle_create_post(sidebar_title, sidebar_content, sidebar_published)
        if error:
            st.error(error)
        else:
            st.toast("Post created 🎉")
            # reset feed for new post
            st.session_state.posts_loaded = []
            st.session_state.post_skip = 0
            st.rerun()
st.sidebar.divider()
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
        save = col1.form_submit_button(
            "💾 Save",
            disabled=not (current_password and new_password and confirm_password),
        )

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
    st.subheader("🗑️ Delete Account")

    st.error("Danger Zone")

    st.markdown(
        "Deleting your account will permanently remove all your data. "
        "This action cannot be undone."
    )

    # Initialize state
    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = False

    st.divider()

    # STEP 1: Initial Button
    if not st.session_state.confirm_delete:
        if st.button("🗑️ Delete My Account", type="primary"):
            st.session_state.confirm_delete = True
            st.rerun()

    # STEP 2: Confirmation Card
    if st.session_state.confirm_delete:
        # Wrap the card in a container with a unique key for CSS scoping
        with st.container():
            container_id = "delete-confirm-card"
            st.markdown(f'<div id="{container_id}">', unsafe_allow_html=True)

            st.warning("⚠️ Final Confirmation Required")

            st.markdown(
                "Please confirm your password and acknowledge that this "
                "action is irreversible."
            )

            with st.form("final_delete_form"):
                password = st.text_input(
                    "Enter your password to confirm",
                    type="password",
                )

                confirm = st.checkbox("Yes, I understand this action is irreversible")

                col1, col2 = st.columns(2)
                cancel_btn = col1.form_submit_button("Cancel")
                confirm_btn = col2.form_submit_button("Confirm Delete")

            st.markdown("</div>", unsafe_allow_html=True)

        # ---- Cancel Action ----
        if cancel_btn:
            st.session_state.confirm_delete = False
            st.rerun()

        # ---- Confirm Delete ----
        if confirm_btn:
            if not password:
                st.error("❌ Password is required")
            elif not confirm:
                st.error("❌ You must confirm the irreversible action")
            else:
                try:
                    response = delete(
                        f"/users/{user['id']}",
                        {"password": password},
                    )

                    if response.status_code == 204:
                        st.success("✅ Account deleted successfully")
                        time.sleep(2)
                        logout()
                    else:
                        st.error("❌ Incorrect password")

                except Exception as e:
                    st.error(f"❌ Failed to delete account: {str(e)}")


# # -------------------- DELETE ACCOUNT --------------------
# with tab5:
#     st.error("🛑 This will permanently delete your account!")
#     # st.warning("This action cannot be undone")

#     password = st.text_input("Confirm your password", type="password")
#     confirm = st.checkbox("I understand this action is irreversible")

#     col1, col2 = st.columns(2)
#     # if col2.button("❌ Cancel"):
#     #     st.session_state.active_tab = "Profile"
#     #     st.rerun()

#     if col1.button("🗑️ Yes, delete my account", disabled=not (confirm and password)):
#         response = delete(f"/users/{user['id']}", {"password": password})
#         if response.status_code == 204:
#             st.success("✅ Account deleted")
#             time.sleep(2)
#             logout()
#         else:
#             st.error("❌ Incorrect password")
