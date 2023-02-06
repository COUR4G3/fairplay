import typing as t

from marshmallow import Schema

from .filtering import filter_only_fields


def prepare_schema(
    schema: t.Type[Schema], default_exclude: t.Sequence[str] = ()
):
    only = filter_only_fields()
    if not only:
        exclude = default_exclude
    else:
        exclude = tuple()

    return schema(exclude=exclude, only=only)
