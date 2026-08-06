from functools import wraps
from flask import abort
from flask_login import current_user

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if current_user.role not in allowed_roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator
