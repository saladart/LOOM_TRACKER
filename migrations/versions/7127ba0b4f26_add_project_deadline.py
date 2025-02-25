"""Add project deadline

Revision ID: 7127ba0b4f26
Revises: 
Create Date: 2024-11-14 14:31:30.875194

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7127ba0b4f26'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deadline', sa.Date(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.drop_column('deadline')

    # ### end Alembic commands ###
