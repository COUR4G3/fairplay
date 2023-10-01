import sqlalchemy as sa
import sqlalchemy.orm as orm
import sqlalchemy_utils

from flask import current_app
from flask_login import AnonymousUserMixin, UserMixin
from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemySchema
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.ext.hybrid import hybrid_property

from ..audit import audit, audit_record_changes
from ..cache import cache
from ..db import BaseModel
from ..i18n import _, get_locale, get_timezone
from ..utils.passlib import get_passlib_context


class AnonymousUser(AnonymousUserMixin):
    active = True
    email = name = name_first = name_last = None
    role = "anonymous"
    id = None

    @property
    def lang(self):
        return get_locale()

    @property
    def tz(self):
        return get_timezone()

    default_tz = tz


class User(BaseModel, UserMixin):
    __tablename__ = "users"

    ROLE_CHOICES = [
        ("user", _("User")),
        ("admin", _("Administrator")),
    ]

    name = sa.Column(
        sa.String,
        sa.Computed("name_first || ' ' || name_last", persisted=True),
        nullable=False,
    )

    name_first = sa.Column(sa.String, nullable=False)
    name_last = sa.Column(sa.String, nullable=False)

    _email = sa.Column("email", sa.String, nullable=False)
    sanitized_email = sa.Column(sa.String)

    _password = sa.Column("password", sa.String)

    _active = sa.Column(
        "active",
        sa.Boolean,
        default=True,
        server_default=sa.text("true"),
        nullable=False,
    )

    default_tz = sa.Column(
        sqlalchemy_utils.TimezoneType(backend="pytz"),
        default=lambda _: get_timezone(),
        nullable=False,
    )

    lang = sa.Column(
        sqlalchemy_utils.LocaleType, default=lambda _: get_locale(), nullable=False
    )

    role = sa.Column(
        sqlalchemy_utils.ChoiceType(ROLE_CHOICES),
        default="user",
        server_default="user",
        nullable=False,
    )

    last_login_date = sa.Column(sa.DateTime(True))
    last_login_location = sa.Column(sa.String)
    last_login_remote_addr = sa.Column(
        sqlalchemy_utils.IPAddressType().with_variant(INET, "postgresql"),
    )

    __table_args__ = (
        sa.Index(
            "ix_users_email",
            _email,
            postgresql_using="gin",
            postgresql_ops={"email": "gin_trgm_ops"},
        ),
        sa.Index(
            "ix_users_name",
            name,
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
        sa.Index("ix_users_locale", lang, postgresql_using="brin"),
        sa.UniqueConstraint(sanitized_email, name="uq_users_sanitized_email"),
        sa.Index("ix_users_inactive", _active, postgresql_where="active IS false"),
    )

    @hybrid_property
    def active(self):
        return self._active

    @active.setter  # type: ignore[no-redef]
    def active(self, value):
        if self._active and not value:
            audit("security", "disabled_user", "User account was disabled", record=self)
        elif not self._active and value:
            audit("security", "enabled_user", "User account was enabled", record=self)

        self._active = value

    @active.update_expression  # type: ignore[no-redef]
    def active(cls, value):
        return [(cls._active, value)]

    def check_password(self, password):
        ctx = get_passlib_context()
        verified, update = ctx.verify_and_update(
            password, self._password, category="user"
        )

        if update:
            audit(
                "security",
                "updated_password",
                "Password hash for user was updated",
                context={
                    "from": ctx.identify(self._password),
                    "to": ctx.default_scheme(category="user"),
                },
                record=self,
            )

            self._password = update

        return verified

    @classmethod
    def dummy_verify(cls):
        ctx = get_passlib_context()
        ctx.dummy_verify()

    @hybrid_property
    def email(self):
        return self._email

    @email.setter  # type: ignore[no-redef]
    def email(self, value):
        if self._email and self._email != value:
            audit(
                "security",
                "changed_email",
                "Email address for user was changed to '%s'",
                value,
                context={
                    "from": self._email,
                    "to": value,
                },
                record=self,
            )

        self._email = value
        self.sanitized_email = self.sanitize_email(value)

    @email.update_expression  # type: ignore[no-redef]
    def email(cls, value):
        sanitized_email = cls.sanitize_email(value)
        return [(cls._email, value), (cls.sanitized_email, sanitized_email)]

    def get_cache_key(self):
        return get_cache_key_for_user(self)

    def get_tz_cache_key(self):
        return f"i18n.user-timezone:{self.id}"

    @property
    def is_active(self):
        return self.active

    @hybrid_property
    def password(self):
        return

    @password.expression  # type: ignore[no-redef]
    def password(cls):
        return cls._password

    @password.setter  # type: ignore[no-redef]
    def password(self, value):
        if self._password:
            audit(
                "security",
                "changed_password",
                "Password for user was changed",
                record=self,
            )

        self.set_password(value)

    @password.update_expression  # type: ignore[no-redef]
    def password(cls, value):
        ctx = get_passlib_context()
        hash = ctx.hash(value, category="user")
        return [(cls._password, hash)]

    @property
    def photo_url(self):
        from flask import url_for

        anchor = self.name.lstrip()[0].lower()
        return url_for("static", filename="img/profile.svg", _anchor=anchor)

    @staticmethod
    def sanitize_email(value):
        mailbox, domain = value.split("@", 1)
        base_mailbox = mailbox.split("+", 1)[0]
        return f"{base_mailbox}@{domain}".lower()

    def set_password(self, password):
        ctx = get_passlib_context()
        self._password = ctx.hash(password, category="user")

    @hybrid_property
    def tz(self):
        cache_key = self.get_tz_cache_key()
        value = cache.get(cache_key)

        if not value:
            value = self.default_tz

        return value

    @tz.expression  # type: ignore[no-redef]
    def tz(cls):
        return cls.default_tz

    @tz.setter  # type: ignore[no-redef]
    def tz(self, value):
        cache_key = self.get_tz_cache_key()
        cache.set(cache_key, value, 86400 * 3)

    @tz.update_expression  # type: ignore[no-redef]
    def tz(cls, value):
        return [(cls.default_tz, value)]


# class UserNotification(NotificationMixin, BaseModel):
#     __tablename__ = "users_notification"

#     user_id = sa.Column(
#         sqlalchemy_utils.UUIDType, sa.ForeignKey("users.id", ondelete="cascade")
#     )

#     user = orm.relationship("User", lazy="joined", back_populates="notifications")


def get_cache_key_for_user(user):
    return get_cache_key_for_user_id(user.get_id())


def get_cache_key_for_user_id(user_id):
    return f"auth.models.user:{user_id}"


def invalidate_user_cache(mapper, connection, target):
    current_app.logger.info(
        "Invalidate cache for user %s",
        target.id,
        extra={"category": "cache"},
    )
    cache_key = get_cache_key_for_user(target)
    cache.delete(cache_key)


event.listen(User, "after_update", invalidate_user_cache)


class UserAuditSchema(SQLAlchemySchema):
    class Meta:
        model = User

    name = fields.String()
    name_first = fields.String()
    name_last = fields.String()
    email = fields.String()
    role = fields.String()
    active = fields.Boolean()


audit_record_changes(User, schema=UserAuditSchema)
