import streamlit as st
from core.auth import require_auth
from core.api import get, post, patch, delete
from ui.sidebar import render_sidebar
from core.post_utils import time_ago


# -------------------- AUTH --------------------
require_auth()
current_user = get("/users/profile/me")
current_user_id = current_user["id"]


# -------------------- POST CREATION LOGIC --------------------
def handle_create_post(title, content, published):
    if not title or not content:
        return "Title and content are required"

    try:
        post("/posts", {"title": title, "content": content, "published": published})
    except Exception as e:
        return f"Failed to create post: {str(e)}"
    return None  # success


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
st.title("📰 Feed")
st.divider()


# -------------------- CREATE POST DIALOG --------------------
@st.dialog("➕ Create Post")
def create_post_dialog():
    with st.form("create_post_form", clear_on_submit=True):
        create_title = st.text_input("Title").strip()
        create_content = st.text_area("Content").strip()
        create_published = st.checkbox("Publish now?", value=True)
        col1, col2 = st.columns(2)
        cancel = col2.form_submit_button("Cancel")
        submitted = col1.form_submit_button("Create")

    if cancel:
        st.rerun()

    if submitted:
        error = handle_create_post(create_title, create_content, create_published)
        if error:
            st.error(error)
        else:
            st.toast("Post created 🎉")
            st.session_state.posts_loaded = []
            st.session_state.post_skip = 0
            st.rerun()


st.button("➕ Create Post", on_click=create_post_dialog)


# -------------------- UPDATE / DELETE DIALOGS --------------------
@st.dialog("✏️ Update Post")
def update_post_dialog(post_data):
    if post_data["owner_id"] != current_user_id:
        st.error("You are not allowed to edit this post.")
        return
    with st.form("update_post_form"):
        title = st.text_input("Title", post_data["title"]).strip()
        content = st.text_area("Content", post_data["content"]).strip()
        published = st.checkbox("Published", post_data["published"])
        col1, col2 = st.columns(2)
        save = col1.form_submit_button("💾 Save")
        cancel = col2.form_submit_button("Cancel")
        if cancel:
            st.rerun()
    if save:
        if not title or not content:
            st.error("Title and content are required")
        else:
            with st.spinner("Updating post..."):
                patch(
                    f"/posts/{post_data['id']}",
                    {"title": title, "content": content, "published": published},
                )
            st.toast("Post updated ✅")
            st.session_state.posts_loaded = []
            st.session_state.post_skip = 0
            st.rerun()


@st.dialog("🗑️ Confirm Delete")
def confirm_delete(post_id):
    st.warning("This action cannot be undone.")
    col1, col2 = st.columns(2)
    if col2.button("Cancel"):
        st.rerun()
    if col1.button("Delete", type="primary"):
        delete(f"/posts/{post_id}")
        st.toast("Post deleted 🗑️")
        st.session_state.posts_loaded = []
        st.session_state.post_skip = 0
        st.rerun()


# -------------------- INFINITE SCROLL STATE --------------------
if "post_skip" not in st.session_state:
    st.session_state.post_skip = 0
if "posts_loaded" not in st.session_state:
    st.session_state.posts_loaded = []

BATCH_SIZE = 50


def fetch_posts_batch():
    skip = st.session_state.post_skip
    new_posts = get(f"/posts?limit={BATCH_SIZE}&skip={skip}")
    st.session_state.posts_loaded.extend(new_posts)
    st.session_state.post_skip += len(new_posts)


# Initial load
if not st.session_state.posts_loaded:
    fetch_posts_batch()

# -------------------- DISPLAY POSTS --------------------
for idx, item in enumerate(st.session_state.posts_loaded):
    post_data = item["Post"]
    votes = item["votes"]
    user_voted = item["user_voted"]

    post_id = post_data.get("id")
    if post_id is None:
        continue

    is_owner = post_data["owner_id"] == current_user_id
    is_published = post_data["published"]

    vote_key = f"vote_{post_id}_{idx}"
    expand_key = f"expand_{post_id}"

    # Vote state
    direction = 0 if user_voted else 1
    vote_label = "Remove Vote" if user_voted else "Vote"

    # Expand preview
    if expand_key not in st.session_state:
        st.session_state[expand_key] = False
    show_full = st.session_state[expand_key]

    full_content = post_data["content"]
    preview_limit = 220
    display_content = (
        full_content
        if show_full or len(full_content) <= preview_limit
        else full_content[:preview_limit] + "..."
    )
    show_read_more = len(full_content) > preview_limit and not show_full

    with st.container(border=True):
        # Header: Title + Likes
        header_col1, header_col2 = st.columns([5, 1])
        with header_col1:
            st.subheader(post_data["title"])
        if votes > 0:
            with header_col2:
                st.markdown(
                    f"<div style='text-align:right;font-weight:bold;'>{votes} 👍</div>",
                    unsafe_allow_html=True,
                )

        # Content
        st.markdown(display_content)

        # Read more / show less
        if show_read_more:
            if st.button("Read more", key=f"read_{post_id}"):
                st.session_state[expand_key] = True
                st.rerun()
        elif show_full and len(full_content) > preview_limit:
            if st.button("Show less", key=f"less_{post_id}"):
                st.session_state[expand_key] = False
                st.rerun()
        st.caption(
            f"👤 {post_data['owner']['first_name']} {post_data['owner']['last_name']} • {time_ago(post_data['created_at'])}"
        )

        # Draft badge
        if is_owner and not is_published:
            st.warning("📝 Draft (Not Published)")

        # Vote / Action buttons
        # Action buttons row
        col1, col2, col3 = st.columns([1, 1, 1])

        # Column 1: Publish / Vote
        if is_owner:
            if not is_published:
                # Show Publish button for drafts
                if col1.button(
                    "🚀 Publish", key=f"pub_{post_id}", use_container_width=True
                ):
                    patch(
                        f"/posts/{post_id}",
                        {
                            "title": post_data["title"],
                            "content": post_data["content"],
                            "published": True,
                        },
                    )
                    st.toast("Post published successfully 🚀")
                    # refresh feed and update session_state
                    st.session_state.posts_loaded = []
                    st.session_state.post_skip = 0
                    st.rerun()
            else:
                # Already published → show vote button
                vote_color = "#ff4b4b" if user_voted else "#00c853"
                vote_button_text = (
                    f"👎🏻 {vote_label}" if user_voted else f"👍 {vote_label}"
                )
                st.markdown(
                    f"""
                    <style>
                    button[data-testid="stButton"][data-key="{vote_key}"] {{
                        background-color: {vote_color} !important;
                        color: white !important;
                        border: none !important;
                    }}
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                if col1.button(
                    vote_button_text, key=vote_key, use_container_width=True
                ):
                    post("/vote", {"post_id": post_id, "dir": direction})
                    st.session_state.posts_loaded = []
                    st.session_state.post_skip = 0
                    st.rerun()

            # Column 2: Update
            if col2.button("✏️ Update", key=f"upd_{post_id}", use_container_width=True):
                update_post_dialog(post_data)

            # Column 3: Delete
            if col3.button("🗑️ Delete", key=f"del_{post_id}", use_container_width=True):
                confirm_delete(post_id)
        else:
            vote_color = "#ff4b4b" if user_voted else "#00c853"
            vote_button_text = (
                f"👎🏻 {vote_label}" if user_voted else f"👍 {vote_label}"
            )
            st.markdown(
                f"""
                <style>
                button[data-testid="stButton"][data-key="{vote_key}"] {{
                    background-color: {vote_color} !important;
                    color: white !important;
                    border: none !important;
                }}
                </style>
                """,
                unsafe_allow_html=True,
            )
            if col1.button(vote_button_text, key=vote_key, use_container_width=True):
                post("/vote", {"post_id": post_id, "dir": direction})
                st.session_state.posts_loaded = []
                st.session_state.post_skip = 0
                st.rerun()

# -------------------- LOAD MORE BUTTON --------------------
if len(st.session_state.posts_loaded) >= BATCH_SIZE:
    if st.button("Load More Posts"):
        fetch_posts_batch()
        st.rerun()
