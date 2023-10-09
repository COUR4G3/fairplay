from flask_assets import Environment


assets = Environment()


def init_assets(app):
    assets.from_yaml("fairplay/assets.yml")

    assets.init_app(app)
