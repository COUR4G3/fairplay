import datetime as dt
import uuid

import sqlalchemy as sa
from flask import abort
from flask import Blueprint
from flask import jsonify
from flask import request
from flask_cors import CORS
from marshmallow import ValidationError
from marshmallow_sqlalchemy import auto_field
from marshmallow_sqlalchemy import SQLAlchemySchema

from ..db import db
from ..models.course import Course
from ..models.hole import Hole
from ..models.game import Game
from ..models.player import Player
from .holes import HoleSchema
from .games import GameSchema
from .utils import prepare_schema
from .utils.filtering import apply_filtering
from .utils.ordering import apply_ordering
from .utils.pagination import apply_paged_pagination


courses = Blueprint("courses", __name__, url_prefix="/courses")

CORS(courses)


class CourseSchema(SQLAlchemySchema):
    class Meta:
        load_instance = True
        model = Course
        session = db.session

    id = auto_field(dump_only=True)
    name = auto_field()


def get_course(id):
    try:
        id = uuid.UUID(id)
    except ValueError:
        abort(404)

    return get_courses().filter(Course.id == id).first_or_404()


def get_courses():
    return Course.query


def get_hole(id, number):
    try:
        return next(filter(lambda h: h.number == number, get_holes(id)))
    except StopIteration:
        abort(404)


def get_holes(id):
    course = get_course(id)
    return course.holes


@courses.route("", methods=["POST"])
def create():
    schema = prepare_schema(CourseSchema)

    course = schema.load(request.json or request.form, transient=True)
    db.session.add(course)
    db.session.commit()

    return jsonify(schema.dump(course))


@courses.route("/<id>/holes", methods=["POST"])
@courses.route("/<id>/holes/<number>", methods=["PUT"])
def create_hole(id, number=None):
    course = get_course(id)

    schema = prepare_schema(HoleSchema, default_exclude=("course",))

    data = (request.json or request.form).copy()
    data["course_id"] = str(course.id)
    if number is not None:
        data["number"] = number

    hole = schema.load(data, transient=True)
    db.session.add(hole)
    db.session.commit()

    return jsonify(schema.dump(hole))


@courses.route("/<id>", methods=["DELETE"])
def delete(id):
    course = get_course(id)

    db.session.delete(course)
    db.session.commit()

    return "", 204


@courses.route("/<id>/holes/<number>", methods=["DELETE"])
def delete_hole(id, number):
    hole = get_hole(id, number)

    db.session.delete(hole)
    db.session.commit()

    return "", 204


@courses.route("", methods=["GET"])
def list():
    courses = get_courses()
    courses = apply_filtering(courses, Course.id)
    courses = apply_filtering(courses, Course.name)
    courses = apply_filtering(courses, Course.hole_count)
    courses = apply_ordering(courses, (Course.name,))
    courses = apply_paged_pagination(courses)

    schema = prepare_schema(CourseSchema)
    return jsonify(schema.dump(courses, many=True))


@courses.route("/<id>/holes", methods=["GET"])
def list_holes(id):
    holes = get_holes(id)

    holes = apply_filtering(holes, Hole.number)
    holes = apply_ordering(holes, (Hole.number,), default=Hole.number)
    holes = apply_paged_pagination(holes)

    schema = prepare_schema(HoleSchema, default_exclude=("course",))
    return jsonify(schema.dump(holes, many=True))


@courses.route("/<id>", methods=["GET"])
def read(id):
    schema = prepare_schema(CourseSchema)

    course = get_course(id)

    return jsonify(schema.dump(course))


@courses.route("/<id>/holes/<number>", methods=["GET"])
def read_hole(id, number):
    schema = prepare_schema(HoleSchema, default_exclude=("course",))

    hole = get_hole(id, number)

    return jsonify(schema.dump(hole))


@courses.route("/<id>/roster/<date>", methods=["GET"])
def roster(id, date):
    try:
        date = dt.datetime.strptime("%Y%m%d").date()
    except ValueError:
        try:
            date = dt.datetime.strptime("%Y-%m-%d").date()
        except ValueError:
            try:
                date = dt.datetime.strptime("%Y%m%d").date()
            except ValueError:
                raise ValidationError("Invalid date format", "date")

    course = get_course(id)
    games = course.games.filter(
        (sa.func.date(Game.date_planned) | sa.func.date(Game.date_started))
        == date
    ).all()

    games = apply_filtering(games, Game.player_count)
    games = apply_filtering(
        games,
        sa.func.time(Game.date_planned) | sa.func.time(Game.date_started),
        "time",
    )
    games = apply_filtering(games, Player.id | Player.name, "player")
    games = apply_paged_pagination(games)

    schema = prepare_schema(GameSchema, default_exclude=("course",))
    return jsonify(schema.dump(games, many=True))


@courses.route("/<id>", methods=["POST"])
def update(id):
    schema = prepare_schema(CourseSchema)

    course = get_course(id)

    schema.load(request.json or request.form, instance=course, partial=True)
    db.session.commit()

    return jsonify(schema.dump(course))


@courses.route("/<id>/holes/<number>", methods=["POST"])
def update_hole(id, number):
    schema = prepare_schema(HoleSchema, default_exclude=("course",))

    hole = get_hole(id, number)

    schema.load(request.json or request.form, instance=hole, partial=True)
    db.session.commit()

    return jsonify(schema.dump(hole))
