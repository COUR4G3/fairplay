from .routes import admin


def init_app(app):
    app.register_blueprint(admin)
