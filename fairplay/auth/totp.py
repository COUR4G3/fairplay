import sqlalchemy as sa
import sqlalchemy.orm as orm
import sqlalchemy_utils

from flask import Blueprint

from ..db import BaseModel


class TotpAuthenticator:
    __tablename__ = "users_totp_authenticator"

    name = sa.Column(sa.String)

    info = sa.Column(sqlalchemy_utils.JSONType, nullable=False)

    last_used_date = sa.Column(sa.DateTime(True))

    user_id = sa.Column(
        sqlalchemy_utils.UUIDType,
        sa.ForeignKey("users.id", ondelete="cascade"),
        nullable=False,
    )

    user = orm.relationship("User", lazy="joined")

    __table_args__ = (
        sa.UniqueConstraint(user_id, name, name="uq_users_totp_authenticator_name"),
    )
