from flask import Blueprint, request, url_for
from marshmallow import ValidationError, fields, validate
from marshmallow_sqlalchemy import SQLAlchemySchema

from ..api.v1 import v1
from ..api.utils.pagination import apply_paged_pagination
from ..courses.api import validate_course
from ..courses.models import current_course
from ..db import db
from .models import Game, GameHole


games = Blueprint("games", __name__, url_prefix="/games")


def init_app(app):
    v1.register_blueprint(games)


class GameSchema(SQLAlchemySchema):
    class Meta:
        load_instance = True
        model = Game
        session = db.session

    id = fields.UUID(dump_only=True)
    name = fields.String(required=True)

    course_id = fields.UUID(required=True)


def get_games():
    return Game.query


def get_game(id):
    games = get_games()

    return db.one_or_404(games.filter(Game.id == id))


def validate_game(id):
    valid = db.session.query(
        Game.query.filter_by_current_user().filter(Game.id == id).exists()
    ).scalar()

    if not valid:
        raise ValidationError("Game not found")


@games.route("", methods=["POST"])
def create():
    schema = GameSchema()

    data = (request.form or request.json).copy()

    if "course_id" in data:
        schema.course_id.validators.append(validate_course)
    else:
        data["course_id"] = current_course.id

    game = schema.load(data, session=db.session, transient=True)

    db.session.add(game)
    db.session.commit()

    headers = {"Location": url_for(".read", id=game.id)}

    return schema.dump(game), headers, 201


@games.route("/<id>", methods=["DELETE"])
def delete(id):
    game = get_game(id)

    db.session.delete(game)
    db.session.commit()

    return "", 204


@games.route("", methods=["GET"])
def list():
    games = get_games()

    games = apply_paged_pagination(games)

    schema = GameSchema()
    return schema.dump(games, many=True)


@games.route("/<id>", methods=["GET"])
def read(id):
    game = get_game(id)

    schema = GameSchema()
    return schema.dump(game)


@games.route("/<id>", methods=["POST"])
def update(id):
    schema = GameSchema(exclude=("course_id",))

    data = request.form or request.json
    game = get_game(id)
    schema.load(data, session=db.session, instance=game, partial=True)

    db.session.commit()

    schema = GameSchema()
    return schema.dump(game)


holes = Blueprint("holes", __name__)

games.register_blueprint(holes)


class GameHoleSchema(SQLAlchemySchema):
    class Meta:
        load_instance = True
        model = GameHole
        session = db.session

    id = fields.UUID(dump_only=True)
    number = fields.Integer(required=True, validate=(validate.Range(min=1),))
    index = fields.Integer(validate=(validate.Range(min=0),))
    par = fields.Integer(validate=(validate.Range(min=3, max=5),))
    game_id = fields.UUID(required=True)


def get_game_holes(game_id=None):
    holes = GameHole.query

    if game_id:
        holes = holes.filter(GameHole.game_id == game_id)

    return holes


def get_game_hole(game_id=None, id=None, number=None):
    holes = get_game_holes(game_id=game_id)

    if id:
        return db.one_or_404(holes.filter(GameHole.id == id))
    else:
        return db.one_or_404(holes.filter(GameHole.number == number))


@holes.route("/holes", endpoint="list", methods=["POST"])
@holes.route("/<game_id>/holes", endpoint="list", methods=["POST"])
def list_holes(game_id=None):
    holes = get_game_holes(game_id=game_id)

    holes = apply_paged_pagination(holes)

    schema = GameHoleSchema()
    return schema.dump(holes, many=True)


@holes.route("/holes/<id>", endpoint="read", methods=["GET"])
@holes.route("/<game_id>/holes/<number>", endpoint="read", methods=["GET"])
def read_hole(game_id=None, id=None, number=None):
    hole = get_game_hole(game_id=game_id, id=id, number=number)

    schema = GameHoleSchema()
    return schema.dump(hole)


@holes.route("/holes/<id>", endpoint="update", methods=["POST"])
@holes.route("/<game_id>/holes/<number>", endpoint="update", methods=["POST"])
def update_hole(game_id=None, id=None, number=None):
    schema = GameHoleSchema(exclude=("game_id", "number"))

    data = request.form or request.json
    hole = get_game_hole(game_id=game_id, id=id, number=number)
    schema.load(data, session=db.session, instance=hole, partial=True)

    db.session.commit()

    schema = GameHoleSchema()
    return schema.dump(hole)
