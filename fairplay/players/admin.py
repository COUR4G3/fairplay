import uuid

import sqlalchemy as sa

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_wtf import FlaskForm
from wtforms import fields, validators
from wtforms.validators import DataRequired

from ..admin import admin
from ..admin.utils.pagination import apply_paged_pagination
from ..db import db
from ..i18n import _
from ..utils.security import safe_redirect
from .models import Player


players = Blueprint(
    "players", __name__, template_folder="templates", url_prefix="/players"
)


def init_app(app):
    admin.register_blueprint(players)


def get_player(id):
    try:
        id = uuid.UUID(id)
    except ValueError:
        abort(404)

    players = get_players()
    return db.one_or_404(players.filter(Player.id == id))


def get_players():
    return Player.query


class PlayerForm(FlaskForm):
    name = fields.StringField("Name", validators=(DataRequired(),))
    handicap = fields.IntegerField(
        "Handicap", validators=(validators.NumberRange(min=0, max=54),)
    )


@players.route("", endpoint="create", methods=["POST"])
@players.route("/new", endpoint="create", methods=["GET", "POST"])
def create():
    form = PlayerForm()

    if form.validate_on_submit():
        player = Player()
        form.populate_obj(player)

        db.session.add(player)
        db.session.commit()

        flash(_("Player created"), "success")

        return redirect(url_for(".read", id=player.id), 303)

    return render_template("admin/players/player.html", form=form)


@players.route("", endpoint="delete", methods=["DELETE"])
@players.route("/<id>", endpoint="delete", methods=["DELETE"])
def delete(id=None):
    next = request.values.get("next")

    if id:
        player = get_player(id)

        db.session.delete(player)
    else:
        ids = request.form.getlist("ids[]")

        players = get_players()
        players = players.filter(Player.id.in_(ids))
        players.delete()

    db.session.commit()

    flash(_("Player(s) deleted"), "warning")

    if next:
        return safe_redirect(next)

    return redirect(url_for(".list"), 303)


@players.route("", endpoint="list", methods=["GET"])
def list():
    players = get_players()

    q = request.args.get("q")
    if q:
        players = players.filter(
            sa.or_(
                Player.name.ilike(f"%{q}%"),
            )
        )

    players = apply_paged_pagination(players)

    return render_template("admin/players/players.html", players=players)


@players.route("/<id>", endpoint="update", methods=["POST"])
@players.route("/<id>", endpoint="read", methods=["GET"])
def read(id):
    player = get_player(id)

    form = PlayerForm(obj=player)

    if form.validate_on_submit():
        form.populate_obj(player)

        db.session.commit()

        flash(_("Player updated"), "success")

    return render_template("admin/players/player.html", player=player, form=form)


update = read
