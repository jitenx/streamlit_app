import streamlit as st
import time
from core.auth import require_auth, logout
from core.api import get, patch, delete
from ui.sidebar import render_sidebar
from core.validators import valid_email, check_password_strength
from core.post_utils import handle_create_post

# 1. -------------------- AUTH & CONFIG --------------------
require_auth()
st.set_page_config(page_title="My Profile", layout="centered")

# 2. -------------------- DYNAMIC MODERN CSS --------------------
st.markdown(
    """
    <style>
    /* Card adapts to light/dark background */
    .profile-card {
        border-radius: 16px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 24px;
        margin-bottom: 20px;
        background-color: rgba(128, 128, 128, 0.03);
    }
    
    .profile-info {
        font-size: 1.1rem;
        color: var(--text-color);
        margin-bottom: 10px;
        display: flex;
        align-items: center;
    }

    .badge {
        background: rgba(255, 75, 75, 0.1);
        padding: 4px 10px;
        border-radius: 8px;
        margin-right: 12px;
    }

    /* Danger Zone Styling */
    .danger-box {
        border: 1px solid #ff4b4b;
        border-radius: 12px;
        padding: 20px;
        background-color: rgba(255, 75, 75, 0.05);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# 3. -------------------- SIDEBAR --------------------
with st.sidebar:
    with st.expander("➕ Quick Post", expanded=False):
        st.markdown("### Create a New Post 📝")
        with st.form("sidebar_create_form", clear_on_submit=True):
            sidebar_title = st.text_input("Title").strip()
            sidebar_content = st.text_area("Content").strip()
            sidebar_published = st.checkbox("Publish now?", value=True)
            submitted_sidebar = st.form_submit_button("Create", type="primary")

        if submitted_sidebar:
            error = handle_create_post(
                sidebar_title, sidebar_content, sidebar_published
            )
            if error:
                st.error(error)
            else:
                st.toast("✅ Post created successfully 🎉", icon="📝")
                st.session_state.posts_loaded = []
                st.session_state.post_skip = 0
                st.rerun()
    st.sidebar.divider()
    render_sidebar()

# 4. -------------------- PROFILE DATA --------------------
st.title("👤 My Profile")
user = get("/users/profile/me")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Profile", "Edit Profile", "Update Email", "Change Password", "Delete Account"]
)

# -------------------- TAB 1: PROFILE --------------------
with tab1:
    st.markdown(
        f"""
        <div class="profile-card">
            <div class="profile-info"><span class="badge">👤</span> <strong>Name:</strong> &nbsp; {user["first_name"]} {user["last_name"]}</div>
            <div class="profile-info"><span class="badge">📧</span> <strong>Email:</strong> &nbsp; {user["email"]}</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

# -------------------- TAB 2: EDIT PROFILE --------------------
with tab2:
    st.subheader("✏️ Edit Name")
    with st.form("update_user"):
        first_name = st.text_input("First Name", user["first_name"])
        last_name = st.text_input("Last Name", user["last_name"])
        col1, col2 = st.columns([1, 1])
        if col1.form_submit_button("💾 Save", type="primary"):
            if not all([first_name, last_name]):
                st.error("All fields are required")
            else:
                patch(
                    f"/users/{user['id']}",
                    {"first_name": first_name, "last_name": last_name},
                )
                st.toast("✅ Profile updated successfully 🎉")
                st.rerun()
        if col2.form_submit_button("❌ Cancel"):
            st.rerun()

# -------------------- TAB 3: UPDATE EMAIL --------------------
with tab3:
    st.subheader("📧 Update Email")
    with st.form("update_email"):
        email = st.text_input("Email", user["email"])
        col1, col2 = st.columns([1, 1])
        if col1.form_submit_button("💾 Save", type="primary"):
            if not email:
                st.error("Email is required")
            elif not valid_email(email):
                st.error("Invalid email")
            else:
                patch(f"/users/{user['id']}", {"email": email})
                st.toast("✅ Email updated — please login again", icon="📧")
                time.sleep(2)
                logout()
        if col2.form_submit_button("❌ Cancel"):
            st.rerun()

# -------------------- TAB 4: CHANGE PASSWORD --------------------
with tab4:
    st.subheader("🔐 Security")
    with st.form("change_password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        col1, col2 = st.columns([1, 1])
        if col1.form_submit_button("💾 Save", type="primary"):
            if new_password != confirm_password:
                st.error("New passwords do not match")
            else:
                errors = check_password_strength(new_password)
                if errors:
                    st.error("- " + "\n- ".join(errors))
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
                            st.toast("✅ Password updated — logging out", icon="🔐")
                            time.sleep(2)
                            logout()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        if col2.form_submit_button("❌ Cancel"):
            st.rerun()

# --- TAB 5: DELETE ACCOUNT (Corrected Logic) ---
with tab5:
    st.markdown('<div class="danger-container">', unsafe_allow_html=True)
    st.subheader("⚠️ Close Account")
    st.write("This action will delete all your posts and profile data forever.")

    # Use a specific key for the deletion state
    if "show_delete_confirm" not in st.session_state:
        st.session_state.show_delete_confirm = False

    if not st.session_state.show_delete_confirm:
        if st.button("Delete My Account", type="primary", use_container_width=True):
            st.session_state.show_delete_confirm = True
            st.rerun()
    else:
        st.error("Final Warning: This is irreversible.")
        with st.form("final_termination"):
            confirm_pw = st.text_input("Enter Password to Confirm", type="password")
            understand = st.checkbox("I understand my data will be lost.")

            c1, c2 = st.columns(2)
            if c1.form_submit_button("🔥 Confirm Deletion", type="primary"):
                if understand and confirm_pw:
                    # Corrected: Sending password in body for deletion verification
                    resp = delete(f"/users/{user['id']}", data={"password": confirm_pw})
                    if resp.status_code == 204:
                        st.success("Account deleted.")
                        time.sleep(1)
                        logout()
                    else:
                        st.error("Incorrect password.")
                else:
                    st.warning("Please check the box and enter your password.")

            if c2.form_submit_button("Cancel"):
                st.session_state.show_delete_confirm = False
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
