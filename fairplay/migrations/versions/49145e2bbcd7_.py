"""empty message

Revision ID: 49145e2bbcd7
Revises: a2392ec04c5c
Create Date: 2023-09-26 20:05:06.545299

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils

from sqlalchemy.sql.schema import ScalarElementColumnDefault

from fairplay.courses.models import CourseFeature
from fairplay.db import Coordinates


# revision identifiers, used by Alembic.
revision = "49145e2bbcd7"
down_revision = "a2392ec04c5c"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "course",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("hole_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "id",
            sqlalchemy_utils.types.uuid.UUIDType(),
            server_default=sa.text("uuid_generate_v1()"),
            nullable=False,
        ),
        sa.Column(
            "created_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_updated_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("course", schema=None) as batch_op:
        batch_op.create_index(
            "ix_course_hole_count",
            ["hole_count"],
            unique=False,
            postgresql_where="hole_count > 0",
        )
        batch_op.create_index(
            "ix_course_name",
            ["name"],
            unique=False,
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        )

    op.create_table(
        "course_hole",
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("index", sa.Integer(), nullable=True),
        sa.Column("par", sa.Integer(), nullable=True),
        sa.Column("course_id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column(
            "id",
            sqlalchemy_utils.types.uuid.UUIDType(),
            server_default=sa.text("uuid_generate_v1()"),
            nullable=False,
        ),
        sa.Column(
            "created_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_updated_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "index IS NULL OR index > 0", name="ck_course_hole_index_positive"
        ),
        sa.CheckConstraint("number > 0", name="ck_course_hole_positive"),
        sa.CheckConstraint(
            "par IS NULL or par > 0", name="ck_course_hole_par_positive"
        ),
        sa.ForeignKeyConstraint(["course_id"], ["course.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "number", name="uq_course_hole_number"),
    )
    with op.batch_alter_table("course_hole", schema=None) as batch_op:
        batch_op.create_index(
            "ix_course_hole_index",
            ["index"],
            unique=False,
            postgresql_where="index IS NOT NULL",
        )
        batch_op.create_index(
            "ix_course_hole_par",
            ["par"],
            unique=False,
            postgresql_where="par IS NOT NULL",
        )

    op.create_table(
        "game",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("course_id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column("date_started", sa.DateTime(timezone=True), nullable=True),
        sa.Column("date_finished", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hole_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("player_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "id",
            sqlalchemy_utils.types.uuid.UUIDType(),
            server_default=sa.text("uuid_generate_v1()"),
            nullable=False,
        ),
        sa.Column(
            "created_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_updated_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["course_id"], ["course.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("game", schema=None) as batch_op:
        batch_op.create_index(
            "ix_game_hole_count",
            ["hole_count"],
            unique=False,
            postgresql_where="hole_count > 0",
        )
        batch_op.create_index(
            "ix_game_name",
            ["name"],
            unique=False,
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        )
        batch_op.create_index(
            "ix_game_player_count",
            ["player_count"],
            unique=False,
            postgresql_where="player_count > 0",
        )

    op.create_table(
        "player",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("handicap", sa.Integer(), nullable=True),
        sa.Column("course_id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column("player_id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=True),
        sa.Column(
            "id",
            sqlalchemy_utils.types.uuid.UUIDType(),
            server_default=sa.text("uuid_generate_v1()"),
            nullable=False,
        ),
        sa.Column(
            "created_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_updated_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "handicap IS NULL OR handicap > 0", name="ck_player_handicap_positive"
        ),
        sa.ForeignKeyConstraint(["course_id"], ["course.id"], ondelete="cascade"),
        sa.ForeignKeyConstraint(["player_id"], ["player.id"], ondelete="set null"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "player_id", name="uq_player_id"),
    )
    with op.batch_alter_table("player", schema=None) as batch_op:
        batch_op.create_index(
            "ix_player_handicap",
            ["handicap"],
            unique=False,
            postgresql_where="handicap IS NOT NULL",
        )
        batch_op.create_index(
            "ix_player_name",
            ["name"],
            unique=False,
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        )

    Coordinates.create(op.get_bind(), checkfirst=False)
    op.create_table(
        "course_feature",
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "type",
            sqlalchemy_utils.types.choice.ChoiceType(
                CourseFeature.FEATURE_TYPE_CHOICES
            ),
            nullable=False,
        ),
        sa.Column(
            "coords",
            sqlalchemy_utils.types.pg_composite.CompositeType(
                "coordinates",
                (
                    sa.Column("lat", sa.Float()),
                    sa.Column("lon", sa.Float()),
                    sa.Column(
                        "hgt",
                        sa.Float(),
                        default=ScalarElementColumnDefault(0.0),
                    ),
                ),
            ),
            nullable=True,
        ),
        sa.Column("r", sa.Float(), nullable=True),
        sa.Column("hole_id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column(
            "id",
            sqlalchemy_utils.types.uuid.UUIDType(),
            server_default=sa.text("uuid_generate_v1()"),
            nullable=False,
        ),
        sa.Column(
            "created_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_updated_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["hole_id"], ["course_hole.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("course_feature", schema=None) as batch_op:
        batch_op.create_index("ix_course_feature_hole_id", ["hole_id"], unique=False)
        batch_op.create_index("ix_course_feature_type", ["type"], unique=False)

    op.create_table(
        "game_hole",
        sa.Column("date_started", sa.DateTime(timezone=True), nullable=True),
        sa.Column("date_finished", sa.DateTime(timezone=True), nullable=True),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("index", sa.Integer(), nullable=True),
        sa.Column("par", sa.Integer(), nullable=True),
        sa.Column("game_id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column("hole_id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=True),
        sa.Column(
            "id",
            sqlalchemy_utils.types.uuid.UUIDType(),
            server_default=sa.text("uuid_generate_v1()"),
            nullable=False,
        ),
        sa.Column(
            "created_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_updated_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "index IS NULL OR index > 0", name="ck_game_hole_index_positive"
        ),
        sa.CheckConstraint("number > 0", name="ck_game_hole_positive"),
        sa.CheckConstraint("par IS NULL or par > 0", name="ck_game_hole_par_positive"),
        sa.ForeignKeyConstraint(["game_id"], ["game.id"], ondelete="cascade"),
        sa.ForeignKeyConstraint(["hole_id"], ["course_hole.id"], ondelete="set null"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("game_id", "number", name="uq_game_hole_number"),
    )
    with op.batch_alter_table("game_hole", schema=None) as batch_op:
        batch_op.create_index(
            "ix_game_hole_index",
            ["index"],
            unique=False,
            postgresql_where="index IS NOT NULL",
        )
        batch_op.create_index(
            "ix_game_hole_par",
            ["par"],
            unique=False,
            postgresql_where="par IS NOT NULL",
        )

    op.create_table(
        "game_player",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("handicap", sa.Integer(), nullable=True),
        sa.Column("game_id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column("player_id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column(
            "id",
            sqlalchemy_utils.types.uuid.UUIDType(),
            server_default=sa.text("uuid_generate_v1()"),
            nullable=False,
        ),
        sa.Column(
            "created_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_updated_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "handicap IS NULL OR handicap > 0", name="ck_game_player_handicap_positive"
        ),
        sa.ForeignKeyConstraint(["game_id"], ["game.id"], ondelete="cascade"),
        sa.ForeignKeyConstraint(["player_id"], ["player.id"], ondelete="restrict"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("game_id", "player_id", name="uq_game_player_id"),
    )
    with op.batch_alter_table("game_player", schema=None) as batch_op:
        batch_op.create_index(
            "ix_game_player_handicap",
            ["handicap"],
            unique=False,
            postgresql_where="handicap IS NOT NULL",
        )
        batch_op.create_index(
            "ix_game_player_name",
            ["name"],
            unique=False,
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("game_player", schema=None) as batch_op:
        batch_op.drop_index(
            "ix_game_player_name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        )
        batch_op.drop_index(
            "ix_game_player_handicap", postgresql_where="handicap IS NOT NULL"
        )

    op.drop_table("game_player")
    with op.batch_alter_table("game_hole", schema=None) as batch_op:
        batch_op.drop_index("ix_game_hole_par", postgresql_where="par IS NOT NULL")
        batch_op.drop_index("ix_game_hole_index", postgresql_where="index IS NOT NULL")

    op.drop_table("game_hole")
    with op.batch_alter_table("course_feature", schema=None) as batch_op:
        batch_op.drop_index("ix_course_feature_type")
        batch_op.drop_index("ix_course_feature_hole_id")

    op.drop_table("course_feature")
    with op.batch_alter_table("player", schema=None) as batch_op:
        batch_op.drop_index(
            "ix_player_name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        )
        batch_op.drop_index(
            "ix_player_handicap", postgresql_where="handicap IS NOT NULL"
        )

    op.drop_table("player")
    with op.batch_alter_table("game", schema=None) as batch_op:
        batch_op.drop_index("ix_game_player_count", postgresql_where="player_count > 0")
        batch_op.drop_index(
            "ix_game_name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        )
        batch_op.drop_index("ix_game_hole_count", postgresql_where="hole_count > 0")

    op.drop_table("game")
    with op.batch_alter_table("course_hole", schema=None) as batch_op:
        batch_op.drop_index("ix_course_hole_par", postgresql_where="par IS NOT NULL")
        batch_op.drop_index(
            "ix_course_hole_index", postgresql_where="index IS NOT NULL"
        )

    op.drop_table("course_hole")
    with op.batch_alter_table("course", schema=None) as batch_op:
        batch_op.drop_index(
            "ix_course_name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        )
        batch_op.drop_index("ix_course_hole_count", postgresql_where="hole_count > 0")

    op.drop_table("course")
    # ### end Alembic commands ###
