from functools import wraps

from flask import Blueprint
from flask_login import current_user

from .manager import login_manager


def auth_required(f=None, scopes=None):
    def decorator(f):
        if isinstance(f, Blueprint):

            @f.before_request
            def auth_required():
                if not current_user.is_authenticated:
                    return login_manager.unauthorized()

            return f
        else:

            @wraps(f)
            def wrapper(*args, **kwargs):
                if not current_user.is_authenticated:
                    return login_manager.unauthorized()

                return f(*args, **kwargs)

            return wrapper

    if f:
        return decorator(f)
    return decorator
