import datetime as dt

import flag
import pytz

from faker import Faker
from flask import request, session
from flask_babel import (
    Babel,
    force_locale,
    get_locale,
    get_timezone,
    gettext,
    lazy_gettext,
    lazy_ngettext,
    lazy_npgettext,
    lazy_pgettext,
    ngettext,
    npgettext,
    pgettext,
    refresh as refresh_locale,
)
from lazy_string import LazyString
from werkzeug.local import LocalProxy

from .auth import current_user
from .cache import cache


__all__ = [
    "_",
    "force_locale",
    "get_locale",
    "get_timezone",
    "gettext",
    "lazy_gettext",
    "lazy_ngettext",
    "lazy_npgettext",
    "lazy_pgettext",
    "ngettext",
    "npgettext",
    "pgettext",
    "refresh_locale",
    "set_locale",
    "set_timezone",
]


babel = Babel()


def init_i18n(app):
    babel.init_app(
        app,
        default_translation_directories="fairplay/translations",
        locale_selector=locale_selector,
        timezone_selector=timezone_selector,
    )

    app.add_template_global(get_locale)
    app.add_template_global(get_timezone)
    app.add_template_global(iter_locales)
    app.add_template_global(iter_timezones)
    app.add_template_filter(locale_to_flag)
    app.add_template_filter(flag.flag, "flag")
    app.add_template_filter(flag.flagize, "flagize")


def iter_locales(current_locale=None, flagize=False):
    if not current_locale:
        current_locale = get_locale()

    for locale in sorted(
        babel.list_translations(),
        key=lambda l: l.get_language_name(str(current_locale)),
    ):
        value = str(locale)

        if value in ("uk_UA",):
            label = f"{locale.get_language_name(str(current_locale))}"
        elif value in ("en_GB", "en_US"):
            label = f"{locale.get_display_name(str(current_locale))}"
        else:
            label = f"{locale.get_display_name(str(current_locale))}"

        if current_locale.language != locale.language:
            if value in ("en_GB", "en_US"):
                label += f" / {locale.get_language_name()}"
                acronym = [t[0] for t in locale.get_territory_name().split()]
                label += f" ({''.join(acronym)})"
            else:
                label += f" / {locale.get_language_name()}"

        if flagize:
            label = f"{locale_to_flag(locale)} {label}"

        yield (value, label)


def iter_timezones():
    now = dt.datetime.now()

    yield ("UTC", "UTC")

    for tzname in sorted(pytz.common_timezones):
        if tzname == "UTC":
            continue

        tz = pytz.timezone(tzname)
        label = tz.zone.replace("_", " ")

        offset = tz.utcoffset(now)

        offset_hours = offset.total_seconds() / 3600
        offset_mins = offset.total_seconds() / 60 % 60

        if offset_hours or offset_mins:
            label = f"{label} ({offset_hours:+0{2}.{0}f}:{offset_mins:0{2}.{0}f})"
        elif tzname not in ("GMT", "UTC"):
            label = f"{label} (UTC)"

        yield (tzname, label)


def locale_to_flag(locale):
    """Convert a locale to a approximate representative country flag."""
    s = str(locale)

    if s == "ar":
        s = "SA"
    elif s == "hi":
        s = "IN"
    elif s == "zh_Hans":
        s = "CN"
    elif s == "zh_Hant":
        s = "TW"

    s = s.split("_", 1)[-1]
    return flag.flag(s)


def locale_selector():
    if not request:
        return

    # try get locale from current session
    locale = session.get("locale")

    # next, try get locale from the current user account
    if not locale and current_user.is_authenticated:
        locale = current_user.lang

    # lastly, try get the locale from the browser
    if not locale:
        locales = [str(locale) for locale in babel.list_translations()]
        locale = request.accept_languages.best_match(locales)

    return locale


def timezone_selector():
    if not request:
        return

    # try get timezone from current session
    tz = session.get("timezone")

    # next, try get the current user's timezone
    if not tz and current_user.is_authenticated:
        tz = current_user.tz

    return tz


def set_locale(locale):
    session["locale"] = locale

    if current_user.is_authenticated:
        current_user.locale = locale


def set_timezone(tz):
    session["timezone"] = tz

    if current_user.is_authenticated:
        current_user.tz = tz


_ = gettext


def get_faker():
    return Faker(str(get_locale()))


faker = LocalProxy(get_faker)


class Fake:
    def __getattr__(self, name):
        return LazyString(lambda: getattr(faker, name)())


fake = Fake()
