import typing as t

import sqlalchemy as sa
from flask import after_this_request
from flask import current_app
from flask import request
from flask import url_for
from flask_sqlalchemy import BaseQuery
from itsdangerous import BadData
from itsdangerous import URLSafeSerializer
from marshmallow import ValidationError


DEFAULT_LIMIT = 100
DEFAULT_MAX_LIMIT = 1000
DEFAULT_MAX_PER_PAGE = 1000
DEFAULT_PER_PAGE = 20


def get_cursor_signer():
    return URLSafeSerializer(current_app.secret_key, "cursor-pagination")


def apply_cursor_pagination(
    query: BaseQuery,
    field: t.Union[sa.Column, str],
    cursor: t.Optional[str] = None,
    limit: t.Optional[int] = None,
    max_limit: t.Optional[int] = None,
    cursor_param: str = "cursor",
    limit_param: str = "limit",
):
    """Apply cursor pagination to large dynamic results."""
    if isinstance(field, sa.Column):
        field = field.name
    if limit is None:
        limit = DEFAULT_LIMIT
    if max_limit is None:
        max_limit = DEFAULT_MAX_LIMIT

    if cursor is None:
        cursor = request.args.get("cursor")

    s = get_cursor_signer()

    if cursor:
        try:
            direction, value, offset = s.loads(cursor)
        except BadData:
            raise ValidationError("Invalid or malformed cursor", "cursor")
    else:
        value = 0
        direction = "next"
        offset = 0

    limit = min(limit, max_limit)

    total = query.count()

    query = query.limit(limit).offset(offset)

    items = query.all()

    args = request.args.copy()

    args["cursor"] = cursor = s.dumps((direction, value, offset))
    link_headers = {"self": url_for(request.endpoint, **args)}

    next_value = items and getattr(items[-1], field) or value
    next_offset = sum(1 for i in items if getattr(i, field) == next_value) - 1
    args["cursor"] = s.dumps(("next", next_value, next_offset))
    link_headers["next"] = url_for(request.endpoint, **args)

    prev_value = items and getattr(items[0], field) or value
    prev_offset = sum(1 for i in items if getattr(i, field) == prev_value) - 1
    args["cursor"] = s.dumps(("prev", prev_value, prev_offset))
    link_headers["prev"] = url_for(request.endpoint, **args)

    headers = {
        "Link": ", ".join(
            f'<{url}>; rel="{rel}"' for rel, url in link_headers.items()
        ),
        "X-Pagination-Count": len(items),
        "X-Pagination-Cursor": cursor,
        "X-Pagination-Limit": limit,
        "X-Pagination-Total": total,
    }

    @after_this_request
    def add_pagination_headers(response):
        response.headers.update(headers)
        return response

    return items


def apply_paged_pagination(
    query: BaseQuery,
    page: t.Optional[int] = None,
    per_page: t.Optional[int] = None,
    max_per_page: t.Optional[int] = None,
    page_param: str = "page",
    per_page_param: str = "per_page",
):
    """Apply paged pagination to results."""
    if page is None:
        page = int(request.args.get("page", 1))
    if per_page is None:
        per_page = int(request.args.get("per_page", DEFAULT_PER_PAGE))
    if max_per_page is None:
        max_per_page = DEFAULT_MAX_PER_PAGE

    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False,
        max_per_page=max_per_page,
    )

    args = request.args.copy()
    link_headers = {"self": url_for(request.endpoint, **args)}

    if pagination.page > 1:
        args["page"] = 1
        link_headers["first"] = url_for(request.endpoint, **args)

    if pagination.has_next:
        args["page"] = str(pagination.next_num)
        link_headers["next"] = url_for(request.endpoint, **args)

    if pagination.has_prev:
        args["page"] = str(pagination.prev_num)
        link_headers["prev"] = url_for(request.endpoint, **args)

    if pagination.page < pagination.pages:
        args["page"] = pagination.pages
        link_headers["first"] = url_for(request.endpoint, **args)

    headers = {
        "Link": ", ".join(
            f'<{url}>; rel="{rel}"' for rel, url in link_headers.items()
        ),
        "X-Pagination-Count": len(pagination.items),
        "X-Pagination-Page": pagination.page,
        "X-Pagination-Pages": pagination.pages,
        "X-Pagination-Per-Page": pagination.per_page,
        "X-Pagination-Total": pagination.total,
    }

    @after_this_request
    def add_pagination_headers(response):
        response.headers.update(headers)
        return response

    return pagination.items
