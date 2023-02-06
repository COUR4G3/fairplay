import click
from flask.cli import AppGroup

from ..auth.models import User
from ..db import db


@click.group(cls=AppGroup)
def users():
    """Manage users and authentication."""


@users.command()
@click.argument("email")
@click.option("-n", "--name")
@click.password_option()
def create(email, name, password):
    """Create a new user."""
    user = User(
        email=email,
        name=name or email,
        password=password,
    )

    db.session.add(user)
    db.session.commit()

    click.echo("User created!")
    click.echo(f"ID: {user.id}")
    click.echo(f"Name: {user.name}")
    click.echo(f"Email address: {user.email}")
