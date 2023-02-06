"""Command-line utilities for managing the application."""

import platform
import sys

import click
from flask import __version__ as flask_version
from flask.cli import FlaskGroup
from werkzeug import __version__ as werkzeug_version

from .. import __version__
from ..app import create_app


def get_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    click.echo(
        f"""FairPlay, {__version__}
Python, {platform.python_version()}
Flask, {flask_version}
Werkzeug, {werkzeug_version}""",
        color=ctx.color,
    )

    ctx.exit()


@click.group(cls=FlaskGroup, create_app=create_app, add_version_option=False)
@click.option(
    "--version",
    is_flag=True,
    help="Show the application version.",
    callback=get_version,
    is_eager=True,
    expose_value=False,
)
def cli():
    """Manage the FairPlay server application."""


def main(as_module=False):
    prog_name = as_module and "python -m fairplay" or sys.argv[0]
    cli.main(sys.argv[1:], prog_name=prog_name)


if __name__ == "__main__":
    main(as_module=True)
