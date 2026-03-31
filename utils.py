from functools import wraps
from flask import session, flash, redirect, url_for


def login_required(role):
    """Protects a route to a specific role only."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if session.get("role") != role:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("auth.login"))
            return f(*args, **kwargs)
        return wrapper
    return decorator