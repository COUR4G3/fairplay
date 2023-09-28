import calendar
import datetime as dt
import logging
import uuid

import sqlalchemy as sa
import sqlalchemy.orm as orm
import sqlalchemy.event as event
import sqlalchemy_utils

from flask import current_app, g, has_app_context, has_request_context, request
from sqlalchemy.dialects.postgresql import INET, JSONB

from .auth import current_user
from .db import BaseModel, BaseQuery, ServerUUID, db
from .i18n import _
from .utils.datetime import aware_datetime


logger = logging.getLogger("fairplay.audit")


def default_request_id():
    if not has_request_context():
        return
    if not g.get("audit_request_id"):
        g.audit_request_id = uuid.uuid1()
    return g.audit_request_id


class AuditEventQuery(BaseQuery):
    def filter_by_current_user(self):
        return self.filter_by_user(current_user)

    def filter_by_user(self, user):
        return self.filter(AuditEvent.user == user)


class AuditEvent(BaseModel):
    __tablename__ = "audit"

    CATEGORY_CHOICES = [
        ("record", _("Record")),
        ("security", _("Security")),
    ]

    id = sa.Column(
        sqlalchemy_utils.UUIDType,
        default=lambda _: uuid.uuid4(),
        server_default=ServerUUID(),
    )

    date = sa.Column(
        sa.DateTime(True),
        default=lambda _: aware_datetime(),
        server_default=sa.func.now(),
        nullable=False,
    )

    category = sa.Column(sqlalchemy_utils.ChoiceType(CATEGORY_CHOICES), nullable=False)
    event = sa.Column(sa.String, nullable=False)
    message = sa.Column(sa.String)

    context = sa.Column(sqlalchemy_utils.JSONType().with_variant(JSONB, "postgresql"))

    record_model = sa.Column(sa.String)
    record_id = sa.Column(sqlalchemy_utils.UUIDType)

    remote_addr = sa.Column(
        sqlalchemy_utils.IPAddressType().with_variant(INET, "postgresql"),
        default=lambda _: has_request_context() and request.remote_addr or None,
    )

    request_id = sa.Column(
        sqlalchemy_utils.UUIDType, default=lambda _: default_request_id()
    )

    user_id = sa.Column(
        sqlalchemy_utils.UUIDType,
        sa.ForeignKey("users.id", ondelete="set null"),
        default=lambda _: current_user and current_user.get_id() or None,
    )

    record = sqlalchemy_utils.generic_relationship(record_model, record_id)
    user = orm.relationship("User", lazy="joined")

    __table_args__ = (
        sa.PrimaryKeyConstraint(date, "id", name="pk_audit_date_id"),
        sa.Index("ix_audit_date", date, postgresql_using="brin"),
        sa.Index("ix_audit_category_event", category, event),
        sa.Index(
            "ix_audit_message",
            message,
            postgresql_using="gin",
            postgresql_ops={"message": "gin_trgm_ops"},
        ),
        sa.Index(
            "ix_audit_context",
            context,
            postgresql_using="gin",
            postgresql_ops={"context": "jsonb_ops"},
        ),
        sa.Index("ix_audit_record", record_model, record_id),
        sa.Index(
            "ix_audit_remote_addr",
            remote_addr,
            postgresql_using="gist",
            postgresql_ops={"remote_addr": "gist_inet_ops"},
        ),
        sa.Index("ix_audit_request", request_id),
        sa.Index("ix_audit_user", user_id),
        {"postgresql_partition_by": "RANGE (date)"},
    )

    @classmethod
    def __declare_last__(cls):
        def create_partition(mapper, connection, target):
            date = target.date or aware_datetime()
            date_string = date.strftime("%Y%m")

            end_day = calendar.monthrange(date.year, date.month)[1]
            date_from = date.replace(day=1).strftime("%Y-%m-%d")
            date_to = date.replace(day=end_day) + dt.timedelta(days=1)
            date_to = date_to.strftime("%Y-%m-%d")

            tablename = cls.__tablename__
            partition_name = f"{tablename}_{date_string}"

            db.session.execute(
                sa.text(
                    f"CREATE TABLE IF NOT EXISTS {partition_name} PARTITION OF "
                    f"{tablename} FOR VALUES FROM ('{date_from}') TO ('{date_to}')"
                )
            )

        event.listen(cls, "before_insert", create_partition)


def audit(category, event, message, *args, context=None, record=None):
    if has_request_context():
        if not g.get("audit_request_id"):
            g.audit_request_id = uuid.uuid1()
        request_id = g.audit_request_id
    else:
        request_id = None

    audit = AuditEvent(
        category=category,
        event=event,
        message=message % args,
        context=context,
        record=record,
        request_id=request_id,
    )

    db.session.add(audit)

    if not has_app_context():
        return

    logger.info(
        message,
        *args,
        extra={
            "category": category,
            "event": event,
            "context": context,
            "record_model": audit.record_model,
            "record_id": audit.record_id and str(audit.record_id) or None,
            "remote_addr": request and request.remote_addr or None,
            "request_id": str(request_id),
            "user_id": request and current_user.get_id() or None,
        },
    )


def audit_record_changes(model, schema=None, create=True, delete=True, update=True):
    if isinstance(schema, type):
        schema = schema()

    def get_data(record):
        nonlocal schema
        if schema:
            if isinstance(schema, type):
                schema = schema()

            return schema.dump(record)
        else:
            state = sa.inspect(model)
            data = {}
            for attr in state.attrs:
                data[attr.key] = attr.data

    def before_flush(session, flush_context, instances):
        for instance in session.new:
            if not delete or not isinstance(instance, model):
                continue

            context = {
                "id": str(instance.id),
                "values": get_data(instance),
            }

            message = "Record was created"

            audit("record", "created", message, context=context, record=instance)

        for instance in session.deleted:
            if not delete or not isinstance(instance, model):
                continue

            context = {
                "id": str(instance.id),
                "values": get_data(instance),
            }

            message = "Record was deleted"

            audit("record", "deleted", message, context=context, record=instance)

        for instance in session.dirty:
            if not update or not isinstance(instance, model):
                continue

            state = sa.inspect(instance)
            changes = {}
            for attr in state.attrs:
                if schema and attr.key not in schema.dump_fields:
                    continue

                hist = state.get_history(attr.key, True)

                if not hist.has_changes():
                    continue

                old_value = hist.deleted[0] if hist.deleted else None
                new_value = hist.added[0] if hist.added else None
                changes[attr.key] = [old_value, new_value]

            if not changes:
                return

            context = {
                "id": str(instance.id),
                "changes": changes,
            }

            message = "Record was updated"

            audit("record", "updated", message, context=context, record=instance)

    event.listen(db.session, "before_flush", before_flush)
