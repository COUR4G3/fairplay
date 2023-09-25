from flask_login import current_user, login_user, logout_user

from .decorators import auth_required
from .manager import login_manager
from .routes import auth


__all__ = [
    "auth_required",
    "current_user",
    "login_user",
    "logout_user",
]


def init_app(app):
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    login_manager.init_app(app)

    app.register_blueprint(auth)
