"""Add is_active field to User and Project

Revision ID: d8aae20cf9e4
Revises: 7127ba0b4f26
Create Date: 2024-11-14 14:48:54.337554

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd8aae20cf9e4'
down_revision = '7127ba0b4f26'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True))

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('is_active')

    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.drop_column('is_active')

    # ### end Alembic commands ###
