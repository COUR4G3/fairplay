"""Command-line utilities for managing the application."""
import platform
import sys

import click

from dynaconf.cli import main as dynaconf
from flask import __version__ as flask_version
from flask.cli import FlaskGroup
from werkzeug import __version__ as werkzeug_version

from . import __version__
from .app import create_app


def get_version(ctx, param, value):  # pragma: nocover
    if not value or ctx.resilient_parsing:
        return

    click.echo(
        f"Fairplay {__version__}\n"
        f"{platform.python_implementation()} {platform.python_version()}\n"
        f"Flask {flask_version}\n"
        f"Werkzeug {werkzeug_version}",
        color=ctx.color,
    )

    ctx.exit()


@click.option(
    "--version",
    help="Show the app version.",
    expose_value=False,
    callback=get_version,
    is_flag=True,
    is_eager=True,
)
@click.group(cls=FlaskGroup, create_app=create_app, add_version_option=False)
def cli():
    """Manage the Fairplay server application."""


dynaconf.help = "Manage configuration."
cli.add_command(dynaconf, "config")


def main(as_module=False):  # pragma: nocover
    prog_name = as_module and "python -m fairplay" or sys.argv[0]
    cli.main(sys.argv[1:], prog_name=prog_name)


if __name__ == "__main__":
    main(as_module=True)
