from flask import Flask
from sqlalchemy.orm import configure_mappers

from . import auth
from .cache import init_cache
from .config import configure_app
from .db import init_db
from .i18n import init_i18n
from .utils.htmx import init_htmx
from .utils.security import init_captcha, init_csrf
from .utils.web import init_web_utils


def create_app(**options):
    app = Flask("fairplay")

    configure_app(app, **options)

    init_cache(app)
    init_db(app)
    init_i18n(app)

    init_captcha(app)
    init_csrf(app)
    init_htmx(app)
    init_web_utils(app)

    auth.init_app(app)

    app.config.load_extensions()

    configure_mappers()

    return app
