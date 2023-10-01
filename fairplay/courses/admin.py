import uuid

import sqlalchemy as sa

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_wtf import FlaskForm
from wtforms import fields, validators
from wtforms.validators import DataRequired

from ..admin import admin
from ..admin.utils.pagination import apply_paged_pagination
from ..db import db
from ..i18n import _
from ..utils.security import safe_redirect
from .models import Course, CourseFeature, CourseHole


courses = Blueprint(
    "courses", __name__, template_folder="templates", url_prefix="/courses"
)


def init_app(app):
    admin.register_blueprint(courses)


def get_course(id):
    try:
        id = uuid.UUID(id)
    except ValueError:
        abort(404)

    courses = get_courses()
    return db.one_or_404(courses.filter(Course.id == id))


def get_courses():
    return Course.query.filter_by_current_user()


class CoordiateField(fields.FormField):
    class PositionForm(FlaskForm):
        lat = fields.FloatField(
            "Latitude",
            validators=(DataRequired(), validators.NumberRange(min=-180.0, max=180.0)),
        )
        lon = fields.FloatField(
            "Longitude",
            validators=(DataRequired(), validators.NumberRange(min=-180.0, max=180.0)),
        )
        hgt = fields.FloatField(
            "Height",
            validators=(validators.Optional(), validators.NumberRange(min=0.0)),
        )

    def __init__(self, label, **kwargs):
        super().__init__(self.PositionForm, label, **kwargs)

    def populate_obj(self, obj, name):
        data = {"lat": self.lat.data, "lon": self.lon.data, "hgt": self.hgt.data}
        setattr(obj, name, data)


class CourseForm(FlaskForm):
    name = fields.StringField("Name", validators=(DataRequired(),))
    description = fields.TextAreaField("Description")
    pos = CoordiateField("Position")


@courses.route("", endpoint="create", methods=["POST"])
@courses.route("/new", endpoint="create", methods=["GET", "POST"])
def create():
    form = CourseForm()

    if form.validate_on_submit():
        course = Course()
        form.populate_obj(course)

        db.session.add(course)
        db.session.commit()

        flash(_("Course created"), "success")

        return redirect(url_for(".read", id=course.id), 303)

    return render_template("admin/courses/course.html", form=form)


@courses.route("", endpoint="delete", methods=["DELETE"])
@courses.route("/<id>", endpoint="delete", methods=["DELETE"])
def delete(id=None):
    next = request.values.get("next")

    if id:
        course = get_course(id)

        db.session.delete(course)
    else:
        ids = request.form.getlist("ids[]")

        courses = get_courses()
        courses = courses.filter(Course.id.in_(ids))
        courses.delete()

    db.session.commit()

    flash(_("Course(s) deleted"), "warning")

    if next:
        return safe_redirect(next)

    return redirect(url_for(".list"), 303)


@courses.route("", endpoint="list", methods=["GET"])
def list():
    courses = get_courses()

    q = request.args.get("q")
    if q:
        courses = courses.filter(
            sa.or_(
                Course.name.ilike(f"%{q}%"),
            )
        )

    courses = apply_paged_pagination(courses)

    return render_template("admin/courses/courses.html", courses=courses)


@courses.route("/<id>", endpoint="update", methods=["POST"])
@courses.route("/<id>", endpoint="read", methods=["GET"])
def read(id):
    course = get_course(id)

    form = CourseForm(obj=course)

    if form.validate_on_submit():
        form.populate_obj(course)

        db.session.commit()

        flash(_("Course updated"), "success")

    holes = CourseHole.query.filter(CourseHole.course == course)
    holes = apply_paged_pagination(holes)

    return render_template(
        "admin/courses/course.html", course=course, form=form, holes=holes
    )


update = read


holes = Blueprint(
    "holes", __name__, template_folder="templates", url_prefix="/<course_id>/holes"
)

courses.register_blueprint(holes)


def get_hole(course_id, number):
    try:
        return get_holes(course_id)[number]
    except IndexError:
        abort(404)


def get_holes(course_id):
    return db.get_or_404(Course, course_id).holes


class CourseHoleForm(FlaskForm):
    number = fields.IntegerField(
        "Number", validators=(DataRequired(), validators.NumberRange(min=1, max=18))
    )
    name = fields.StringField("Name")
    pos = CoordiateField("Position")


@holes.route("", endpoint="create", methods=["POST"])
@holes.route("/new", endpoint="create", methods=["GET", "POST"])
def create_hole(course_id):
    course = get_course(course_id)

    form = CourseHoleForm(
        data={
            "number": course.hole_count + 1,
            "pos": {"lat": course.pos.lat, "lon": course.pos.lon},
        }
    )

    if form.validate_on_submit():
        hole = CourseHole(course=course)
        form.populate_obj(hole)

        db.session.add(hole)
        db.session.commit()

        flash(_("Hole created"), "success")

        return redirect(url_for(".read", course_id=course.id, number=hole.number), 303)

    return render_template("admin/courses/hole.html", course=course, form=form)


@holes.route("", endpoint="delete", methods=["DELETE"])
@holes.route("/<int:number>", endpoint="delete", methods=["DELETE"])
def delete_hole(course_id, number=None):
    next = request.values.get("next")

    if number:
        hole = get_hole(course_id, number)
        course = hole.course

        db.session.delete(hole)
    else:
        course = get_course(course_id)
        ids = request.form.getlist("ids[]")

        holes = CourseHole.query.filter(
            CourseHole.course == course, CourseHole.id.in_(ids)
        )
        holes.delete()

    db.session.commit()

    flash(_("Hole(s) deleted"), "warning")

    if next:
        return safe_redirect(next)

    return redirect(url_for(".list", course_id=course.id), 303)


@holes.route("", endpoint="list", methods=["GET"])
def list_holes(course_id):
    course = get_course(course_id)
    holes = CourseHole.query.filter(CourseHole.course == course)

    q = request.args.get("q")

    holes = apply_paged_pagination(holes)

    return render_template("admin/courses/holes.html", course=course, holes=holes)


@holes.route("/<int:number>", endpoint="update", methods=["POST"])
@holes.route("/<int:number>", endpoint="read", methods=["GET"])
def read_hole(course_id, number):
    hole = get_hole(course_id, number)

    form = CourseHoleForm(obj=hole)

    if form.validate_on_submit():
        form.populate_obj(hole)

        db.session.commit()

        flash(_("Hole updated"), "success")

    features = CourseFeature.query.filter(CourseFeature.hole == hole)
    features = apply_paged_pagination(features)

    return render_template(
        "admin/courses/hole.html",
        course=hole.course,
        hole=hole,
        features=features,
        form=form,
    )


update_hole = read_hole


features = Blueprint(
    "features",
    __name__,
    template_folder="templates",
    url_prefix="<int:number>/features",
)

holes.register_blueprint(features)


def get_feature(course_id, number, id):
    hole = get_hole(course_id, number)
    return db.one_or_404(get_features(hole.id).filter(CourseFeature.id == id))


def get_features(hole_id):
    return CourseFeature.query.filter(CourseFeature.hole_id == hole_id)


class CourseFeatureForm(FlaskForm):
    name = fields.StringField("Name")
    description = fields.TextAreaField("Description")
    coords = CoordiateField("Position")
    type = fields.SelectField(
        "Type", choices=CourseFeature.FEATURE_TYPE_CHOICES, validators=(DataRequired(),)
    )


@features.route("", endpoint="create", methods=["POST"])
@features.route("/new", endpoint="create", methods=["GET", "POST"])
def create_feature(course_id, number):
    hole = get_hole(course_id, number)
    course = hole.course

    form = CourseFeatureForm(
        data={"coords": {"lat": hole.pos.lat, "lon": hole.pos.lon}}
    )

    if form.validate_on_submit():
        feature = CourseFeature(hole=hole)
        form.populate_obj(feature)

        db.session.add(feature)
        db.session.commit()

        flash(_("Feature created"), "success")

        return redirect(
            url_for(".read", course_id=course_id, number=number, id=feature.id),
            303,
        )

    return render_template(
        "admin/courses/feature.html", course=course, hole=hole, form=form
    )


@features.route("", endpoint="delete", methods=["DELETE"])
@features.route("/<id>", endpoint="delete", methods=["DELETE"])
def delete_feature(course_id, number, id=None):
    next = request.values.get("next")

    if id:
        feature = get_feature(course_id, number, id)

        db.session.delete(feature)
    else:
        hole = get_hole(course_id, number)
        ids = request.form.getlist("ids[]")

        features = CourseFeature.query.filter(
            CourseFeature.hole == hole, CourseFeature.id.in_(ids)
        )
        features.delete()

    db.session.commit()

    flash(_("Feature(s) deleted"), "warning")

    if next:
        return safe_redirect(next)

    return redirect(url_for(".list", course_id=course_id, number=number), 303)


@features.route("", endpoint="list", methods=["GET"])
def list_features(course_id, number):
    hole = get_hole(course_id, number)
    features = CourseFeature.query.filter(CourseFeature.hole == hole)

    q = request.args.get("q")

    features = apply_paged_pagination(features)

    return render_template(
        "admin/courses/features.html", course=hole.course, hole=hole, features=features
    )


@features.route("/<id>", endpoint="update", methods=["POST"])
@features.route("/<id>", endpoint="read", methods=["GET"])
def read_feature(course_id, number, id):
    feature = get_feature(course_id, number, id)
    hole = feature.hole

    form = CourseFeatureForm(obj=feature)

    if form.validate_on_submit():
        form.populate_obj(feature)

        db.session.commit()

        flash(_("Feature updated"), "success")

    return render_template(
        "admin/courses/feature.html",
        course=hole.course,
        hole=hole,
        feature=feature,
        form=form,
    )


update_feature = read_feature
