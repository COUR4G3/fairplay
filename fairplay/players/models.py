import sqlalchemy as sa
import sqlalchemy.orm as orm
import sqlalchemy_utils

from ..courses.models import current_course
from ..db import BaseModel, BaseQuery


class PlayerQuery(BaseQuery):
    def filter_by_current_course(self):
        return self.filter_by_course(current_course)

    def filter_by_course(self, course):
        if not course:
            return self.filter(None)

        return self.filter(Player.course == course)


class Player(BaseModel):
    __tablename__ = "player"

    name = sa.Column(sa.String, nullable=False)
    handicap = sa.Column(sa.Integer)

    course_id = sa.Column(
        sqlalchemy_utils.UUIDType(),
        sa.ForeignKey("course.id", ondelete="cascade"),
        nullable=False,
    )
    player_id = sa.Column(
        sqlalchemy_utils.UUIDType(),
        sa.ForeignKey("player.id", ondelete="set null"),
    )

    course = orm.relationship("Course", lazy="joined", back_populates="players")
    games = orm.relationship(
        "Game", secondary="game_player", lazy="dynamic", viewonly=True
    )
    player = orm.relationship("Player", lazy="joined")

    query_class = PlayerQuery

    __table_args__ = (
        sa.CheckConstraint(
            "handicap IS NULL OR handicap > 0", "ck_player_handicap_positive"
        ),
        sa.Index(
            "ix_player_handicap",
            handicap,
            postgresql_where="handicap IS NOT NULL",
        ),
        sa.Index(
            "ix_player_name",
            name,
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
        sa.UniqueConstraint(course_id, player_id, name="uq_player_id"),
    )
