import typing as t
from itertools import chain

import sqlalchemy as sa
from flask import request
from flask_sqlalchemy import BaseQuery
from marshmallow import ValidationError
from sqlalchemy.orm import InstrumentedAttribute

from ...i18n import _


def apply_ordering(
    query: BaseQuery,
    fields: t.Iterable[t.Union[sa.Column, t.Tuple[sa.Column, str]]],
    param_name: str = "order",
    default: t.Optional[sa.Column] = None,
):
    order = chain(
        px for p in request.args.getlist(param_name) for px in p.split(",")
    )

    field_mapping = {}
    for field in fields:
        if isinstance(field, (InstrumentedAttribute, sa.Column)):
            name = field.name
        else:
            field, name = field

        field_mapping[name] = field

    for order_field in order:
        desc = order_field.startswith("-")
        if desc:
            order_field = order_field[1:]

        try:
            field = field_mapping[order_field]
        except KeyError:
            raise ValidationError(
                _("Cannot order by field `{}`").format(order_field),
                "order",
            )

        if desc:
            query = query.order_by(field.desc())
        else:
            query = query.order_by(field)

    return query
