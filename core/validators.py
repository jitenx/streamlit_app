import re

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")


def valid_email(email):
    return bool(EMAIL_REGEX.match(email))


def check_password_strength(password: str):
    errors = []

    if len(password) < 8:
        errors.append("At least 8 characters")

    if not re.search(r"[A-Z]", password):
        errors.append("One uppercase letter")

    if not re.search(r"[a-z]", password):
        errors.append("One lowercase letter")

    if not re.search(r"\d", password):
        errors.append("One number")

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("One special character")

    return errors
