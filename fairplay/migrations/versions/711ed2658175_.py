"""empty message

Revision ID: 711ed2658175
Revises: eeb6c86597af
Create Date: 2023-09-30 18:28:21.344095

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "711ed2658175"
down_revision = "eeb6c86597af"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("audit", schema=None) as batch_op:
        batch_op.add_column(sa.Column("location", sa.String(), nullable=True))

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("last_login_location", sa.String(), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "last_login_remote_addr",
                sqlalchemy_utils.types.ip_address.IPAddressType(length=50).with_variant(
                    postgresql.INET(), "postgresql"
                ),
                nullable=True,
            )
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("last_login_remote_addr")
        batch_op.drop_column("last_login_location")

    with op.batch_alter_table("audit", schema=None) as batch_op:
        batch_op.drop_column("location")

    # ### end Alembic commands ###
