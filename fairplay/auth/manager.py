from flask_login import LoginManager

from .models import User


manager = LoginManager()


@manager.request_loader
def request_loader(request):
    remote_user = request.environ.get("REMOTE_USER")
    if remote_user:
        return User.query.filter(User.email == remote_user).first()


@manager.user_loader
def user_loader(user_id):
    return User.query.get(user_id)
