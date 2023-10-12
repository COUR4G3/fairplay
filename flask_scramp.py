import base64
import secrets

from functools import wraps

from flask import (
    abort,
    after_this_request,
    has_app_context,
    current_app,
    make_response,
    request,
    session,
)
from scramp import ScramException, ScramMechanism


DEFAULT_SCRAMP_MECHANISMS = ["SCRAM-SHA-256"]

mech = ScramMechanism("SCRAM-SHA-256")
auth_info = mech.make_auth_info("pass")


class Scramp:
    """Implements RFC7804 HTTP SCRAM authentication."""

    def __init__(self, app=None, **options):
        self.app = app
        self.options = options
        if app:
            self.init_app(app)

    def init_app(self, app, **options):
        options = {**self.options, **options}

        app.config.setdefault("SCRAMP_MECHANISMS", DEFAULT_SCRAMP_MECHANISMS)

        realm = options.get("realm")
        if realm:
            app.config.setdefault("SCRAMP_REALM", realm)

    def _get_app(self):
        if not has_app_context() and self.app:
            return self.app
        return current_app

    def _get_options(self):
        app = self._get_app()
        return app.config.get_namespace("SCRAMP_")

    def _get_user_key(self, user):
        return auth_info

    def _unauthorized(self):
        response = make_response("", 401)

        options = self._get_options()

        mechanisms = options["mechanisms"]
        realm = options.get("realm", request.host)

        sid = session.get("flask_scramp.sid")
        s_nonce = session.get("flask_scramp.s_nonce")

        for mechanism in mechanisms:
            auth_header = f'{mechanism} realm="{realm}"'
            if sid and s_nonce:
                auth_header = f", sid={sid}, s={s_nonce}"

            response.headers.add("WWW-Authenticate", auth_header)

        abort(response)

    def authenticate(self):
        if not request.authorization:
            self._unauthorized()

        type = request.authorization.type.upper()
        if not type or not type.startswith("SCRAM-"):
            self._unauthorized()

        sid = request.authorization.parameters.get("sid")
        if sid and sid != session.get("flask_scramp.sid"):
            self._unauthorized()

        s_nonce = session.get("flask_scramp.s_nonce", None)
        if not s_nonce:
            session["flask_scramp.s_nonce"] = s_nonce = secrets.token_hex(16)

        mechanism = ScramMechanism(type)
        server = mechanism.make_server(self._get_user_key, s_nonce=s_nonce)

        data = request.authorization.parameters.get("data")
        if not data:
            self._unauthorized()

        decoded_data = base64.b64decode(data).decode("utf-8")

        try:
            if sid:
                server.set_client_first(session.pop("flask_scramp.cfirst", ""))
                server.get_server_first()
                server.set_client_final(decoded_data)
                returned_data = server.get_server_final()
                encoded_data = base64.b64encode(returned_data.encode("utf-8")).decode(
                    "utf-8"
                )

                @after_this_request
                def set_authentication_info_header(response):
                    auth_header = f"sid={sid}, data={encoded_data}"
                    response.headers["Authentication-Info"] = auth_header
                    return response

                return server.user
            else:
                server.set_client_first(decoded_data)
                session["flask_scramp.cfirst"] = decoded_data
                session["flask_scramp.s_nonce"] = s_nonce
                returned_data = server.get_server_first()
                session["flask_scramp.sid"] = sid = secrets.token_hex(16)
        except ScramException:
            if server.stage and server.stage >= 3:
                returned_data = server.get_server_final()
            else:
                returned_data = server.get_server_first()

        encoded_data = base64.b64encode(returned_data.encode("utf-8")).decode("utf-8")

        response = make_response("", 401)
        response.headers["WWW-Authenticate"] = f"{type} sid={sid}, data={encoded_data}"

        abort(response)

    def login_required(self, f=None):
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                self.authenticate()

                return f(*args, **kwargs)

            return wrapper

        return f and decorator(f) or decorator
