from flask import Blueprint, render_template

from ..auth import auth_required
from ..courses.models import Course


games = Blueprint("games", __name__, template_folder="templates")


def init_app(app):
    app.register_blueprint(games)


@games.route("/")
@auth_required
def map():
    course = Course.query.first()

    return render_template("web/games/map.html", course=course)
