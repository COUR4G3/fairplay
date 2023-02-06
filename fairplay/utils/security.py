from importlib import import_module

import requests

from flask import current_app
from flask import Flask
from flask import request
from flask_wtf.csrf import CSRF
from passlib.context import CryptContext
from requests_toolbelt.utils.user_agent import user_agent

from .. import __version__


csrf = CSRF()


def get_password_crypt_context():
    options = current_app.options.get_namespace("PASSLIB_")
    options.setdefault("schemes", ["scrypt", "pbkdf2_hmac", "none"])
    options.setdefault("deprecated", "auto")

    return CryptContext(**options)


def init_csrf(app: Flask):
    csrf.init_app(app)


def verify_captcha_response(response):
    if current_app.testing:
        return True

    options = current_app.config.get_namespace("CAPTCHA_")
    enabled = options["enabled"]
    verify_function = options["verify_function"]

    if enabled:
        if callable(verify_function):
            function = verify_function
        elif "." in verify_function:
            module_name, function_name = verify_function.rsplit(".", 1)
            module = import_module(module_name, __package__)
            function = getattr(module, function_name)
        else:
            function = globals()[verify_function]

        return function(response)

    return True


def verify_hcaptcha_response(response):
    options = current_app.config.get_namespace("HCAPTCHA_")
    allowed_hosts = options.get("allowed_hosts", request.trusted_hosts)
    secret = options.get("secret")
    sitekey = options.get("sitekey")

    data = {
        "remoteip": request.remote_addr,
        "response": response,
        "secret": secret,
        "sitekey": sitekey,
    }

    headers = {
        "User-Agent": user_agent(
            "fairplay",
            __version__,
            extra=(("requests", requests.__version__),),
        )
    }

    try:
        resp = requests.post(
            "https://hcaptcha.com/siteverify", data=data, headers=headers
        )
        resp.raise_for_status()
    except requests.RequestException:
        return

    response_data = resp.json()

    if response_data["hostname"] not in allowed_hosts:
        return False

    error_codes = response_data.get("error-codes")
    if error_codes:
        pass

    return response_data["success"]
