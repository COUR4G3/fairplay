import hashlib

from flask import abort, make_response, request


def check_if_match(obj, schema, generate_etag_func=None):
    if not generate_etag_func:
        generate_etag_func = generate_etag
    etag = generate_etag_func(obj, schema)

    if etag not in request.if_match:
        abort(412)


def check_if_modified_since(obj, attr="last_updated_date"):
    last_updated = getattr(obj, attr)
    if last_updated <= request.if_unmodified_since:
        abort(make_response("", 304))


def check_if_none_match(obj, schema, generate_etag_func=None):
    if not generate_etag_func:
        generate_etag_func = generate_etag
    etag = generate_etag_func(obj, schema)

    if etag in request.if_none_match:
        abort(make_response("", 304))


def check_if_unmodified_since(obj, attr="last_updated_date"):
    last_updated = getattr(obj, attr)
    if last_updated > request.if_unmodified_since:
        abort(412)


def generate_etag(obj, schema):
    data = schema.dumps(obj)
    h = hashlib.sha1(data.encode("utf-8"))
    return f'W/"{h.hexdigest()[:7]}"'
