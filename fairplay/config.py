import os

from logging.config import dictConfig as configure_logging

from dynaconf import FlaskDynaconf, Validator, ValidationError
from platformdirs import PlatformDirs


dirs = PlatformDirs("fairplay", "fair.play")


config = FlaskDynaconf(
    envvar_prefix="FAIRPLAY",
    settings_files=[
        "fairplay/default_settings.toml",
        "/etc/fairplay/settings.toml",
        str(dirs.site_config_path.joinpath("settings.toml")),
        str(dirs.user_config_path.joinpath("settings.toml")),
        ".fairplay.toml",
        "settings.toml",
        "fairplay.toml",
    ],
    environments=True,
    env_switcher="FAIRPLAY_ENV",
    validate_on_update=True,
)

validators = [
    Validator("DATABASE_URL", required=True),
    Validator("SECRET_KEY", required=True),
]


def configure_app(app, **options):
    config.init_app(app, **options)

    # load environment variable for various cloud-platforms
    if "DATABASE_URL" in os.environ:
        app.config.setdefault("DATABASE_URL", os.environ["DATABASE_URL"])
    if "REDIS_URL" in os.environ:
        app.config.setdefault("REDIS_URL", os.environ["REDIS_URL"])

    # validate configuration
    app.config.validators.register(*validators)

    try:
        app.config.validators.validate_all()
    except ValidationError as e:
        error_message = "Error(s) occured while reading configuration:\n"
        error_message += "\n".join(f" * {d}" for _, d in e.details)

        raise RuntimeError(error_message)

    # load logging configuration
    if "LOGGING" in app.config:
        configure_logging(app.config["LOGGING"])
