import sqlalchemy as sa
import sqlalchemy.orm as orm
import sqlalchemy_utils

from flask import session
from werkzeug.local import LocalProxy

from ..auth import current_user
from ..db import BaseModel, BaseQuery, Coordinates, db
from ..i18n import _


def get_current_course():
    course = None
    course_id = session.get("course_id")

    if course_id:
        course = db.session.get(Course, course_id)

    if not course:
        course = Course.query.filter_by_current_user().first()
        if course:
            session["course_id"] = str(course.id)

    return course


current_course = LocalProxy(get_current_course)


class CourseQuery(BaseQuery):
    def filter_by_current_user(self):
        return self.filter_by_user(current_user)

    def filter_by_user(self, user):
        if not user.is_authenticated:
            return self.filter(None)

        return self


class Course(BaseModel):
    __tablename__ = "course"

    name = sa.Column(sa.String, nullable=False)
    description = sa.Column(sa.Text)

    pos = sa.Column(Coordinates)

    games = orm.relationship("Game", lazy="dynamic", back_populates="course")

    holes = orm.relationship("CourseHole", back_populates="course")
    players = orm.relationship("Player", lazy="dynamic", back_populates="course")

    @sqlalchemy_utils.aggregated(
        "holes", sa.Column(sa.Integer, default=0, server_default="0", nullable=False)
    )
    def hole_count(self):
        return sa.func.count(CourseHole.number)

    query_class = CourseQuery

    __table_args__ = (
        sa.Index(
            "ix_course_hole_count", hole_count.column, postgresql_where="hole_count > 0"
        ),
        sa.Index(
            "ix_course_name",
            name,
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )

    @property
    def photo_url(self):
        from flask import url_for

        anchor = self.name.lstrip()[0].lower()
        return url_for("static", filename="img/profile.svg", _anchor=anchor)


class CourseHole(BaseModel):
    __tablename__ = "course_hole"

    number = sa.Column(sa.Integer, nullable=False)
    name = sa.Column(sa.String)
    index = sa.Column(sa.Integer)
    par = sa.Column(sa.Integer)

    pos = sa.Column(Coordinates)

    course_id = sa.Column(
        sqlalchemy_utils.UUIDType(),
        sa.ForeignKey("course.id", ondelete="cascade"),
        nullable=False,
    )

    course = orm.relationship("Course", lazy="joined", back_populates="holes")
    features = orm.relationship("CourseFeature", back_populates="hole")
    games = orm.relationship("GameHole", lazy="dynamic", back_populates="hole")

    __table_args__ = (
        sa.CheckConstraint("number > 0", "ck_course_hole_positive"),
        sa.CheckConstraint(
            "index IS NULL OR index > 0", "ck_course_hole_index_positive"
        ),
        sa.CheckConstraint("par IS NULL or par > 0", "ck_course_hole_par_positive"),
        sa.Index("ix_course_hole_index", index, postgresql_where="index IS NOT NULL"),
        sa.Index("ix_course_hole_par", par, postgresql_where="par IS NOT NULL"),
        sa.UniqueConstraint(course_id, number, name="uq_course_hole_number"),
    )

    @property
    def display_name(self):
        if self.name:
            return f"{self.name} (Hole #{self.number})"
        else:
            return f"Hole #{self.number}"


class CourseFeature(BaseModel):
    __tablename__ = "course_feature"

    FEATURE_TYPE_CHOICES = [
        ("bunker", _("Bunker")),
        ("fairway", _("Fairway")),
        ("green", _("Green")),
        ("hole", _("Hole")),
        ("tee", _("Tee")),
        ("tree", _("Tree")),
        ("water", _("Water")),
    ]

    name = sa.Column(sa.String)
    description = sa.Column(sa.Text)

    type = sa.Column(sqlalchemy_utils.ChoiceType(FEATURE_TYPE_CHOICES), nullable=False)

    coords = sa.Column(Coordinates)
    r = sa.Column(sa.Float)

    hole_id = sa.Column(
        sqlalchemy_utils.UUIDType(),
        sa.ForeignKey("course_hole.id", ondelete="cascade"),
        nullable=False,
    )

    hole = orm.relationship("CourseHole", lazy="joined", back_populates="features")

    __table_args__ = (
        sa.Index("ix_course_feature_hole_id", hole_id),
        sa.Index("ix_course_feature_type", type),
    )

    @property
    def display_name(self):
        return self.name or self.type.label
