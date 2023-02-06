import sqlalchemy as sa
from geoalchemy2 import Geography
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from ..db import BaseModel
from ..db import BaseQuery


class HoleQuery(BaseQuery):
    pass


class Hole(BaseModel):
    __tablename__ = "hole"

    number = sa.Column(sa.Integer, nullable=False)

    course_id = sa.Column(
        UUIDType,
        sa.ForeignKey("course.id", ondelete="cascade"),
        nullable=False,
    )

    course = relationship("Course", back_populates="holes")
    tees = relationship("HoleTee", back_populates="hole")

    area = sa.Column(Geography("MULTIPOLYGON"))
    bunker = sa.Column(Geography("MULTIPOLYGON"))
    fairway = sa.Column(Geography("MULTIPOLYGON"))
    green = sa.Column(Geography("POLYGON"))
    hole = sa.Column(Geography("POINTZ"))
    water = sa.Column(Geography("MULTIPOLYGON"))

    query_class = HoleQuery

    __sql_constraints__ = (
        sa.CheckConstraint("number > 0", name="check_hole_number"),
        sa.UniqueConstraint(course_id, number, name="uniq_course_hole_number"),
    )


class HoleTee(BaseModel):
    __tablename__ = "hole_tee"

    point = sa.Column(Geography("POINTZ"))

    hole_id = sa.Column(
        UUIDType,
        sa.ForeignKey("hole.id", ondelete="cascade"),
        nullable=False,
    )

    hole = relationship("Hole", back_populates="tees")
