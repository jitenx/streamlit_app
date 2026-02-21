import streamlit as st
from core.auth import require_auth
from core.api import get, post, patch, delete
from ui.sidebar import render_sidebar
from core.post_utils import time_ago

# 1. -------------------- PAGE CONFIG & DYNAMIC THEME CSS --------------------
st.set_page_config(page_title="My Posts", layout="centered")

st.markdown(
    """
    <style>
    div[data-testid="stVBCard"] {
        border-radius: 16px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 24px;
        margin-bottom: 20px;
        background-color: rgba(128, 128, 128, 0.03);
    }
    .post-meta { color: var(--text-color); opacity: 0.6; font-size: 0.85rem; margin-bottom: 8px; }
    .post-title { font-size: 1.5rem; font-weight: 800; color: var(--text-color); margin-bottom: 12px; }
    .draft-badge {
        display: inline-block; padding: 2px 10px; border-radius: 20px;
        background-color: rgba(255, 165, 0, 0.2); color: #ffa500;
        font-size: 0.75rem; font-weight: 700; text-transform: uppercase; margin-bottom: 10px;
    }
    .stats-badge {
        background: rgba(128, 128, 128, 0.1);
        padding: 5px 12px;
        border-radius: 10px;
        font-size: 0.9rem;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# 2. -------------------- AUTH & STATE --------------------
require_auth()
current_user = get("/users/profile/me")

if "my_posts_loaded" not in st.session_state:
    st.session_state.my_posts_loaded = []
if "my_post_skip" not in st.session_state:
    st.session_state.my_post_skip = 0


def reset_my_feed():
    st.session_state.my_posts_loaded = []
    st.session_state.my_post_skip = 0


# 3. -------------------- DIALOGS (REUSED) --------------------
@st.dialog("✏️ Update Post")
def update_post_dialog(post_data):
    with st.form("upd_form"):
        u_t = st.text_input("Title", post_data["title"]).strip()
        u_c = st.text_area("Content", post_data["content"]).strip()
        u_p = st.checkbox("Published", post_data["published"])
        if st.form_submit_button("Save Changes", type="primary"):
            if u_t and u_c:
                patch(
                    f"/posts/{post_data['id']}",
                    {"title": u_t, "content": u_c, "published": u_p},
                )
                st.toast("Updated! ✅")
                reset_my_feed()
                st.rerun()
            else:
                st.error("Fields cannot be empty")


@st.dialog("🗑️ Confirm Delete")
def confirm_delete(post_id):
    st.warning("Delete this post permanently?")
    if st.button("Delete Forever", type="primary", use_container_width=True):
        delete(f"/posts/{post_id}")
        st.toast("Deleted 🗑️")
        reset_my_feed()
        st.rerun()


# 4. -------------------- SIDEBAR --------------------
with st.sidebar:
    render_sidebar()


# ... (Previous code remains the same) ...


# 6. -------------------- API FETCH --------------------
def fetch_my_posts():
    # Only fetch if we haven't loaded anything yet or need more
    skip = st.session_state.my_post_skip
    new_posts = get(f"/posts/me?limit=1000&skip={skip}&sort=newest")
    st.session_state.my_posts_loaded.extend(new_posts)
    st.session_state.my_post_skip += len(new_posts)


# TRIGGER FETCH FIRST
if not st.session_state.my_posts_loaded:
    fetch_my_posts()

# 5. -------------------- HEADER (CALCULATE STATS AFTER FETCH) --------------------
st.title("📂 My Creations")

# Now that fetch_my_posts() has run, these lists won't be empty
my_posts = st.session_state.my_posts_loaded
draft_count = len([i for i in my_posts if not i["Post"]["published"]])
pub_count = len(my_posts) - draft_count

c1, c2, c3 = st.columns(3)
c1.markdown(
    f"<div class='stats-badge'>📝 <b>{draft_count}</b> Drafts</div>",
    unsafe_allow_html=True,
)
c2.markdown(
    f"<div class='stats-badge'>🚀 <b>{pub_count}</b> Published</div>",
    unsafe_allow_html=True,
)

st.divider()

# ... (Rest of the display loop) ...

# 7. -------------------- DISPLAY LOOP --------------------
if not st.session_state.my_posts_loaded:
    st.info(
        "You haven't created any posts yet. Start by clicking 'Create' in the sidebar!"
    )
else:
    for idx, item in enumerate(st.session_state.my_posts_loaded):
        p = item["Post"]

        with st.container(border=True):
            col_t, col_v = st.columns([4, 1])
            col_t.markdown(
                f"<div class='post-meta'>Created {time_ago(p['created_at'])}</div>",
                unsafe_allow_html=True,
            )
            col_v.markdown(
                f"<div style='text-align:right;'>{item['votes']} 👍</div>",
                unsafe_allow_html=True,
            )

            if not p["published"]:
                st.markdown(
                    "<span class='draft-badge'>📝 Draft</span>", unsafe_allow_html=True
                )

            st.markdown(
                f"<div class='post-title'>{p['title']}</div>", unsafe_allow_html=True
            )
            st.write(p["content"][:200] + ("..." if len(p["content"]) > 200 else ""))

            # Action Buttons
            b1, b2, b3 = st.columns([1, 1, 1])

            if not p["published"]:
                if b1.button(
                    "🚀 Publish",
                    key=f"pub_{p['id']}",
                    use_container_width=True,
                    type="primary",
                ):
                    patch(f"/posts/{p['id']}", {"published": True})
                    st.toast("Post is now live! 🚀")
                    reset_my_feed()
                    st.rerun()
            else:
                b1.button(
                    "✅ Published",
                    key=f"is_pub_{p['id']}",
                    use_container_width=True,
                    disabled=True,
                )

            if b2.button("✏️ Edit", key=f"ed_{p['id']}", use_container_width=True):
                update_post_dialog(p)

            if b3.button("🗑️", key=f"del_{p['id']}", use_container_width=True):
                confirm_delete(p["id"])

    if len(st.session_state.my_posts_loaded) >= 15:
        if st.button("Load More", use_container_width=True):
            fetch_my_posts()
            st.rerun()
