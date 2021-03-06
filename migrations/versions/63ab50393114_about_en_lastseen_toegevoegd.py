"""about en lastseen toegevoegd

Revision ID: 63ab50393114
Revises: aab5925ccad7
Create Date: 2019-01-30 12:55:15.883044

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '63ab50393114'
down_revision = 'aab5925ccad7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('about', sa.String(length=140), nullable=True))
    op.add_column('user', sa.Column('lastseen', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'lastseen')
    op.drop_column('user', 'about')
    # ### end Alembic commands ###
