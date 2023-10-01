import logging
import os

import geoip2.database
import geoip2.webservice

from flask import Flask, current_app, request
from geoip2.errors import AddressNotFoundError, GeoIP2Error

from ..cache import shared_cache, worker_cache
from ..i18n import _, get_locale

UNKNOWN_LOCATION = _("Unknown")

logger = logging.getLogger(__name__)


def init_geoip(app: Flask):
    app.config.setdefault("GEOIP_DATABASE", "/usr/share/GeoIP/GeoLite2-City.mmdb")

    app.add_template_global(get_country_code)


def _get_result_database(ip_address, database):
    with geoip2.database.Reader(database) as reader:
        try:
            result = reader.city(ip_address)
        except AddressNotFoundError:
            return
        except TypeError:
            try:
                result = reader.country(ip_address)
            except AddressNotFoundError:
                return

    return _parse_geoip2_result(result)


def _get_result_webservice(ip_address, options):
    account_id = options.get("account_id")
    license_key = options.get("license_key")
    host = options.get("host")
    use_geolite = options.get("use_geolite")

    kw = {}
    if host:
        kw["host"] = host
    elif use_geolite:
        kw["host"] = "geolite.info"

    with geoip2.webservice.Client(account_id, license_key, **kw) as client:
        try:
            result = client.city(ip_address)
        except AddressNotFoundError:
            return
        except GeoIP2Error as e:
            logger.exception("Error getting GeoIP for %s: %s", ip_address, e)
            return

    return _parse_geoip2_result(result)


def _parse_geoip2_result(result):
    locale = str(get_locale()) or "en"

    try:
        location = result.location
    except AttributeError:
        location = tz = None
    if location:
        tz = location.time_zone

    try:
        city = result.city
    except AttributeError:
        city = None
    if city:
        try:
            try:
                city_name = city.names[locale]
            except KeyError:
                city_name = city.names[locale.split("_")[0]]
        except KeyError:
            city_name = city.names["en"]

    try:
        state = result.subdivisions.most_specific
    except AttributeError:
        state = None
    if state:
        try:
            try:
                state_name = state.names[locale]
            except KeyError:
                state_name = state.names[locale.split("_")[0]]
        except KeyError:
            state_name = state.names["en"]

    try:
        country = result.country
    except AttributeError:
        country = None
    if country:
        try:
            try:
                country_name = country.names[locale]
            except KeyError:
                country_name = country.names[locale.split("_")[0]]
        except KeyError:
            country_name = country.names["en"]

    return {
        "city": city and city_name,
        "country": country and (country.iso_code, country_name),
        "state": state and (state.iso_code, state_name),
        "tz": tz,
    }


def get_result(ip_address=None):
    if not ip_address:
        ip_address = request.remote_addr

    cache_key = f"geoip.result:{ip_address}"

    result = worker_cache.get(cache_key)
    if result:
        return result

    result = shared_cache.get(cache_key)
    if result:
        return result

    webservice_options = current_app.config.get_namespace("GEOIP_WEBSERVICE_")

    account_id = webservice_options.get("account_id")
    license_key = webservice_options.get("license_key")

    if account_id and license_key:
        result = _get_result_webservice(ip_address, webservice_options)

    if not result:
        database = current_app.config.get(
            "GEOIP_DATABASE",
            os.environ.get("GEOIP_DATABASE"),
        )

        if database:
            result = _get_result_database(ip_address, database)

    ttl = current_app.config.get("GEOIP_CACHE_SECONDS", 86400)

    if result and account_id and license_key:
        shared_cache.set(cache_key, result, ttl)
    if result:
        worker_cache.set(cache_key, result, ttl)

    return result


def get_city(ip_address=None):
    result = get_result(ip_address)
    if not result:
        return
    city = result["city"]
    return city


def get_country_code(ip_address=None, default=...):
    if default is ...:
        default = current_app.config.get("GEOIP_DEFAULT_COUNTRY")
    result = get_result(ip_address)
    if not result:
        return default
    country = result["country"]
    if country:
        return country[0]
    return default


def get_country_name(ip_address=None):
    result = get_result(ip_address)
    if not result:
        return
    country = result["country"]
    if country:
        return country[1]


def get_state_code(ip_address=None):
    result = get_result(ip_address)
    if not result:
        return
    state = result["state"]
    if state:
        return state[0]


def get_state_name(ip_address=None):
    result = get_result(ip_address)
    if not result:
        return
    state = result["state"]
    if state:
        return state[1]


def get_timezone(ip_address=None):
    result = get_result(ip_address)
    if not result:
        return
    return result["tz"]


def get_location(ip_address=None, default=UNKNOWN_LOCATION):
    result = get_result(ip_address)
    if not result:
        return default
    city = result.get("city")
    country = result.get("country")
    state = result.get("state")

    if city and state and country:
        location = f"{city}, {state[0]}, {country[1]}"
    elif city and country:
        location = f"{city}, {country[1]}"
    elif state and country:
        location = f"{state[1]}, {country[1]}"
    elif country:
        location = f"{country[1]}"
    else:
        location = default
    return location
