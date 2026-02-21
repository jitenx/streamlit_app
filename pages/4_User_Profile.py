import streamlit as st
import time
from core.auth import require_auth, logout
from core.api import get, patch, delete
from ui.sidebar import render_sidebar
from core.validators import valid_email, check_password_strength
from core.post_utils import handle_create_post

require_auth()

# =======================
# SIDEBAR QUICK POST
# =======================
with st.sidebar.expander("➕ Quick Post", expanded=False):
    st.markdown("### Create a New Post 📝")
    with st.form("sidebar_create_form", clear_on_submit=True):
        sidebar_title = st.text_input("Title").strip()
        sidebar_content = st.text_area("Content").strip()
        sidebar_published = st.checkbox("Publish now?", value=True)
        submitted_sidebar = st.form_submit_button("Create", type="primary")

    if submitted_sidebar:
        error = handle_create_post(sidebar_title, sidebar_content, sidebar_published)
        if error:
            st.error(error)
        else:
            st.toast("✅ Post created successfully 🎉", icon="📝")
            st.session_state.posts_loaded = []
            st.session_state.post_skip = 0
            st.rerun()
st.sidebar.divider()
render_sidebar()

# =======================
# USER PROFILE PAGE
# =======================
st.title("👤 User Profile")

# -------------------- TAB STATE --------------------
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Profile"

# Fetch user data
user = get("/users/profile/me")

# -------------------- TABS --------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Profile", "Edit Profile", "Update Email", "Change Password", "Delete Account"]
)

# -------------------- PROFILE TAB --------------------
with tab1:
    with st.container():
        st.markdown(
            f"""
            <div class="profile-card">
                <p><span class="badge">👤</span> <strong>Name:</strong> {user["first_name"]} {user["last_name"]}</p>
                <p><span class="badge">📧</span> <strong>Email:</strong> {user["email"]}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# -------------------- EDIT PROFILE TAB --------------------
with tab2:
    st.subheader("✏️ Edit Profile")
    with st.container():
        with st.form("update_user"):
            first_name = st.text_input("First Name", user["first_name"])
            last_name = st.text_input("Last Name", user["last_name"])

            col1, col2 = st.columns([1, 1])
            save = col1.form_submit_button("💾 Save", type="primary")
            cancel = col2.form_submit_button("❌ Cancel", type="secondary")

        if cancel:
            st.rerun()

        if save:
            if not all([first_name, last_name]):
                st.error("All fields are required")
            else:
                patch(
                    f"/users/{user['id']}",
                    {"first_name": first_name, "last_name": last_name},
                )
                st.toast("✅ Profile updated successfully 🎉", icon="✅")

# -------------------- UPDATE EMAIL TAB --------------------
with tab3:
    st.subheader("📧 Update Email")
    with st.container():
        with st.form("update_email"):
            email = st.text_input("Email", user["email"])
            col1, col2 = st.columns([1, 1])
            save = col1.form_submit_button("💾 Save", type="primary")
            cancel = col2.form_submit_button("❌ Cancel", type="secondary")

        if cancel:
            st.rerun()

        if save:
            if not email:
                st.error("Email is required")
            elif not valid_email(email):
                st.error("Invalid email")
            else:
                result = patch(f"/users/{user['id']}", {"email": email})
                if result:
                    st.toast(
                        "✅ Email updated successfully — please login again 📧",
                        icon="📧",
                    )
                    time.sleep(2)
                    logout()

# -------------------- CHANGE PASSWORD TAB --------------------
with tab4:
    st.subheader("🔐 Change Password")
    with st.container():
        with st.form("change_password_form"):
            current_password = st.text_input(
                "Current Password", type="password", key="current_pw"
            )
            new_password = st.text_input("New Password", type="password", key="new_pw")
            confirm_password = st.text_input(
                "Confirm New Password", type="password", key="confirm_pw"
            )

            col1, col2 = st.columns([1, 1])
            save = col1.form_submit_button(
                "💾 Save",
                type="primary",
            )
            cancel = col2.form_submit_button("❌ Cancel", type="secondary")

        if cancel:
            for key in ["current_pw", "new_pw", "confirm_pw"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

        if save:
            if new_password != confirm_password:
                st.error("New passwords do not match")
            else:
                errors = check_password_strength(new_password)
                if errors:
                    st.error("Password must contain:\n- " + "\n- ".join(errors))
                else:
                    try:
                        resp = patch(
                            f"/users/{user['id']}",
                            {
                                "password": new_password,
                                "current_password": current_password,
                            },
                        )
                        if resp:
                            st.toast(
                                "✅ Password updated successfully — please login again 🔐",
                                icon="🔐",
                            )
                            time.sleep(2)
                            logout()
                        else:
                            st.error("❌ Password update failed")
                    except Exception as e:
                        msg = str(e)
                        if "Current password is incorrect" in msg:
                            st.error("❌ Current password is incorrect")
                        else:
                            st.error(f"❌ Failed to update password: {msg}")

# -------------------- DELETE ACCOUNT TAB --------------------
with tab5:
    st.subheader("🗑️ Delete Account")
    st.error("Danger Zone")
    st.markdown(
        "Deleting your account will permanently remove all your data. "
        "This action cannot be undone."
    )

    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = False

    st.divider()

    if not st.session_state.confirm_delete:
        if st.button("🗑️ Delete My Account", type="primary"):
            st.session_state.confirm_delete = True
            st.rerun()

    if st.session_state.confirm_delete:
        with st.container():
            container_id = "delete-confirm-card"
            st.markdown(f'<div id="{container_id}">', unsafe_allow_html=True)
            st.warning("⚠️ Final Confirmation Required")
            st.markdown(
                "Confirm your password and check the box to delete your account permanently."
            )

            with st.form("final_delete_form"):
                password = st.text_input("Password", type="password", key="delete_pw")
                confirm = st.checkbox(
                    "I understand this action is irreversible", key="delete_checkbox"
                )

                col1, col2 = st.columns([1, 1])
                cancel_btn = col1.form_submit_button("❌ Cancel", type="secondary")
                confirm_btn = col2.form_submit_button(
                    "🗑️ Confirm Delete",
                    type="secondary",
                )

            st.markdown("</div>", unsafe_allow_html=True)

        if cancel_btn:
            for key in ["delete_pw", "delete_checkbox", "confirm_delete"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

        if confirm_btn:
            try:
                resp = delete(
                    f"/users/{user['id']}", {"password": st.session_state.delete_pw}
                )
                if resp.status_code == 204:
                    st.toast("✅ Account deleted successfully 🗑️", icon="🗑️")
                    time.sleep(2)
                    logout()
                else:
                    st.error("❌ Incorrect password")
            except Exception as e:
                st.error(f"❌ Failed to delete account: {str(e)}")

# =======================
# MODERN CSS
# =======================
st.markdown(
    """
    <style>
    /* Card-like containers */
    div.stContainer {
        padding: 1rem;
        border-radius: 12px;
        background-color: #fdfdfd;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    div.stContainer:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(0,0,0,0.12);
    }

    /* Profile badges */
    .badge {
        display: inline-block;
        background: #e0f3ff;
        padding: 0.15rem 0.5rem;
        border-radius: 6px;
        font-size: 0.9rem;
        margin-right: 0.5rem;
    }

    /* Buttons hover */
    div.stButton>button:hover:enabled {
        opacity: 0.9;
        transform: translateY(-1px);
    }

    /* Delete confirm button */
    #delete-confirm-card div.stButton > button:first-of-type + button {
        background-color: #d9534f;
        color: white;
        border: 1px solid #d43f3a;
        transition: all 0.2s;
    }
    #delete-confirm-card div.stButton > button:first-of-type + button:hover:enabled {
        background-color: #c9302c;
        box-shadow: 0 0 8px rgba(255,0,0,0.3);
    }
    #delete-confirm-card div.stButton > button:first-of-type + button:disabled {
        background-color: #f5c6cb;
        color: #a94442;
        border-color: #f5c6cb;
        cursor: not-allowed;
    }

    /* Subtle alerts */
    div.stAlert {
        border-radius: 10px;
        padding: 0.75rem;
    }

    /* Tabs spacing */
    div[data-testid="stTabs"] > div > div {
        padding-top: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
