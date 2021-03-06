"""DB update for client monitoring in bg

Revision ID: 6dc1b592bffa
Revises: 5f72e9e0fa9f
Create Date: 2017-04-28 17:55:45.462597

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '6dc1b592bffa'
down_revision = '5f72e9e0fa9f'
branch_labels = None
depends_on = None


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('monitoringrequest', 'request_token',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.Boolean(),
               existing_nullable=True)
    op.add_column('monitoringstatus', sa.Column('fail_count', sa.Integer(), nullable=True))
    op.add_column('monitoringstatus', sa.Column('fail_date', sa.DateTime(), nullable=True))
    op.add_column('monitoringstatus', sa.Column('start_date', sa.DateTime(), nullable=True))
    op.add_column('monitoringstatus', sa.Column('stop_date', sa.DateTime(), nullable=True))
    op.alter_column('torrentrequest', 'request_token',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.Boolean(),
               existing_nullable=True)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('torrentrequest', 'request_token',
               existing_type=sa.Boolean(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.drop_column('monitoringstatus', 'stop_date')
    op.drop_column('monitoringstatus', 'start_date')
    op.drop_column('monitoringstatus', 'fail_date')
    op.drop_column('monitoringstatus', 'fail_count')
    op.alter_column('monitoringrequest', 'request_token',
               existing_type=sa.Boolean(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    ### end Alembic commands ###
