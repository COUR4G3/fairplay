import uuid

from flask import abort
from flask import Blueprint
from flask import jsonify
from flask import request
from flask_cors import CORS

from ..auth import current_user
from ..auth import login_required
from ..auth import User
from ..db import db
from .user import UserSchema
from .utils import prepare_schema
from .utils.filtering import apply_filtering
from .utils.ordering import apply_ordering
from .utils.pagination import apply_paged_pagination


users = Blueprint("users", __name__, url_prefix="/users")

CORS(users)
login_required(users)


def get_user(id):
    try:
        id = uuid.UUID(id)
    except ValueError:
        abort(404)

    return get_users().filter(User.id == id).first_or_404()


def get_users():
    return User.query


@users.route("", methods=["POST"])
def create():
    schema = prepare_schema(UserSchema)

    user = schema.load(request.json or request.form, transient=True)
    db.session.add(user)
    db.session.commit()

    return jsonify(schema.dump(user))


@users.route("/<id>", methods=["DELETE"])
def delete(id):
    user = get_user(id)

    db.session.delete(user)
    db.session.commit()

    return "", 204


@users.route("", methods=["GET"])
def list():
    users = get_users()
    users = apply_filtering(users, User.id)
    users = apply_filtering(users, User.name)
    users = apply_filtering(users, User.email)
    users = apply_filtering(users, User.active, default=True)
    users = apply_ordering(users, (User.name, User.email))
    users = apply_paged_pagination(users)

    schema = prepare_schema(UserSchema)
    return jsonify(schema.dump(users, many=True))


@users.route("/<id>", methods=["GET"])
def read(id):
    schema = prepare_schema(UserSchema)

    user = get_user(id)

    return jsonify(schema.dump(user))


@users.route("/<id>", methods=["POST"])
def update(id):
    schema = prepare_schema(UserSchema)

    user = get_user(id)

    schema.load(request.json or request.form, instance=user, partial=True)
    db.session.commit()

    return jsonify(schema.dump(user))
