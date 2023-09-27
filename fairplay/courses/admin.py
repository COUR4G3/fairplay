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
from .models import Course


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


class CourseForm(FlaskForm):
    name = fields.StringField("Name", validators=(DataRequired(),))
    description = fields.TextAreaField("Description")


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

    return render_template("admin/courses/course.html", course=course, form=form)


update = read
