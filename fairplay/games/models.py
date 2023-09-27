import sqlalchemy as sa
import sqlalchemy.orm as orm
import sqlalchemy_utils

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.collections import attribute_mapped_collection

from ..courses.models import current_course
from ..db import BaseModel, BaseQuery, db


class GameQuery(BaseQuery):
    def filter_by_current_course(self):
        return self.filter_by_course(current_course)

    def filter_by_course(self, course):
        if not course:
            return self.filter(None)

        return self.filter(Game.course == course)


class Game(BaseModel):
    __tablename__ = "game"

    name = sa.Column(sa.String, nullable=False)

    course_id = sa.Column(
        sqlalchemy_utils.UUIDType(),
        sa.ForeignKey("course.id", ondelete="cascade"),
        nullable=False,
    )

    course = orm.relationship("Course", lazy="joined")
    holes = orm.relationship(
        "GameHole",
        collection_class=attribute_mapped_collection("number"),
        back_populates="game",
    )
    players = orm.relationship("GamePlayer", back_populates="game")

    @hybrid_property
    def duration(self):
        return self.date_finished - self.date_started

    @sqlalchemy_utils.aggregated("holes", sa.Column(sa.DateTime(True)))
    def date_started(self):
        return sa.func.min(GameHole.date_started)

    @sqlalchemy_utils.aggregated("holes", sa.Column(sa.DateTime(True)))
    def date_finished(self):
        return sa.func.case(
            sa.func.count(GameHole.date_finished) == sa.func.count(GameHole.id),
            sa.func.max(GameHole.date_finished),
        )

    @sqlalchemy_utils.aggregated(
        "holes", sa.Column(sa.Integer, default=0, server_default="0", nullable=False)
    )
    def hole_count(self):
        return sa.func.count(GameHole.number)

    @sqlalchemy_utils.aggregated(
        "players", sa.Column(sa.Integer, default=0, server_default="0", nullable=False)
    )
    def player_count(self):
        return sa.func.count(GamePlayer.id)

    query_class = GameQuery

    __table_args__ = (
        sa.Index(
            "ix_game_hole_count", hole_count.column, postgresql_where="hole_count > 0"
        ),
        sa.Index(
            "ix_game_player_count",
            player_count.column,
            postgresql_where="player_count > 0",
        ),
        sa.Index(
            "ix_game_name",
            name,
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )


class GameHole(BaseModel):
    __tablename__ = "game_hole"

    date_started = sa.Column(sa.DateTime(True))
    date_finished = sa.Column(sa.DateTime(True))

    number = sa.Column(sa.Integer, nullable=False)
    index = sa.Column(sa.Integer)
    par = sa.Column(sa.Integer)

    game_id = sa.Column(
        sqlalchemy_utils.UUIDType(),
        sa.ForeignKey("game.id", ondelete="cascade"),
        nullable=False,
    )

    hole_id = sa.Column(
        sqlalchemy_utils.UUIDType(),
        sa.ForeignKey("course_hole.id", ondelete="set null"),
    )

    game = orm.relationship("Game", lazy="joined", back_populates="holes")
    hole = orm.relationship("CourseHole", lazy="joined")

    @hybrid_property
    def duration(self):
        return self.date_finished - self.date_started

    __table_args__ = (
        sa.CheckConstraint("number > 0", "ck_game_hole_positive"),
        sa.CheckConstraint("index IS NULL OR index > 0", "ck_game_hole_index_positive"),
        sa.CheckConstraint("par IS NULL or par > 0", "ck_game_hole_par_positive"),
        sa.Index("ix_game_hole_index", index, postgresql_where="index IS NOT NULL"),
        sa.Index("ix_game_hole_par", par, postgresql_where="par IS NOT NULL"),
        sa.UniqueConstraint(game_id, number, name="uq_game_hole_number"),
    )


class GamePlayer(BaseModel):
    __tablename__ = "game_player"

    name = sa.Column(sa.String, nullable=False)
    handicap = sa.Column(sa.Integer)

    game_id = sa.Column(
        sqlalchemy_utils.UUIDType(),
        sa.ForeignKey("game.id", ondelete="cascade"),
        nullable=False,
    )

    player_id = sa.Column(
        sqlalchemy_utils.UUIDType(),
        sa.ForeignKey("player.id", ondelete="restrict"),
        nullable=False,
    )

    game = orm.relationship("Game", lazy="joined", back_populates="players")
    player = orm.relationship("Player", lazy="joined")

    __table_args__ = (
        sa.CheckConstraint(
            "handicap IS NULL OR handicap > 0", "ck_game_player_handicap_positive"
        ),
        sa.Index(
            "ix_game_player_handicap", handicap, postgresql_where="handicap IS NOT NULL"
        ),
        sa.Index(
            "ix_game_player_name",
            name,
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
        sa.UniqueConstraint(game_id, player_id, name="uq_game_player_id"),
    )
