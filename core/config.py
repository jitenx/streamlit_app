import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


LOGIN_ENDPOINT = "/login"
USERS_ENDPOINT = "/users"
POSTS_ENDPOINT = "/posts"
