import sqlalchemy as sa

from flask import Blueprint, flash, render_template, request, session
from flask_wtf import FlaskForm
from flask_wtf.recaptcha import RecaptchaField
from wtforms import fields, validators
from wtforms.validators import DataRequired

from . import current_user, login_user, logout_user
from .models import User
from ..audit import audit
from ..db import db
from ..i18n import _, get_locale, get_timezone
from ..utils.datetime import aware_datetime
from ..utils.htmx import HTMX_TRUE, htmx_request
from ..utils.security import is_safe_url, safe_redirect


auth = Blueprint("auth", __name__, template_folder="templates", url_prefix="/auth")


@auth.after_request
def force_htmx_refresh(response):
    if htmx_request:
        response.headers["HX-Refresh"] = HTMX_TRUE
    return response


class ForgotPasswordForm(FlaskForm):
    email = fields.StringField("Email address", validators=(DataRequired(),))
    recaptcha = RecaptchaField()


@auth.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    return render_template("auth/forgot-password.html")


class LoginForm(FlaskForm):
    email = fields.StringField("Email address", validators=(DataRequired(),))
    password = fields.PasswordField("Password", validators=(DataRequired(),))
    recaptcha = RecaptchaField()


@auth.route("/login", methods=["GET", "POST"])
def login():
    next = request.values.get("next")

    if current_user.is_authenticated:
        return safe_redirect(next)

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(
            sa.or_(
                User.email == form.email.data,
                User.sanitized_email == form.email.data,
            )
        ).first()

        if user and user.check_password(form.password.data):
            if not login_user(user):
                return render_template("auth/banned.html", user=user)

            audit("security", "login", "User account logged in", record=user)

            user.last_login_date = aware_datetime()
            db.session.commit()

            return safe_redirect(next)
        elif not user:
            User.dummy_verify()

        flash(_("Incorrect email or password"), "danger")

    return render_template("auth/login.html", form=form)


@auth.route("/logout", methods=["GET", "POST"])
def logout():
    next = request.args.get("next")

    if request.method != "POST":
        do_logout = False

        if request.origin and is_safe_url(request.origin):
            do_logout = True
        elif request.referrer and is_safe_url(request.referrer):
            do_logout = True

        if not do_logout:
            return render_template("auth/logout.html")

    logout_user()

    lang = get_locale()
    tz = get_timezone()

    session.clear()
    session.update({"lang": str(lang), "tz": str(tz)})

    return safe_redirect(next)


class RefreshForm(FlaskForm):
    password = fields.PasswordField("Password", validators=(DataRequired(),))


@auth.route("/refresh", methods=["GET", "POST"])
def refresh():
    return render_template("auth/refresh.html")


class RegisterForm(FlaskForm):
    name_first = fields.StringField("First name", validators=(DataRequired(),))
    name_last = fields.StringField("Last name", validators=(DataRequired(),))
    email = fields.EmailField(
        "Email address", validators=(DataRequired(), validators.Email())
    )

    password = fields.PasswordField("Password", validators=(DataRequired(),))
    confirm_password = fields.PasswordField(
        "Confirm password", validators=(DataRequired(), validators.EqualTo("password"))
    )

    recaptcha = RecaptchaField()


@auth.route("/register", methods=["GET", "POST"])
def register():
    return render_template("auth/register.html")


class ResetPasswordForm(FlaskForm):
    password = fields.PasswordField("New password", validators=(DataRequired(),))
    confirm_password = fields.PasswordField(
        "Confirm password", validators=(DataRequired(), validators.EqualTo("password"))
    )


@auth.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    return render_template("auth/reset-password.html")
