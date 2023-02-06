import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from ..auth import User
from ..db import BaseModel
from ..db import BaseQuery


class PlayerQuery(BaseQuery):
    pass


class Player(BaseModel):
    __tablename__ = "player"

    name = sa.Column(sa.String, index=True, nullable=False)

    games = relationship(
        "Game", secondary="game_player", back_populates="players"
    )

    user_id = sa.Column(
        UUIDType, sa.ForeignKey("users.id", ondelete="cascade"), nullable=False
    )

    user = relationship("User", lazy="joined", backref="player")

    query_class = PlayerQuery
