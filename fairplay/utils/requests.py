from urllib.parse import urlparse, urlunparse

import requests

from requests.adapters import HTTPAdapter

from .. import __version__

USER_AGENT = f"fairplay/{__version__} requests/{requests.__version__}"


session = requests.Session()

session.headers["User-Agent"] = USER_AGENT


def generate_bearer_url(token, url):
    parsed_url = urlparse(url)
    parsed_url._replace(username=token)
    parsed_url._replace(scheme="bearer://")
    return urlunparse(parsed_url)


class BearerAdapter(HTTPAdapter):
    """HTTP adapter that supports Bearer URLs."""

    def request_url(self, request, proxies):
        """Handle Bearer URLs and some proxy stuff."""
        parsed_url = urlparse(request.url)
        scheme = parsed_url.scheme
        if scheme != "bearer":
            return super().request_url(request, proxies)

        parsed_url._replace(username=None)

        url = parsed_url.path

        return url

    def add_headers(self, request, **kwargs):
        """Add the token for the Bearer URL."""
        parsed_url = urlparse(request.url)
        scheme = parsed_url.scheme
        if scheme != "bearer":
            super().add_headers(request, **kwargs)

        token = parsed_url.username

        request.headers["Authorization"] = f"Bearer {token}"


session.mount("bearer://", BearerAdapter())
