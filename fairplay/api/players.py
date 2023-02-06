import uuid

from flask import abort
from flask import Blueprint
from flask import jsonify
from flask import request
from flask_cors import CORS
from marshmallow import fields
from marshmallow_sqlalchemy import auto_field
from marshmallow_sqlalchemy import SQLAlchemySchema

from ..db import db
from ..models.player import Player
from .utils import prepare_schema
from .utils.filtering import apply_filtering
from .utils.ordering import apply_ordering
from .utils.pagination import apply_paged_pagination


players = Blueprint("players", __name__, url_prefix="/players")

CORS(players)


class PlayerSchema(SQLAlchemySchema):
    class Meta:
        load_instance = True
        model = Player
        session = db.session

    id = auto_field(dump_only=True)
    name = auto_field()


def get_player(id):
    try:
        id = uuid.UUID(id)
    except ValueError:
        abort(404)

    return get_players().filter(Player.id == id).first_or_404()


def get_players():
    return Player.query


@players.route("", methods=["POST"])
def create():
    schema = prepare_schema(PlayerSchema)

    player = schema.load(request.json or request.form, transient=True)
    db.session.add(player)
    db.session.commit()

    return jsonify(schema.dump(player))


@players.route("/<id>", methods=["DELETE"])
def delete(id):
    player = get_player(id)

    db.session.delete(player)
    db.session.commit()

    return "", 204


@players.route("", methods=["GET"])
def list():
    players = get_players()
    players = apply_filtering(players, Player.id)
    players = apply_filtering(players, Player.name)
    players = apply_ordering(players, (Player.name,))
    players = apply_paged_pagination(players)

    schema = prepare_schema(PlayerSchema)
    return jsonify(schema.dump(players, many=True))


@players.route("/<id>", methods=["GET"])
def read(id):
    schema = prepare_schema(PlayerSchema)

    player = get_player(id)

    return jsonify(schema.dump(player))


@players.route("/<id>", methods=["POST"])
def update(id):
    schema = prepare_schema(PlayerSchema)

    player = get_player(id)

    schema.load(request.json or request.form, instance=player, partial=True)
    db.session.commit()

    return jsonify(schema.dump(player))
