import sqlalchemy as sa
from flask import abort
from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request
from flask_cors import cross_origin
from marshmallow import fields
from marshmallow import validate
from marshmallow_sqlalchemy import auto_field
from marshmallow_sqlalchemy import SQLAlchemySchema
from webargs.flaskparser import parser

from ..auth import confirm_login
from ..auth import current_user
from ..auth import login_fresh
from ..auth import login_required
from ..auth import logout_user
from ..auth import User
from ..db import db
from ..i18n import _
from ..utils.security import verify_captcha_response
from .utils import prepare_schema


user = Blueprint("user", __name__, url_prefix="/user")


class UserSchema(SQLAlchemySchema):
    class Meta:
        load_instance = True
        model = User
        session = db.session

    id = auto_field(dump_only=True)
    name = auto_field()
    email = auto_field()
    password = fields.String(load_only=True)
    active = auto_field()
    fresh = fields.Method("check_login_fresh")
    last_login = auto_field()
    created_at = auto_field()
    updated_at = auto_field()

    def check_login_fresh(self, obj):
        return login_fresh()


@user.route("/login", methods=["POST"])
def login():
    data = parser.parse(
        {
            "login": fields.String(required=True),
            "password": fields.String(required=True),
            "remember": fields.Boolean(),
            "captcha_response": fields.String(),
        },
        location="json_or_form",
        error_status_code=400,
    )

    if not verify_captcha_response(data["captcha_response"]):
        return {
            "code": 400,
            "description": "CAPTCHA verification failed",
            "name": "captcha_verify_failed",
        }, 400

    user = User.login(data["login"], data["password"], data["remember"])
    if not user:
        abort(401)

    db.session.commit()

    schema = UserSchema()
    return jsonify(schema.dump(user))


@user.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return "", 204


@user.route("", methods=["GET"])
@cross_origin()
@login_required
def read():
    schema = prepare_schema(UserSchema)
    return jsonify(schema.dump(current_user))


@user.route("/refresh", methods=["POST"])
@login_required
def refresh():
    data = parser.parse(
        {"password": fields.String(required=True)},
        location="json_or_form",
    )

    if not current_user.check_password(data["password"]):
        abort(401)

    confirm_login()

    return "", 204


@user.route("", methods=["POST"])
@cross_origin()
@login_required
def update():
    schema = prepare_schema(UserSchema)

    password_min_length = current_app.config["PASSWORD_MIN_LENGTH"]
    schema.password.validators.append(
        validate.Length(
            min=password_min_length,
            error=_(
                "Password should be atleast {min} alphanumeric characters."
            ),
        )
    )

    schema.load(
        request.json or request.form, instance=current_user, partial=True
    )
    db.session.commit()

    return jsonify(schema.dump(current_user))
