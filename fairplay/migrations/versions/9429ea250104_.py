"""empty message

Revision ID: 9429ea250104
Revises: 711ed2658175
Create Date: 2023-10-01 20:13:19.449216

"""
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9429ea250104"
down_revision = "711ed2658175"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("course", schema=None) as batch_op:
        batch_op.drop_column("pos")
        batch_op.add_geospatial_column(
            sa.Column(
                "pos",
                Geography(
                    geometry_type="POINT",
                    spatial_index=False,
                    from_text="ST_GeogFromText",
                    name="geography",
                ),
                nullable=True,
            )
        )
        batch_op.create_geospatial_index(
            "ix_course_pos",
            ["pos"],
            unique=False,
            postgresql_using="gist",
            postgresql_ops={"pos": "gist_geography_ops"},
        )

    with op.batch_alter_table("course_feature", schema=None) as batch_op:
        batch_op.add_geospatial_column(
            sa.Column(
                "pos",
                Geography(
                    geometry_type="POLYGON",
                    spatial_index=False,
                    from_text="ST_GeogFromText",
                    name="geography",
                ),
                nullable=True,
            )
        )
        batch_op.create_geospatial_index(
            "ix_course_feature_pos",
            ["pos"],
            unique=False,
            postgresql_using="gist",
            postgresql_ops={"pos": "gist_geography_ops"},
        )
        batch_op.drop_column("r")
        batch_op.drop_column("coords")

    with op.batch_alter_table("course_hole", schema=None) as batch_op:
        batch_op.drop_column("pos")
        batch_op.add_geospatial_column(
            sa.Column(
                "pos",
                Geography(
                    geometry_type="POINT",
                    spatial_index=False,
                    from_text="ST_GeogFromText",
                    name="geography",
                ),
                nullable=True,
            )
        )
        batch_op.create_geospatial_index(
            "ix_course_hole_pos",
            ["pos"],
            unique=False,
            postgresql_using="gist",
            postgresql_ops={"pos": "gist_geography_ops"},
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("course_hole", schema=None) as batch_op:
        batch_op.drop_geospatial_index(
            "ix_course_hole_pos",
            postgresql_using="gist",
            postgresql_ops={"pos": "gist_geography_ops"},
            column_name="pos",
        )

    with op.batch_alter_table("course_feature", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("coords", sa.NullType(), autoincrement=False, nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "r",
                sa.DOUBLE_PRECISION(precision=53),
                autoincrement=False,
                nullable=True,
            )
        )
        batch_op.drop_geospatial_index(
            "ix_course_feature_pos",
            postgresql_using="gist",
            postgresql_ops={"pos": "gist_geography_ops"},
            column_name="pos",
        )
        batch_op.drop_geospatial_column("pos")

    with op.batch_alter_table("course", schema=None) as batch_op:
        batch_op.drop_geospatial_index(
            "ix_course_pos",
            postgresql_using="gist",
            postgresql_ops={"pos": "gist_geography_ops"},
            column_name="pos",
        )
    # ### end Alembic commands ###