import uuid

import sqlalchemy as sa

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_wtf import FlaskForm
from wtforms import fields, validators
from wtforms.validators import DataRequired

from . import current_user
from ..admin import admin
from ..admin.utils.pagination import apply_paged_pagination
from ..audit import AuditEvent
from ..db import db
from ..i18n import _, get_locale, get_timezone, iter_locales, iter_timezones
from ..utils.security import safe_redirect
from .models import User


auth = Blueprint("auth", __name__, template_folder="templates", url_prefix="/auth")


def init_app(app):
    admin.register_blueprint(auth)


users = Blueprint("users", __name__, url_prefix="/users")

auth.register_blueprint(users)


def get_user(id):
    try:
        id = uuid.UUID(id)
    except ValueError:
        abort(404)

    users = get_users()
    return users.filter(User.id == id).first_or_404()


def get_users():
    return User.query


def get_audit_event(id, user_id=None):
    events = get_audit_events(user_id=user_id)

    events = events.filter(AuditEvent.id == id)

    return events.one_or_404()


def get_audit_events(user_id=None):
    events = AuditEvent.query

    if user_id:
        events = events.filter(
            AuditEvent.record_model == "User", AuditEvent.record_id == user_id
        )

    events = events.order_by(AuditEvent.date.desc())

    return events


class UserForm(FlaskForm):
    name_first = fields.StringField("First name", validators=(DataRequired(),))
    name_last = fields.StringField("Last name", validators=(DataRequired(),))
    email = fields.EmailField(
        "Email address", validators=(DataRequired(), validators.Email())
    )
    active = fields.BooleanField("Active", default=True)

    lang = fields.SelectField(
        "Language", default=get_locale, choices=lambda: iter_locales(flagize=True)
    )
    default_tz = fields.SelectField(
        "Default timezone", default=get_timezone, choices=iter_timezones
    )
    tz = fields.SelectField(
        "Current timezone", default=get_timezone, choices=iter_timezones
    )


@users.route(
    "/<user_id>/audit-events/<id>",
    endpoint="audit_event",
    methods=["DELETE", "GET", "POST"],
)
def audit_event(user_id, id):
    event = get_audit_event(id, user_id=user_id)

    return render_template(
        "admin/auth/audit-event.html", event=event, user=event.record
    )


@users.route(
    "/<user_id>/audit-events",
    endpoint="audit_events",
    methods=["DELETE", "GET", "POST"],
)
def audit_events(user_id):
    user = get_user(user_id)
    events = get_audit_events(user_id=user_id)

    q = request.args.get("q")
    if q:
        events = events.filter(
            AuditEvent.message.ilike(f"%{q}%")
            | AuditEvent.request_id.cast(sa.String).istartswith(q)
            | AuditEvent.user_id.cast(sa.String).istartswith(q)
            | (AuditEvent.category.ilike(q))
            | (AuditEvent.event.ilike(q))
            | (sa.func.host(AuditEvent.remote_addr) == q)
        )

    events = apply_paged_pagination(events)

    return render_template("admin/auth/audit-events.html", events=events, user=user)


@users.route("/new", endpoint="create", methods=["GET", "POST"])
def create_user():
    form = UserForm()

    if form.validate_on_submit():
        user = User()
        form.populate_obj(user)

        db.session.add(user)
        db.session.commit()

        flash(_("User accounts created"), "success")

        return redirect(url_for(".read", id=user.id), 303)

    return render_template("admin/auth/user.html", form=form)


@users.route("", endpoint="delete", methods=["DELETE"])
@users.route("/<id>", endpoint="delete", methods=["DELETE"])
def delete_user(id=None):
    next = request.values.get("next")

    if id:
        user = get_user(id)

        if user == current_user:
            flash(_("You cannot delete the current user"), "danger")

            return redirect(url_for(".read", id=user.id), 303)
        else:
            db.session.delete(user)
            db.session.commit()

            flash(_("User account deleted"), "warning")
    else:
        ids = request.form.getlist("ids[]")

        if str(current_user.id) in ids:
            flash(_("You cannot delete the current user"), "danger")
        else:
            users = get_users()
            users = users.filter(User.id.in_(ids))
            users.delete()
            db.session.commit()

            flash(_("User account(s) deleted"), "warning")

    if next:
        return safe_redirect(next)
    else:
        return redirect(url_for(".list"), 303)


@users.route("/disable", endpoint="disable", methods=["POST"])
@users.route("/<id>/disable", endpoint="disable", methods=["POST"])
def disable_user(id=None):
    next = request.values.get("next")

    if id:
        user = get_user(id)
        if user == current_user:
            flash(_("You cannot disable the current user"), "danger")
        else:
            user.active = False

            db.session.commit()

            flash(_("User account disabled"), "warning")
    else:
        ids = request.form.getlist("ids[]")

        if str(current_user.id) in ids:
            flash(_("You cannot disable the current user"), "danger")
        else:
            users = get_users()
            users = users.filter(User.id.in_(ids))

            users.update({"active": False})

            db.session.commit()

            flash(_("User account(s) disabled"), "warning")

    if next:
        return safe_redirect(next)
    elif id:
        return redirect(url_for(".read", id=user.id), 303)
    else:
        return redirect(url_for(".list"), 303)


@users.route("/enable", endpoint="enable", methods=["POST"])
@users.route("/<id>/enable", endpoint="enable", methods=["POST"])
def enable_user(id=None):
    next = request.values.get("next")

    if id:
        user = get_user(id)

        user.active = True
    else:
        ids = request.form.getlist("ids[]")

        users = get_users()
        users = users.filter(User.id.in_(ids))

        users.update({"active": True})

    db.session.commit()

    flash(_("User account(s) enabled"), "success")

    if next:
        return safe_redirect(next)
    elif id:
        return redirect(url_for(".read", id=user.id), 303)
    else:
        return redirect(url_for(".list"), 303)


@users.route("", endpoint="list", methods=["GET"])
def list_users():
    users = get_users()

    if request.args.get("active"):
        users = users.filter(User.active.is_(False))
    else:
        users = users.filter(User.active.is_(True))

    q = request.args.get("q")
    if q:
        users = users.filter(
            sa.or_(
                User.name.ilike(f"%{q}%"),
                User.email.ilike(f"%{q}%"),
            )
        )

    users = apply_paged_pagination(users)

    return render_template("admin/auth/users.html", users=users)


@users.route("/<id>", endpoint="read", methods=["GET"])
def read_user(id):
    user = get_user(id)
    form = UserForm(obj=user)

    events = get_audit_events(user_id=user.id)
    events = apply_paged_pagination(events)

    return render_template("admin/auth/user.html", form=form, events=events, user=user)


@users.route("/<id>", endpoint="update", methods=["POST"])
def update_user(id=None):
    user = get_user(id)
    form = UserForm(obj=user)

    if form.validate_on_submit():
        form.populate_obj(user)

    db.session.commit()

    flash(_("User account updated"), "success")

    events = get_audit_events(user_id=user.id)
    events = apply_paged_pagination(events)

    return render_template("admin/auth/user.html", form=form, events=events, user=user)
