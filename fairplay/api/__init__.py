from flask import Blueprint


api = Blueprint("api", __name__, url_prefix="/api")


def init_app(app):
    app.register_blueprint(api)
