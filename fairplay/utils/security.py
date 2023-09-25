from flask import current_app, g, redirect, request
from flask_wtf.csrf import (
    CSRFError,
    CSRFProtect,
    ValidationError,
    generate_csrf,
    validate_csrf,
)
from is_safe_url import is_safe_url as _is_safe_url

DEFAULT_CF_TURNSTILE_SCRIPT = "https://challenges.cloudflare.com/turnstile/v0/api.js"
DEFAULT_CF_TURNSTILE_VERIFY_SERVER = (
    "https://challenges.cloudflare.com/turnstile/v0/siteverify"
)

DEFAULT_HCAPTCHA_SCRIPT = "https://js.hcaptcha.com/1/api.js"
DEFAULT_HCAPTCHA_VERIFY_SERVER = "https://api.hcaptcha.com/siteverify"


__all__ = [
    "csrf",
    "generate_csrf",
    "validate_csrf",
]


def init_captcha(app):
    captcha_type = app.config.get("CAPTCHA_TYPE", "recaptcha")
    if captcha_type == "cf_turnstile":
        _init_captcha_cf_turnstile(app)
    elif captcha_type == "hcaptcha":
        _init_captcha_hcaptcha(app)
    elif captcha_type != "recaptcha":
        raise RuntimeError(f"Unknown CAPTCHA_TYPE: {captcha_type}")


def _init_captcha_cf_turnstile(app):
    private_key = app.config.get("CF_TURNSTILE_PRIVATE_KEY")
    public_key = app.config.get("CF_TURNSTILE_PUBLIC_KEY")

    data_attrs = {
        "response-field-name": "g-recaptcha-response",
    }

    additional_data_attrs = app.config.get("CF_TURNSTILE_DATA_ATTRS")
    if additional_data_attrs:
        data_attrs.update(additional_data_attrs)

    div_class = app.config.get("CF_TURNSTILE_DIV_CLASS", "cf-turnstile")
    script = app.config.get("CF_TURNSTILE_SCRIPT", DEFAULT_CF_TURNSTILE_SCRIPT)
    verify_server = app.config.get(
        "CF_TURNSTILE_VERIFY_SERVER",
        DEFAULT_CF_TURNSTILE_VERIFY_SERVER,
    )

    app.config.setdefault("RECAPTCHA_PRIVATE_KEY", private_key)
    app.config.setdefault("RECAPTCHA_PUBLIC_KEY", public_key)

    app.config.setdefault("RECAPTCHA_DATA_ATTRS", data_attrs)
    app.config.setdefault("RECAPTCHA_DIV_CLASS", div_class)
    app.config.setdefault("RECAPTCHA_SCRIPT", script)
    app.config.setdefault("RECAPTCHA_VERIFY_SERVER", verify_server)


def _init_captcha_hcaptcha(app):
    private_key = app.config.get("HCAPTCHA_PRIVATE_KEY")
    public_key = app.config.get("HCAPTCHA_PUBLIC_KEY")

    data_attrs = app.config.get("HCAPTCHA_DATA_ATTRS")
    div_class = app.config.get("HCAPTCHA_DIV_CLASS", "h-captcha")
    script = app.config.get("HCAPTCHA_SCRIPT", DEFAULT_HCAPTCHA_SCRIPT)
    verify_server = app.config.get(
        "HCAPTCHA_VERIFY_SERVER",
        DEFAULT_HCAPTCHA_VERIFY_SERVER,
    )

    app.config.setdefault("RECAPTCHA_PRIVATE_KEY", private_key)
    app.config.setdefault("RECAPTCHA_PUBLIC_KEY", public_key)

    app.config.setdefault("RECAPTCHA_DATA_ATTRS", data_attrs)
    app.config.setdefault("RECAPTCHA_DIV_CLASS", div_class)
    app.config.setdefault("RECAPTCHA_SCRIPT", script)
    app.config.setdefault("RECAPTCHA_VERIFY_SERVER", verify_server)

    @app.before_request
    def hcaptcha_response_hook():
        if "h-captcha-response" in request.form:
            request.form["g-recaptcha-response"] = request.form["h-captcha-response"]


csrf = CSRFProtect()


def init_csrf(app):
    app.config.setdefault("WTF_CSRF_CHECK_DEFAULT", False)

    csrf.init_app(app)

    app.before_request(check_request_csrf)


def check_request_csrf():
    if not current_app.config["WTF_CSRF_ENABLED"]:
        return
    if request.authorization is not None:
        return
    if request.blueprint in csrf._exempt_blueprints:
        return

    view = current_app.view_functions.get(request.endpoint)
    if view:
        dest = f"{view.__module__}.{view.__name__}"
        if dest in csrf._exempt_views:
            return

    if request.method not in current_app.config["WTF_CSRF_METHODS"]:
        if not request.url_rule or not request.url_rule.websocket:
            return

    # do origin and referrer check if browser sends headers
    if request.origin and not is_safe_url(request.origin):
        raise CSRFError("Invalid origin")

    if request.referrer and not is_safe_url(request.referrer):
        raise CSRFError("Invalid referrer")

    # get the token from form or header (or query if websocket)
    token = csrf._get_csrf_token()
    if request.url_rule and request.url_rule.websocket:
        token = request.args.get("token")

    try:
        validate_csrf(token)
    except ValidationError as e:
        raise CSRFError(e.args[0])

    g.csrf_valid = True


def is_safe_url(location: str):
    trusted_hosts = request.trusted_hosts or [request.host]
    require_https = request.is_secure
    return _is_safe_url(location, trusted_hosts, require_https)


def safe_redirect(location: str, default: str = "/"):
    if location and is_safe_url(location):
        return redirect(location, 303)
    return redirect(default, 303)
