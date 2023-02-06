import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy_utils import aggregated
from sqlalchemy_utils import UUIDType

from ..db import BaseModel
from ..db import BaseQuery


class CourseQuery(BaseQuery):
    pass


class Course(BaseModel):
    __tablename__ = "course"

    name = sa.Column(sa.String, unique=True, nullable=False)

    games = relationship("Game", back_populates="course")
    holes = relationship("Hole", back_populates="course")

    query_class = CourseQuery

    __sql_constraints__ = (
        sa.Index(
            "ix_course_hole_count", "hole_count", postgresql_using="brin"
        ),
    )

    @aggregated("holes", sa.Column(sa.Integer))
    def hole_count(self):
        return sa.func.count("1")
