"""Golf course play management system."""
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version

try:
    from ._version import version as __version__
except ImportError:
    try:
        __version__ = version("fairplay")
    except PackageNotFoundError:
        __version__ = "0.1-dev0"

from .app import create_app


__all__ = ["create_app"]
