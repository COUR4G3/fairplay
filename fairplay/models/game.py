import datetime as dt

import sqlalchemy as sa
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy_utils import aggregated
from sqlalchemy_utils import UUIDType

from ..db import BaseModel
from ..db import BaseQuery
from ..db import db


game_player = db.Table(
    "game_player",
    sa.Column(
        "game_id",
        UUIDType,
        sa.ForeignKey("game.id", ondelete="cascade"),
        nullable=False,
    ),
    sa.Column(
        "player_id",
        UUIDType,
        sa.ForeignKey("player.id", ondelete="cascade"),
        nullable=False,
    ),
)


class GameQuery(BaseQuery):
    pass


class Game(BaseModel):
    __tablename__ = "game"

    date_planned = sa.Column(sa.DateTime)
    date_started = sa.Column(sa.DateTime)
    date_ended = sa.Column(sa.DateTime)

    course_id = sa.Column(
        UUIDType,
        sa.ForeignKey("course.id", ondelete="cascade"),
        nullable=False,
    )

    course = relationship("Course", back_populates="games")

    players = relationship(
        "Player", secondary="game_player", back_populates="games"
    )

    __sql_constraints__ = (
        sa.Index(
            "ix_game_date_planned", date_planned, postgresql_using="brin"
        ),
        sa.Index(
            "ix_game_date", date_started, date_ended, postgresql_using="brin"
        ),
        sa.Index(
            "ix_game_player_count", "player_count", postgresql_using="brin"
        ),
    )

    @hybrid_property
    def date(self):
        if self.date_started:
            return self.date_started.date()
        elif self.date_planned:
            return self.date_planned.date()

    @date.expression  # type: ignore[no-redef]
    def date(cls):
        return sa.func.date(
            sa.func.coalesce(cls.date_started, cls.date_planned)
        )

    @hybrid_property
    def duration(self):
        if self.date_ended:
            return self.date_ended - self.date_started
        elif self.date_started:
            return dt.datetime.utcnow() - self.date_started
        else:
            return dt.timedelta()

    @duration.expression  # type: ignore[no-redef]
    def duration(cls):
        return sa.func.coalesce(
            cls.date_ended, sa.text("CURRENT_TIMESTAMP")
        ) - sa.func.coalesce(cls.date_started, sa.text("CURRENT_TIMESTAMP"))

    @aggregated("players", sa.Column(sa.Integer))
    def player_count(self):
        return sa.func.count("1")
