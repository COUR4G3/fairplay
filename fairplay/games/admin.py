import uuid

import sqlalchemy as sa

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_wtf import FlaskForm
from wtforms import ValidationError, fields, validators
from wtforms.validators import DataRequired

from ..admin import admin
from ..admin.utils.pagination import apply_paged_pagination
from ..courses.models import Course
from ..db import db
from ..i18n import _
from ..utils.security import safe_redirect
from .models import Game


games = Blueprint("games", __name__, template_folder="templates", url_prefix="/games")


def init_app(app):
    admin.register_blueprint(games)


def get_game(id):
    try:
        id = uuid.UUID(id)
    except ValueError:
        abort(404)

    games = get_games()
    return db.one_or_404(games.filter(Game.id == id))


def get_games():
    return Game.query.filter_by_current_user()


def iter_courses():
    return [(c.id, c.name) for c in Course.query.filter_by_current_user()]


class GameForm(FlaskForm):
    course_id = fields.SelectField(
        "Course", validators=(DataRequired(),), choices=iter_courses
    )


@games.route("", endpoint="create", methods=["POST"])
@games.route("/new", endpoint="create", methods=["GET", "POST"])
def create():
    form = GameForm()

    if form.validate_on_submit():
        game = Game()
        form.populate_obj(game)

        db.session.add(game)
        db.session.commit()

        flash(_("Game created"), "success")

        return redirect(url_for(".read", id=game.id), 303)

    return render_template("admin/games/game.html", form=form)


@games.route("", endpoint="delete", methods=["DELETE"])
@games.route("/<id>", endpoint="delete", methods=["DELETE"])
def delete(id=None):
    next = request.values.get("next")

    if id:
        game = get_game(id)

        db.session.delete(game)
    else:
        ids = request.form.getlist("ids[]")

        games = get_games()
        games = games.filter(Game.id.in_(ids))
        games.delete()

    db.session.commit()

    flash(_("Game(s) deleted"), "warning")

    if next:
        return safe_redirect(next)

    return redirect(url_for(".list"), 303)


@games.route("", endpoint="list", methods=["GET"])
def list():
    games = get_games()

    q = request.args.get("q")
    if q:
        games = games.filter(
            sa.or_(
                Game.name.ilike(f"%{q}%"),
            )
        )

    games = apply_paged_pagination(games)

    return render_template("admin/games/games.html", games=games)


@games.route("/<id>", endpoint="update", methods=["POST"])
@games.route("/<id>", endpoint="read", methods=["GET"])
def read(id):
    game = get_game(id)

    form = GameForm(obj=game, exclude=("course_id",))

    if form.validate_on_submit():
        form.populate_obj(game)

        db.session.commit()

        flash(_("Game updated"), "success")

    return render_template("admin/games/game.html", game=game, form=form)


update = read
