import operator
import typing as t
from functools import partial
from itertools import chain

import sqlalchemy as sa
from flask import request
from flask_sqlalchemy import BaseQuery
from marshmallow import Schema
from marshmallow import ValidationError
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.orm import relationship
from sqlalchemy.sql.base import _entity_namespace
from sqlalchemy.sql.base import _entity_namespace_key


def get_filter_funcs(field: sa.Column, filters):
    funcs = {
        "eq": partial(operator.eq, field),
        "in": field.in_,
        "is": field.is_,
        "is_not": field.is_not,
        "ne": partial(operator.ne, field),
        "not_in": field.not_in,
    }

    if isinstance(field, InstrumentedAttribute):
        pass
    elif isinstance(
        field.type, (sa.Date, sa.DateTime, sa.Float, sa.Integer, sa.Numeric)
    ):
        funcs.update(
            {
                "ge": partial(operator.ge, field),
                "gt": partial(operator.gt, field),
                "le": partial(operator.le, field),
                "lt": partial(operator.lt, field),
            }
        )
    elif isinstance(field.type, sa.String):
        funcs.update(
            {
                "contains": field.contains,
                "endswith": field.endswith,
                "icontains": lambda value: field.ilike(f"%{value}%"),
                "ilike": field.ilike,
                "like": field.like,
                "not_ilike": field.not_ilike,
                "not_like": field.not_like,
                "startswith": field.startswith,
            }
        )

    funcs.update(**filters)

    return funcs


def apply_filtering(
    query: BaseQuery,
    field: sa.Column,
    field_param: t.Optional[str] = None,
    default: t.Any = None,
    **filters,
):
    funcs = get_filter_funcs(field, filters)

    if not field_param:
        field_param = field.name

    for param, value in request.args.items():
        if param.split("__", 1)[0] != field_param:
            continue

        if "__" in param:
            op = param.split("__", 1)[-1]
        else:
            op = "eq"

        func = funcs.get(op)
        if not func:
            raise ValidationError(f"Invalid operator `{op}`", param)

        query = query.filter(func(value))
    else:
        if default:
            query = query.filter(field == default)

    return query


def filter_only_fields(field_param: str = "fields"):
    fields = chain(
        px for p in request.args.getlist(field_param) for px in p.split(",")
    )

    if fields:
        return ["id"] + [f for f in fields]
