"""add_metadata_to_transcripts

Revision ID: 9ca9cd81c77b
Revises: c5201615a379
Create Date: 2024-12-30 01:17:25.123456

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9ca9cd81c77b'
down_revision = 'c5201615a379'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('transcripts', sa.Column('transcript_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('transcripts', 'transcript_metadata')
    # ### end Alembic commands ###
