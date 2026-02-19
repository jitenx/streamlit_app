import streamlit as st
from core.auth import logout


# Helper function for modern sidebar cards
def sidebar_card(label, icon="", page=None, key=None):
    full_label = f"{icon}  {label}" if icon else label
    key = key or full_label

    # Render a Streamlit button
    clicked = st.sidebar.button(full_label, key=key)

    # CSS styling for a card-like button
    st.markdown(
        f"""
    <style>
    div.stButton > button[title="{full_label}"] {{
        display: flex;
        align-items: center;
        gap: 10px;
        justify-content: flex-start;
        width: 100%;
        padding: 14px 18px;
        margin: 8px 0;
        font-size: 16px;
        font-weight: 500;
        color: white;
        background: linear-gradient(90deg, #6a11cb, #2575fc);
        border: none;
        border-radius: 12px;
        cursor: pointer;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transition: all 0.3s ease;
        text-align: left;
    }}
    div.stButton > button[title="{full_label}"]:hover {{
        background: linear-gradient(90deg, #2575fc, #6a11cb);
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(0,0,0,0.25);
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Handle click
    if clicked:
        if page == "logout":
            logout()
        elif page:
            st.switch_page(page)


# Sidebar rendering function
def render_sidebar():
    sidebar_card("Feed", "📜", page="pages/1_All_Posts.py", key="feed")
    sidebar_card(
        "Update Profile", "👤", page="pages/4_User_Profile.py", key="update_profile"
    )
    sidebar_card("🚪 Sign out", "🔓", page="logout", key="sign_out")
