from flask import current_app
from passlib.context import CryptContext


def get_passlib_context():
    options = current_app.config.get_namespace("PASSLIB_")
    schemes = options.pop("schemes", ["pbkdf2_sha256", "plaintext"])
    options.setdefault("deprecated", ["auto"])

    return CryptContext(schemes, **options)
