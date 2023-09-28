"""empty message

Revision ID: b4682cdc3418
Revises: 49145e2bbcd7
Create Date: 2023-09-27 21:20:54.659786

"""
from alembic import op
from sqlalchemy.sql.schema import ScalarElementColumnDefault
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision = "b4682cdc3418"
down_revision = "49145e2bbcd7"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("course", schema=None) as batch_op:
        batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "pos",
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
            )
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("course", schema=None) as batch_op:
        batch_op.drop_column("pos")
        batch_op.drop_column("description")

    # ### end Alembic commands ###
