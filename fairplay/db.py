import uuid

import sqlalchemy as sa
import sqlalchemy_utils

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.query import Query as BaseQuery
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.functions import FunctionElement
from sqlalchemy_utils import force_instant_defaults

from .utils.datetime import aware_datetime


__all__ = ["BaseModel", "BaseQuery", "db"]


db = SQLAlchemy()

migrate = Migrate()


def init_db(app):
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", app.config.get("DATABASE_URL"))

    db.init_app(app)
    migrate.init_app(app, db, directory="fairplay/migrations")


class ServerUUID(FunctionElement):
    name = "uuid"


@compiles(ServerUUID)
def compile_uuid(element, compiler, **kwargs):
    return (
        "lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || "
        "'-4' || substr(lower(hex(randomblob(2))),2) || '-' || "
        "substr('89ab',abs(random()) % 4 + 1, 1) || "
        "substr(lower(hex(randomblob(2))),2) || '-' || "
        "lower(hex(randomblob(6)))"
    )


@compiles(ServerUUID, "postgresql")
def compile_uuid_postgresql(element, compiler, **kwargs):
    return "uuid_generate_v1()"


class Secret(FunctionElement):
    name = "secret"

    def __init__(self, length: int = 16, **kwargs):
        self.length = length

        super().__init__(**kwargs)


@compiles(Secret)
def compile_secret(element, compiler, **kwargs):
    return f"lower(hex(randomblob({element.length})))"


@compiles(Secret, "postgresql")
def compile_secret_postgresql(element, compiler, **kwargs):
    return f"lower(encode(gen_random_bytes({element.length}), 'hex'))"


UUID = sqlalchemy_utils.UUIDType()


@sqlalchemy_utils.generic_repr
class BaseModel(db.Model):
    __abstract__ = True

    id = sa.Column(
        UUID,
        default=lambda _: uuid.uuid1(),
        server_default=ServerUUID(),
        primary_key=True,
    )

    created_date = sa.Column(
        sa.DateTime(True),
        default=lambda _: aware_datetime(),
        server_default=sa.func.now(),
        nullable=False,
    )

    last_updated_date = sa.Column(
        sa.DateTime(True),
        default=lambda _: aware_datetime(),
        server_default=sa.func.now(),
        onupdate=lambda _: aware_datetime(),
        server_onupdate=sa.func.now(),
        nullable=False,
    )


Coordinates = sqlalchemy_utils.CompositeType(
    "coordinates",
    (
        sa.Column("lat", sa.Float),
        sa.Column("lon", sa.Float),
        sa.Column("hgt", sa.Float, default=0.0),
    ),
)


# Monetary = sqlalchemy_utils.CompositeType(
#     "monetary",
#     (
#         sa.Column("currency", sqlalchemy_utils.CurrencyType),
#         sa.Column("amount", sa.Numeric(12, 2)),
#     ),
# )


force_instant_defaults()
