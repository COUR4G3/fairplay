from functools import wraps

from flask import Blueprint
from flask import current_app
from flask_login import current_user

from .manager import manager


def login_required(f):
    if isinstance(f, Blueprint):

        @f.before_request
        def login_required():
            if (
                not current_app.config["LOGIN_DISABLED"]
                and not current_user.is_authenticated
            ):
                manager.unauthorized()

        return f
    else:

        @wraps(f)
        def wrapper(*args, **kwargs):
            if (
                not current_app.config["LOGIN_DISABLED"]
                and not current_user.is_authenticated
            ):
                manager.unauthorized()

            return f(*args, **kwargs)

        return wrapper
