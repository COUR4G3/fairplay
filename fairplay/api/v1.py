from flask import Blueprint
from marshmallow import ValidationError
from flask_wtf.csrf import CSRFError

from . import api
from .. import __version__


v1 = Blueprint("v1", __name__, url_prefix="/v1")


def init_app(app):
    api.register_blueprint(v1)


@v1.errorhandler(400)
def bad_request(e):
    return {
        "error": {
            "code": 400,
            "description": e.description,
            "name": "bad_request",
        }
    }, 400


@v1.errorhandler(CSRFError)
def csrf_error(e):
    return {
        "error": {
            "code": 400,
            "description": e.description,
            "name": "csrf_error",
        }
    }, 400


@v1.errorhandler(ValidationError)
def validation_error(e):
    return {
        "error": {
            "code": 400,
            "description": "Error validating your request data",
            "name": "validation_error",
            "fields": e.messages_dict,
        }
    }, 400


@v1.errorhandler(401)
def unauthorized(e):
    return {
        "error": {
            "code": 401,
            "description": e.description,
            "name": "unauthorized",
        }
    }, 401


# @v1.errorhandler(402)
# def payment_required(e):
#     return {
#         "error": {
#             "code": 402,
#             "description": e.description,
#             "name": "payment_required",
#         }
#     }, 402


@v1.errorhandler(403)
def forbidden(e):
    return {
        "error": {
            "code": 403,
            "description": e.description,
            "name": "forbidden",
        }
    }, 403


@v1.app_errorhandler(404)
def not_found(e):
    return {
        "error": {
            "code": 404,
            "description": e.description,
            "name": "not_found",
        }
    }, 404


@v1.app_errorhandler(405)
def method_not_allowed(e):
    return {
        "error": {
            "code": 405,
            "description": e.description,
            "name": "method_not_allowed",
        }
    }, 405


@v1.errorhandler(406)
def not_acceptable(e):
    return {
        "error": {
            "code": 406,
            "description": e.description,
            "name": "not_acceptable",
        }
    }, 406


@v1.errorhandler(409)
def conflict(e):
    return {
        "error": {
            "code": 409,
            "description": e.description,
            "name": "conflict",
        }
    }, 409


@v1.errorhandler(415)
def unsupported_media_type(e):
    return {
        "error": {
            "code": 415,
            "description": e.description,
            "name": "unsupported_media_type",
        }
    }, 415


@v1.errorhandler(418)
def im_a_teapot(e):
    return {
        "error": {
            "code": 418,
            "description": e.description,
            "name": "im_a_teapot",
        }
    }, 418


# @v1.errorhandler(420)
# def enhance_your_calm(e):
#     return {
#         "error": {
#             "code": 420,
#             "description": "Enhance your calm, John Spartan.",
#             "name": "enhance_your_calm",
#         }
#     }, 420


@v1.errorhandler(429)
def too_many_requests(e):
    return {
        "error": {
            "code": 429,
            "description": e.description,
            "name": "too_many_requests",
        }
    }, 429


@v1.errorhandler(500)
def server_error(e):
    return {
        "error": {
            "code": 500,
            "description": e.description,
            "name": "server_error",
        }
    }, 500


@v1.errorhandler(503)
def service_unavailable(e):
    return {
        "error": {
            "code": 503,
            "description": e.description,
            "name": "service_unavailable",
        }
    }, 503


@v1.route("/info")
def info():
    """Display basic API information, useful as a noop or connection test."""
    return {
        "api_version": "1.0",
        "deprecated": False,
        "version": __version__,
    }
