import sqlalchemy as sa
import sqlalchemy.orm as orm
import sqlalchemy_utils

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.collections import attribute_mapped_collection

from ..db import BaseModel, db


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

    __table_args__ = (
        sa.Index("ix_game_hole_count", hole_count, postgresql_where="hole_count > 0"),
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

    course = orm.relationship("Course", lazy="joined")
    game = orm.relationship("Game", lazy="joined", back_populates="holes")

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
