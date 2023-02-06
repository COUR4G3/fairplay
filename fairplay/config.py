"""Configure the application from configuration sources."""

import os
import typing as t

from flask import Flask


def configure_app(
    app: Flask, options: t.Optional[t.Mapping[str, t.Any]] = None
):
    if options:
        app.config.from_mapping(options)
    app.config.from_object("fairplay.default_settings")

    if app.config.from_pyfile("settings.py", silent=True):
        app.logger.info("Config loaded from settings.py")

    try:
        app.config.from_envvar("ONTHESCENE_SETTINGS")
    except (FileNotFoundError, IOError) as e:
        raise RuntimeWarning(f"ONTHESCENE_SETTINGS could not be loaded: {e}")
    except RuntimeError:
        pass
    else:
        app.logger.info(
            "Config loaded from ONTHESCENE_SETTINGS=%s",
            os.environ["ONTHESCENE_SETTINGS"],
        )

    app.config.from_prefixed_env("ONTHESCENE")
    if not app.secret_key:
        path = app.config.get("SECRET_KEY_PATH")
        if path:
            with open(path, "rb") as f:
                app.secret_key = f.read()

    if not app.secret_key:
        raise RuntimeError(
            "No secret key configured for the application server.\n\n"
            "A secret key is required for signing of session cookies, links, "
            "tokens and encryption/decryption of sensitive fields in the "
            "database. This key should remain safe and secret - if lost or "
            "changed all cookies, links and tokens will become invalid and "
            "all data contained in sensitive fields will be lost.\n\n"
            "Enter a SECRET_KEY or SECRET_KEY_PATH in your settings or "
            "environment."
        )
