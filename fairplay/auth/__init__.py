from flask import Flask
from flask_login import confirm_login
from flask_login import current_user
from flask_login import login_fresh
from flask_login import login_user
from flask_login import logout_user

from .manager import manager
from .models import User
from .utils import login_required


def init_auth(app: Flask):
    manager.init_app(app)


__all__ = [
    "confirm_login",
    "current_user",
    "login_fresh",
    "login_required",
    "login_user",
    "logout_user",
    "User",
]
