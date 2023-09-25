"""An AI product and marketing enrichment service."""
from importlib.metadata import PackageNotFoundError, version

try:
    from ._version import version as __version__
except ImportError:  # pragma: nocover
    try:
        __version__ = version("catalyst")
    except PackageNotFoundError:
        __version__ = "0.1-dev0"

from .app import create_app

__all__ = ["create_app"]
