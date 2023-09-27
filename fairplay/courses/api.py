from flask import Blueprint, request, url_for
from marshmallow import ValidationError, fields, validate
from marshmallow_sqlalchemy import SQLAlchemySchema

from ..api.v1 import v1
from ..api.utils.conditional import (
    add_etag_header,
    add_last_modified_header,
    check_if_match,
    check_if_modified_since,
    check_if_none_match,
    check_if_unmodified_since,
)
from ..api.utils.pagination import apply_paged_pagination
from ..db import db
from .models import Course, CourseHole


courses = Blueprint("courses", __name__, url_prefix="/courses")


def init_app(app):
    v1.register_blueprint(courses)


class CourseSchema(SQLAlchemySchema):
    class Meta:
        load_instance = True
        model = Course
        session = db.session

    id = fields.UUID(dump_only=True)
    name = fields.String(required=True)


def get_courses():
    return Course.query


def get_course(id):
    courses = get_courses()

    return db.one_or_404(courses.filter(Course.id == id))


def validate_course(id):
    valid = db.session.query(
        Course.query.filter_by_current_user().filter(Course.id == id).exists()
    ).scalar()

    if not valid:
        raise ValidationError("Course not found")


@courses.route("", methods=["POST"])
def create():
    schema = CourseSchema()

    data = request.form or request.json
    course = schema.load(data, session=db.session, transient=True)

    db.session.add(course)
    db.session.commit()

    add_etag_header(course, schema)
    add_last_modified_header(course)

    headers = {"Location": url_for(".read", id=course.id)}

    return schema.dump(course), headers, 201


@courses.route("/<id>", methods=["DELETE"])
def delete(id):
    course = get_course(id)

    check_if_match(course, CourseSchema())
    check_if_unmodified_since(course)

    db.session.delete(course)
    db.session.commit()

    return "", 204


@courses.route("", methods=["GET"])
def list():
    courses = get_courses()

    courses = apply_paged_pagination(courses)

    schema = CourseSchema()
    return schema.dump(courses, many=True)


@courses.route("/<id>", methods=["GET"])
def read(id):
    course = get_course(id)

    schema = CourseSchema()

    add_etag_header(course, schema)
    add_last_modified_header(course)

    check_if_modified_since(course)
    check_if_none_match(course, schema)

    return schema.dump(course)


@courses.route("/<id>", methods=["POST"])
def update(id):
    schema = CourseSchema()

    data = request.form or request.json
    course = get_course(id)

    check_if_match(course, schema)
    check_if_unmodified_since(course)

    schema.load(data, session=db.session, instance=course, partial=True)

    db.session.commit()

    add_etag_header(course, schema)
    add_last_modified_header(course)

    return schema.dump(course)


holes = Blueprint("holes", __name__)

courses.register_blueprint(holes)


class CourseHoleSchema(SQLAlchemySchema):
    class Meta:
        load_instance = True
        model = CourseHole
        session = db.session

    id = fields.UUID(dump_only=True)
    number = fields.Integer(required=True, validate=(validate.Range(min=1),))
    index = fields.Integer(validate=(validate.Range(min=0),))
    par = fields.Integer(validate=(validate.Range(min=3, max=5),))
    course_id = fields.UUID(required=True)


def get_course_holes(course_id=None):
    holes = CourseHole.query

    if course_id:
        holes = holes.filter(CourseHole.course_id == course_id)

    return holes


def get_course_hole(course_id=None, id=None, number=None):
    holes = get_course_holes(course_id=course_id)

    if id:
        return db.one_or_404(holes.filter(CourseHole.id == id))
    else:
        return db.one_or_404(holes.filter(CourseHole.number == number))


@holes.route("/holes", endpoint="create", methods=["POST"])
@holes.route("/<course_id>/holes/<number>", endpoint="create", methods=["PUT"])
@holes.route("/<course_id>/holes", endpoint="create", methods=["POST"])
def create_hole(course_id=None, number=None):
    schema = CourseHoleSchema()

    data = (request.form or request.json).copy()

    # 404 if course_id is not found, since path is now invalid
    if course_id:
        course = get_course(course_id)
        data["course_id"] = course.id
    else:
        schema.course_id.validators.append(validate_course)

    if number:
        data["number"] = number

    hole = schema.load(data, session=db.session, transient=True)

    db.session.add(hole)
    db.session.commit()

    if course_id:
        headers = {
            "Location": url_for(".read_hole", course_id=course_id, number=hole.number)
        }
    else:
        headers = {"Location": url_for(".read_hole", id=hole.id)}

    add_etag_header(hole, schema)
    add_last_modified_header(hole)

    return schema.dump(hole), headers, 201


@holes.route("/holes/<id>", endpoint="delete", methods=["DELETE"])
@holes.route("/<course_id>/holes/<number>", endpoint="delete", methods=["DELETE"])
def delete_hole(course_id=None, id=None, number=None):
    hole = get_course_hole(course_id=course_id, id=id, number=number)

    check_if_match(hole, CourseSchema())
    check_if_unmodified_since(hole)

    db.session.delete(hole)
    db.session.commit()

    return "", 204


@holes.route("/holes", endpoint="list", methods=["GET"])
@holes.route("/<course_id>/holes", endpoint="list", methods=["GET"])
def list_holes(course_id=None):
    holes = get_course_holes(course_id=course_id)

    holes = apply_paged_pagination(holes)

    schema = CourseHoleSchema()
    return schema.dump(holes, many=True)


@holes.route("/holes/<id>", endpoint="read", methods=["GET"])
@holes.route("/<course_id>/holes/<number>", endpoint="read", methods=["GET"])
def read_hole(course_id=None, id=None, number=None):
    hole = get_course_hole(course_id=course_id, id=id, number=number)

    schema = CourseHoleSchema()

    add_etag_header(hole, schema)
    add_last_modified_header(hole)

    check_if_modified_since(hole)
    check_if_none_match(hole, schema)

    return schema.dump(hole)


@holes.route("/holes/<id>", endpoint="update", methods=["POST"])
@holes.route("/<course_id>/holes/<number>", endpoint="update", methods=["POST"])
def update_hole(course_id=None, id=None, number=None):
    schema = CourseHoleSchema(exclude=("course_id",))

    data = request.form or request.json
    hole = get_course_hole(course_id=course_id, id=id, number=number)

    check_if_match(hole, CourseHoleSchema())
    check_if_unmodified_since(hole)

    schema.load(data, session=db.session, instance=hole, partial=True)

    db.session.commit()

    schema = CourseHoleSchema()

    add_etag_header(hole, schema)
    add_last_modified_header(hole)

    return schema.dump(hole)
