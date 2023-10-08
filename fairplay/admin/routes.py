from flask import Blueprint, render_template


admin = Blueprint("admin", __name__, template_folder="templates", url_prefix="/admin")


@admin.route("")
def index():
    return render_template("admin/index.html")
