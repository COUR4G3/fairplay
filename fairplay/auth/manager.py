import uuid

from flask_login import LoginManager

from ..db import db
from .models import AnonymousUser, User


login_manager = LoginManager()

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def user_loader(user_id):
    try:
        user_id = uuid.UUID(user_id)
    except ValueError:
        return

    return db.session.get(User, user_id)
