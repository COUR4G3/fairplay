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
from ..models.game import Game
from ..models.player import Player
from .utils import prepare_schema
from .utils.filtering import apply_filtering
from .utils.ordering import apply_ordering
from .utils.pagination import apply_paged_pagination


games = Blueprint("games", __name__, url_prefix="/games")

CORS(games)


class GameSchema(SQLAlchemySchema):
    class Meta:
        load_instance = True
        model = Game
        session = db.session

    id = auto_field(dump_only=True)
    player_count = fields.Integer(dump_only=True)
    players = auto_field()


def get_game(id):
    try:
        id = uuid.UUID(id)
    except ValueError:
        abort(404)

    return get_games().filter(Game.id == id).first_or_404()


def get_games():
    return Game.query


@games.route("", methods=["POST"])
def create():
    schema = prepare_schema(GameSchema)

    game = schema.load(request.json or request.form, transient=True)
    db.session.add(game)
    db.session.commit()

    return jsonify(schema.dump(game))


@games.route("/<id>", methods=["DELETE"])
def delete(id):
    game = get_game(id)

    db.session.delete(game)
    db.session.commit()

    return "", 204


@games.route("", methods=["GET"])
def list():
    games = get_games()
    games = apply_filtering(games, Game.id)
    games = apply_filtering(games, Game.player_count)
    games = apply_filtering(games, Player.id | Player.name, "player")
    games = apply_ordering(games, (Game.date_planned,))
    games = apply_paged_pagination(games)

    schema = prepare_schema(GameSchema)
    return jsonify(schema.dump(games, many=True))


@games.route("/<id>", methods=["GET"])
def read(id):
    schema = prepare_schema(GameSchema)

    game = get_game(id)

    return jsonify(schema.dump(game))


@games.route("/<id>", methods=["POST"])
def update(id):
    schema = prepare_schema(GameSchema)

    game = get_game(id)

    schema.load(request.json or request.form, instance=game, partial=True)
    db.session.commit()

    return jsonify(schema.dump(game))
