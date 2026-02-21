import streamlit as st
from core.auth import require_auth
from core.api import get, post, patch, delete
from ui.sidebar import render_sidebar
from core.post_utils import time_ago
import datetime

# 1. -------------------- PAGE CONFIG & STYLES --------------------
st.set_page_config(page_title="Modern Feed", layout="centered")

st.markdown(
    """
    <style>
    /* Card adapts to light/dark background */
    div[data-testid="stVBCard"] {
        border-radius: 16px;
        border: 1px solid rgba(128, 128, 128, 0.2); /* Dynamic subtle border */
        padding: 24px;
        margin-bottom: 20px;
        background-color: rgba(128, 128, 128, 0.05); /* Very slight tint */
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    div[data-testid="stVBCard"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        border-color: #ff4b4b;
    }
    
    /* Metadata - uses secondary text color */
    .post-meta {
        color: var(--text-color);
        opacity: 0.6;
        font-size: 0.85rem;
        font-weight: 500;
        margin-bottom: 8px;
    }

    /* Dynamic Title - High contrast in both modes */
    .post-title {
        font-size: 1.5rem;
        font-weight: 800;
        color: var(--text-color); /* Automatically switches white/black */
        margin-bottom: 12px;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }

    /* Post Content Text */
    .stMarkdown p {
        color: var(--text-color);
        opacity: 0.9;
        line-height: 1.6;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# 2. -------------------- AUTH & STATE --------------------
require_auth()
current_user = get("/users/profile/me")
current_user_id = current_user["id"]

if "posts_loaded" not in st.session_state:
    st.session_state.posts_loaded = []
if "post_skip" not in st.session_state:
    st.session_state.post_skip = 0


def reset_feed():
    st.session_state.posts_loaded = []
    st.session_state.post_skip = 0


# 3. -------------------- LOGIC HELPERS --------------------
def handle_create_post(title, content, published):
    if not title or not content:
        return "Title and content are required"
    try:
        post("/posts", {"title": title, "content": content, "published": published})
        return None
    except Exception as e:
        return f"Error: {str(e)}"


# 4. -------------------- DIALOGS --------------------
@st.dialog("➕ Create Post")
def create_post_dialog():
    with st.form("create_main_form", clear_on_submit=True):
        c_title = st.text_input("Title").strip()
        c_content = st.text_area("Content").strip()
        c_published = st.checkbox("Publish now?", value=True)
        col1, col2 = st.columns(2)
        if col1.form_submit_button("Create", type="primary"):
            error = handle_create_post(c_title, c_content, c_published)
            if error:
                st.error(error)
            else:
                st.toast("Post created! 🎉", icon="✅")
                reset_feed()
                st.rerun()
        if col2.form_submit_button("Cancel"):
            st.rerun()


@st.dialog("✏️ Update Post")
def update_post_dialog(post_data):
    with st.form("update_post_form"):
        title = st.text_input("Title", post_data["title"]).strip()
        content = st.text_area("Content", post_data["content"]).strip()
        published = st.checkbox("Published", post_data["published"])
        if st.form_submit_button("💾 Save", type="primary"):
            patch(
                f"/posts/{post_data['id']}",
                {"title": title, "content": content, "published": published},
            )
            st.toast("Post updated ✅")
            reset_feed()
            st.rerun()


@st.dialog("🗑️ Confirm Delete")
def confirm_delete(post_id):
    st.warning("Delete this post?")
    if st.button("Delete Forever", type="primary", use_container_width=True):
        delete(f"/posts/{post_id}")
        st.toast("Post deleted 🗑️")
        reset_feed()
        st.rerun()


# 5. -------------------- SIDEBAR --------------------
with st.sidebar:
    with st.expander("➕ Quick Post", expanded=False):
        with st.form("sidebar_create_form", clear_on_submit=True):
            s_title = st.text_input("Title")
            s_content = st.text_area("Content")
            s_published = st.checkbox("Publish now?", value=True)
            if st.form_submit_button("Post"):
                error = handle_create_post(s_title, s_content, s_published)
                if not error:
                    st.toast("Posted!")
                    reset_feed()
                    st.rerun()
    st.divider()
    render_sidebar()

# 6. -------------------- HEADER & FILTERS --------------------
st.title("📰 Feed")

top_col1, top_col2, top_col3 = st.columns([1.5, 3, 1.5])
with top_col1:
    if st.button("➕ Create Post", type="primary", use_container_width=True):
        create_post_dialog()
with top_col2:
    search_query = st.text_input(
        "🔎 Search", placeholder="Search posts...", label_visibility="collapsed"
    )
with top_col3:
    sort_choice = st.selectbox(
        "Sort", ["Newest", "Oldest", "Popularity"], label_visibility="collapsed"
    )

if search_query != st.session_state.get(
    "search_query"
) or sort_choice != st.session_state.get("sort_option"):
    st.session_state.search_query = search_query
    st.session_state.sort_option = sort_choice
    reset_feed()
    st.rerun()


# 7. -------------------- API FETCH --------------------
def fetch_posts_batch():
    skip = st.session_state.post_skip
    search = st.session_state.get("search_query", "")
    sort_option = st.session_state.get("sort_option", "Newest")
    sort_map = {"Newest": "newest", "Oldest": "oldest", "Popularity": "popularity"}

    query_params = f"limit=20&skip={skip}&sort={sort_map[sort_option]}"
    if search:
        query_params += f"&search={search}"

    new_posts = get(f"/posts?{query_params}")
    st.session_state.posts_loaded.extend(new_posts)
    st.session_state.post_skip += len(new_posts)


if not st.session_state.posts_loaded:
    fetch_posts_batch()

# 8. -------------------- FEED DISPLAY LOOP --------------------
for idx, item in enumerate(st.session_state.posts_loaded):
    p_data, p_id = item["Post"], item["Post"]["id"]
    is_owner = p_data["owner_id"] == current_user_id

    expand_key = f"expand_{p_id}_{idx}"
    if expand_key not in st.session_state:
        st.session_state[expand_key] = False

    with st.container(border=True):
        m1, m2 = st.columns([4, 1])
        m1.markdown(
            f"<div class='post-meta'>@{p_data['owner']['first_name']} • {time_ago(p_data['created_at'])}</div>",
            unsafe_allow_html=True,
        )
        if item["votes"] > 0:
            m2.markdown(
                f"<div style='text-align:right;'><b>{item['votes']}</b> 👍</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            f"<div class='post-title'>{p_data['title']}</div>", unsafe_allow_html=True
        )

        # Read More
        txt = p_data["content"]
        if len(txt) > 250 and not st.session_state[expand_key]:
            st.write(txt[:250] + "...")
            if st.button("Read more ↓", key=f"r_{p_id}_{idx}", type="secondary"):
                st.session_state[expand_key] = True
                st.rerun()
        else:
            st.write(txt)
            if len(txt) > 250:
                if st.button("Show less ↑", key=f"l_{p_id}_{idx}", type="secondary"):
                    st.session_state[expand_key] = False
                    st.rerun()

        if is_owner and not p_data["published"]:
            st.warning("Draft Mode", icon="📝")

        # Action Buttons
        b1, b2, b3 = st.columns([1.5, 1, 1])
        if is_owner and not p_data["published"]:
            if b1.button(
                "🚀 Publish", key=f"pb_{p_id}", use_container_width=True, type="primary"
            ):
                patch(f"/posts/{p_id}", {"published": True})
                st.toast("Post live! 🚀")
                reset_feed()
                st.rerun()
        else:
            v_act = item["user_voted"]
            if b1.button(
                "👍 Vote" if not v_act else "👎 Unvote",
                key=f"v_{p_id}_{idx}",
                use_container_width=True,
                type="primary" if v_act else "secondary",
            ):
                post("/vote", {"post_id": p_id, "dir": 0 if v_act else 1})
                st.toast("Vote updated ✅")
                reset_feed()
                st.rerun()

        if is_owner:
            if b2.button("✏️ Edit", key=f"ed_{p_id}", use_container_width=True):
                update_post_dialog(p_data)
            if b3.button("🗑️", key=f"dl_{p_id}", use_container_width=True):
                confirm_delete(p_id)

if len(st.session_state.posts_loaded) >= 10:
    if st.button("Load More", use_container_width=True):
        fetch_posts_batch()
        st.rerun()
