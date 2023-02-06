import uuid

from flask import abort
from flask import Blueprint
from flask import jsonify
from flask import request
from flask_cors import CORS
from marshmallow_sqlalchemy import auto_field
from marshmallow_sqlalchemy import SQLAlchemySchema

from ..db import db
from ..models.hole import Hole
from .utils import prepare_schema
from .utils.filtering import apply_filtering
from .utils.ordering import apply_ordering
from .utils.pagination import apply_paged_pagination


holes = Blueprint("holes", __name__, url_prefix="/holes")

CORS(holes)


class HoleSchema(SQLAlchemySchema):
    class Meta:
        load_instance = True
        model = Hole
        session = db.session

    id = auto_field(dump_only=True)
    number = auto_field()


def get_hole(id):
    try:
        id = uuid.UUID(id)
    except ValueError:
        abort(404)

    return get_holes().filter(Hole.id == id).first_or_404()


def get_holes():
    return Hole.query


@holes.route("", methods=["POST"])
def create():
    schema = prepare_schema(HoleSchema)

    hole = schema.load(request.json or request.form, transient=True)
    db.session.add(hole)
    db.session.commit()

    return jsonify(schema.dump(hole))


@holes.route("/<id>", methods=["DELETE"])
def delete(id):
    hole = get_hole(id)

    db.session.delete(hole)
    db.session.commit()

    return "", 204


@holes.route("", methods=["GET"])
def list():
    holes = get_holes()
    holes = apply_filtering(holes, Hole.id)
    holes = apply_filtering(holes, Hole.number)
    holes = apply_ordering(holes, (Hole.number,))
    holes = apply_paged_pagination(holes)

    schema = prepare_schema(HoleSchema)
    return jsonify(schema.dump(holes, many=True))


@holes.route("/<id>", methods=["GET"])
def read(id):
    schema = prepare_schema(HoleSchema)

    hole = get_hole(id)

    return jsonify(schema.dump(hole))


@holes.route("/<id>", methods=["POST"])
def update(id):
    schema = prepare_schema(HoleSchema)

    hole = get_hole(id)

    schema.load(request.json or request.form, instance=hole, partial=True)
    db.session.commit()

    return jsonify(schema.dump(hole))
