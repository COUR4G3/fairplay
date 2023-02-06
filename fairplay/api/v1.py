from flask import Blueprint
from flask import g
from flask import jsonify
from flask_cors import cross_origin
from flask_wtf.csrf import CSRFError
from flask_wtf.csrf import generate_csrf
from marshmallow import ValidationError

from .. import __version__
from ..utils.datetime import aware_datetime
from .courses import courses
from .games import games
from .holes import holes
from .players import players
from .user import user
from .users import users


v1 = Blueprint("v1", __name__, url_prefix="/v1")


v1.register_blueprint(courses)
v1.register_blueprint(games)
v1.register_blueprint(holes)
v1.register_blueprint(players)
v1.register_blueprint(user)
v1.register_blueprint(users)


@v1.errorhandler(CSRFError)
def csrf_error(e: CSRFError):
    return {
        "code": 400,
        "description": e.description,
        "name": "csrf_error",
    }, 400


@v1.errorhandler(400)
def bad_request(e):
    return {
        "code": 400,
        "description": e.description,
        "name": "bad_request",
    }, 400


@v1.errorhandler(ValidationError)
def validation_error(e: ValidationError):
    data = {
        "code": 400,
        "description": "Validation error",
        "name": "validation_error",
    }

    if e.field_name == "_schema":
        data["fields"] = e.messages
    else:
        data["fields"] = {e.field_name: e.messages}

    return data, 400


@v1.route("/csrf-token")
def csrf_token():
    generate_csrf()
    return jsonify({"csrf_token": g.csrf_token})


@v1.route("/info")
@cross_origin()
def info():
    return jsonify(
        {
            "date": aware_datetime().isoformat(),
            "version": __version__,
        }
    )
