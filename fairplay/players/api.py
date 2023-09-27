from flask import Blueprint, request, url_for

from marshmallow import fields, validate
from marshmallow_sqlalchemy import SQLAlchemySchema

from ..api.v1 import v1
from ..api.utils.pagination import apply_paged_pagination
from ..courses.api import validate_course
from ..courses.models import current_course
from ..db import db
from .models import Player


players = Blueprint("players", __name__, url_prefix="/players")


def init_app(app):
    v1.register_blueprint(players)


class PlayerSchema(SQLAlchemySchema):
    class Meta:
        load_instance = True
        model = Player
        session = db.session

    id = fields.UUID(dump_only=True)
    name = fields.String(required=True)
    handicap = fields.Integer()
    course_id = fields.UUID(required=True, validate=(validate_course,))


def get_players():
    return Player.query.filter_by_current_course()


def get_player(id):
    players = get_players()

    return db.one_or_404(players.filter(Player.id == id))


@players.route("", methods=["POST"])
def create():
    schema = PlayerSchema()

    data = (request.form or request.json).copy()
    data.setdefault("course_id", current_course.id)

    player = schema.load(data, session=db.session, transient=True)

    db.session.add(player)
    db.session.commit()

    headers = {"Location": url_for(".read", id=player.id)}

    return schema.dump(player), headers, 201


@players.route("/<id>", methods=["DELETE"])
def delete(id):
    player = get_player(id)

    db.session.delete(player)
    db.session.commit()

    return "", 204


@players.route("", methods=["GET"])
def list():
    players = get_players()

    players = apply_paged_pagination(players)

    schema = PlayerSchema()
    return schema.dump(players, many=True)


@players.route("/<id>", methods=["GET"])
def read(id):
    player = get_player(id)

    schema = PlayerSchema()
    return schema.dump(player)


@players.route("/<id>", methods=["POST"])
def update(id):
    schema = PlayerSchema()

    data = request.form or request.json
    player = get_player(id)
    schema.load(data, session=db.session, instance=player, partial=True)

    db.session.commit()

    return schema.dump(player)
