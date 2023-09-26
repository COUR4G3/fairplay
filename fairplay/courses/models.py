import sqlalchemy as sa
import sqlalchemy.orm as orm
import sqlalchemy_utils

from sqlalchemy.orm.collections import attribute_mapped_collection

from ..db import BaseModel, db


class Course(BaseModel):
    __tablename__ = "course"

    name = sa.Column(sa.String, nullable=False)

    games = orm.relationship("Game", lazy="dynamic", back_populates="course")

    holes = orm.relationship(
        "CourseHole",
        collection_class=attribute_mapped_collection("number"),
        back_populates="course",
    )

    @sqlalchemy_utils.aggregated(
        "holes", sa.Column(sa.Integer, default=0, server_default="0", nullable=False)
    )
    def hole_count(self):
        return sa.func.count(CourseHole.number)

    __table_args__ = (
        sa.Index("ix_course_hole_count", hole_count, postgresql_where="hole_count > 0"),
        sa.Index(
            "ix_course_name",
            name,
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )


class CourseHole(BaseModel):
    __tablename__ = "course_hole"

    number = sa.Column(sa.Integer, nullable=False)
    index = sa.Column(sa.Integer)
    par = sa.Column(sa.Integer)

    course_id = sa.Column(
        sqlalchemy_utils.UUIDType(),
        sa.ForeignKey("course.id", ondelete="cascade"),
        nullable=False,
    )

    course = orm.relationship("Course", lazy="joined", back_populates="holes")
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
