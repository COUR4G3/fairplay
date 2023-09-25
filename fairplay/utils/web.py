import jinja2

from flask import Markup, get_flashed_messages
from pygments import highlight as _highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from slugify import slugify


def highlight(s, lexer=None):
    if not lexer:
        lexer = guess_lexer(s)
    elif isinstance(lexer, str):
        lexer = get_lexer_by_name(lexer)

    formatter = HtmlFormatter(cssclass="highlight p-4")

    return Markup(_highlight(s, lexer, formatter))


def init_web_utils(app):
    @jinja2.pass_context
    def get_all_messages(ctx):
        for category, message in get_flashed_messages(with_categories=True):
            yield category, message

        for form in (ctx.get("form"), *ctx.get("forms", {}).values()):
            if hasattr(form, "csrf_token"):
                for message in form.csrf_token.errors:
                    yield "danger", message

            if hasattr(form, "recaptcha"):
                for message in form.recaptcha.errors:
                    yield "danger", message

    app.add_template_global(get_all_messages, "get_all_messages")

    app.add_template_filter(highlight, "highlight")

    app.add_template_filter(slugify, "slugify")
