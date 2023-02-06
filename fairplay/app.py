"""Application factory to configure the application."""
from flask import Flask

from . import __version__
from .api import api
from .auth import init_auth
from .config import configure_app
from .db import init_db


def create_app(**options):
    app = Flask(__name__)
    app.logger.info(f"FairPlay, {__version__}")

    configure_app(app, options)

    init_auth(app)
    init_db(app)

    app.register_blueprint(api)

    return app
