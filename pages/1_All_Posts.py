import streamlit as st
from core.auth import require_auth
from core.api import get, post, patch, delete
from ui.sidebar import render_sidebar
from core.post_utils import time_ago
import datetime

# 1. -------------------- PAGE CONFIG & DYNAMIC THEME CSS --------------------
st.set_page_config(page_title="Modern Feed", layout="centered")

st.markdown(
    """
    <style>
    /* Card adapts to light/dark background */
    div[data-testid="stVBCard"] {
        border-radius: 16px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 24px;
        margin-bottom: 20px;
        background-color: rgba(128, 128, 128, 0.03);
        transition: transform 0.2s ease;
    }
    
    div[data-testid="stVBCard"]:hover {
        border-color: #ff4b4b;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Metadata - uses secondary text color */
    .post-meta {
        color: var(--text-color);
        opacity: 0.6;
        font-size: 0.85rem;
        margin-bottom: 8px;
    }

    /* Dynamic Title - Auto-adjusts for Dark/Light Mode */
    .post-title {
        font-size: 1.5rem;
        font-weight: 800;
        color: var(--text-color);
        margin-bottom: 12px;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }

    /* Sleek Draft Badge */
    .draft-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        background-color: rgba(255, 165, 0, 0.2);
        color: #ffa500;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 10px;
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
        c_title = st.text_input("Title", key="dialog_create_title").strip()
        c_content = st.text_area("Content", key="dialog_create_content").strip()
        c_published = st.checkbox("Publish now?", value=True, key="dialog_create_pub")
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
        u_t = st.text_input(
            "Title", post_data["title"], key=f"upd_t_{post_data['id']}"
        ).strip()
        u_c = st.text_area(
            "Content", post_data["content"], key=f"upd_c_{post_data['id']}"
        ).strip()
        u_p = st.checkbox(
            "Published", post_data["published"], key=f"upd_p_{post_data['id']}"
        )

        if st.form_submit_button("💾 Save", type="primary"):
            # --- Validation Check ---
            if not u_t or not u_c:
                st.error("Title and Content cannot be empty!")
            else:
                patch(
                    f"/posts/{post_data['id']}",
                    {"title": u_t, "content": u_c, "published": u_p},
                )
                st.toast("Post updated ✅")
                # If they published it via the edit dialog, reset toggle state
                if u_p:
                    st.session_state.draft_toggle_state = False
                reset_feed()
                st.rerun()


@st.dialog("🗑️ Confirm Delete")
def confirm_delete(post_id):
    st.warning("Delete this post permanently?")
    if st.button("Delete Forever", type="primary", use_container_width=True):
        delete(f"/posts/{post_id}")
        st.toast("Post deleted 🗑️")
        reset_feed()
        st.rerun()


# 5. -------------------- SIDEBAR --------------------
with st.sidebar:
    with st.expander("➕ Quick Post", expanded=False):
        with st.form("sidebar_create_form", clear_on_submit=True):
            s_title = st.text_input("Title", key="sidebar_title")
            s_content = st.text_area("Content", key="sidebar_content")
            s_published = st.checkbox(
                "Publish now?", value=True, key="sidebar_create_pub"
            )
            if st.form_submit_button("Post"):
                error = handle_create_post(s_title, s_content, s_published)
                if not error:
                    st.toast("Posted!")
                    reset_feed()
                    st.rerun()
                else:
                    st.error(error)

    st.divider()
    render_sidebar()

# 6. -------------------- HEADER & FILTERS --------------------
st.title("📰 Feed")

top_col1, top_col2, top_col3 = st.columns([1.5, 3, 1.5])
with top_col1:
    if st.button(
        "➕ Create", type="primary", use_container_width=True, key="main_create_btn"
    ):
        create_post_dialog()
with top_col2:
    search_q = st.text_input(
        "Search",
        placeholder="Search posts...",
        label_visibility="collapsed",
        key="feed_search",
    )
with top_col3:
    sort_c = st.selectbox(
        "Sort",
        ["Newest", "Oldest", "Popularity"],
        label_visibility="collapsed",
        key="feed_sort",
    )

# Draft Toggle
show_drafts_only = st.toggle("📝 Show drafts", value=False, key="draft_toggle")

if search_q != st.session_state.get("search_query") or sort_c != st.session_state.get(
    "sort_option"
):
    st.session_state.search_query = search_q
    st.session_state.sort_option = sort_c
    reset_feed()
    st.rerun()


# 7. -------------------- API FETCH --------------------
def fetch_posts_batch():
    skip = st.session_state.post_skip
    search = st.session_state.get("search_query", "")
    sort_opt = st.session_state.get("sort_option", "Newest")
    sort_map = {"Newest": "newest", "Oldest": "oldest", "Popularity": "popularity"}

    query_params = f"limit=20&skip={skip}&sort={sort_map[sort_opt]}"
    if search:
        query_params += f"&search={search}"

    new_posts = get(f"/posts?{query_params}")
    st.session_state.posts_loaded.extend(new_posts)
    st.session_state.post_skip += len(new_posts)


if not st.session_state.posts_loaded:
    fetch_posts_batch()

# 8. -------------------- FEED DISPLAY LOOP --------------------
display_posts = st.session_state.posts_loaded
if show_drafts_only:
    display_posts = [
        i
        for i in display_posts
        if not i["Post"]["published"] and i["Post"]["owner_id"] == current_user_id
    ]
    if not display_posts:
        st.info("No drafts found.")

for idx, item in enumerate(display_posts):
    p_data, p_id = item["Post"], item["Post"]["id"]
    is_owner = p_data["owner_id"] == current_user_id

    expand_key = f"exp_{p_id}_{idx}"
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

        if is_owner and not p_data["published"]:
            st.markdown(
                "<span class='draft-badge'>📝 Draft</span>", unsafe_allow_html=True
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
            v_lab = "👍 Vote" if not v_act else "👎 Unvote"
            if b1.button(
                v_lab,
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

if len(st.session_state.posts_loaded) >= 20:
    if st.button("Load More", use_container_width=True, key="load_more_footer"):
        fetch_posts_batch()
        st.rerun()
