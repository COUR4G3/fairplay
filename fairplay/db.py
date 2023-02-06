import uuid

import sqlalchemy as sa
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import BaseQuery
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_searchable import make_searchable
from sqlalchemy_utils import force_auto_coercion
from sqlalchemy_utils import force_instant_defaults
from sqlalchemy_utils import generic_repr
from sqlalchemy_utils import UUIDType

from .utils.db import ServerUUID


__all__ = [
    "BaseModel",
    "BaseQuery",
    "db",
]


db = SQLAlchemy()

migrate = Migrate()


def init_db(app: Flask):
    db.init_app(app)
    migrate.init_app(app, db, "fairplay/migrations")

    force_auto_coercion(db.Model)
    force_instant_defaults(db.Model)

    make_searchable(db.metadata)


@generic_repr
class BaseModel(db.Model):
    __abstract__ = True

    id = sa.Column(
        UUIDType,
        default=lambda ctx: uuid.uuid4(),
        primary_key=True,
        server_default=ServerUUID(),
    )
