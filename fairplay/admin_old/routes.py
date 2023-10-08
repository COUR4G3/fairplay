import sqlalchemy as sa

from flask import Blueprint, abort, redirect, render_template, request, session, url_for

from ..auth import auth_required
from ..db import db
from ..i18n import set_locale, set_timezone as _set_timezone
from .utils.pagination import apply_paged_pagination


admin = Blueprint("admin", __name__, template_folder="templates", url_prefix="/admin")

auth_required(admin)


@admin.route("")
def index():
    return render_template("admin/base.html")


# @admin.route("/set-account", methods=["POST"])
# def set_account():
#     account_id = request.form["account_id"]

#     accounts = Account.query.filter_by_current_user()
#     account = accounts.filter(Account.id == account_id).first()

#     if not account:
#         abort(400)

#     session["account_id"] = account_id

#     return "", 204, {"HX-Refresh": "true"}


@admin.route("/audit/events/<id>", methods=["GET"])
def audit_event(id):
    from ..audit import AuditEvent

    event = db.first_or_404(AuditEvent.query.filter(AuditEvent.id == id))

    return render_template("admin/audit-event.html", event=event)


@admin.route("/audit/events", methods=["GET"])
def audit_events():
    from ..audit import AuditEvent

    events = AuditEvent.query.order_by(AuditEvent.date.desc())

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

    return render_template("admin/audit-events.html", events=events)


@admin.route("/set-language", methods=["POST"])
def set_language():
    lang = request.form["lang"]

    set_locale(lang)

    return "", 204, {"HX-Refresh": "true"}


@admin.route("/set-timezone", methods=["POST"])
def set_timezone():
    tz = request.form["tz"]

    _set_timezone(tz)

    return "", 204


@admin.errorhandler(403)
def forbidden(e):
    return render_template("admin/403.html", e=e), 403


@admin.errorhandler(404)
def not_found(e):
    return render_template("admin/404.html", e=e), 404
