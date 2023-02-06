import sqlalchemy as sa
from flask_login import AnonymousUserMixin
from flask_login import login_user
from flask_login import UserMixin

from ..db import BaseModel
from ..utils.datetime import aware_datetime
from ..utils.security import get_password_crypt_context


class AnonymousUser(AnonymousUserMixin):
    id = None
    name = "anonymous"
    email = None
    mobile = None


class User(BaseModel, UserMixin):
    __tablename__ = "users"

    active = sa.Column(sa.Boolean, server_default=sa.text("false"))

    name = sa.Column(sa.String, index=True, nullable=False)

    email = sa.Column(sa.String, unique=True, nullable=False)

    _password = sa.Column("password", sa.String)

    last_login = sa.Column(sa.DateTime(True))
    created_at = sa.Column(
        sa.DateTime(True), server_default=sa.func.now(), nullable=False
    )
    updated_at = sa.Column(
        sa.DateTime(True),
        server_default=sa.func.now(),
        server_onupdate=sa.func.now(),
        nullable=False,
    )

    def check_password(self, password, noupdate=False):
        ctx = get_password_crypt_context()

        verified, update_hash = ctx.verify_and_update(password, self._password)
        if verified and update_hash:
            self._password = update_hash
        return verified

    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return bool(self.active)

    @classmethod
    def login(cls, login, password, remember=False):
        user = cls.filter(User.email == login)

        if user and user.check_password(password):
            if login_user(user, remember):
                user.last_login = aware_datetime()
                return user
        elif not user:
            ctx = get_password_crypt_context()
            ctx.dummy_verify()

        return False

    @property
    def password(self):
        return None

    @password.setter
    def password(self, value):
        ctx = get_password_crypt_context()
        self._password = ctx.hash(value, category="user-password")
