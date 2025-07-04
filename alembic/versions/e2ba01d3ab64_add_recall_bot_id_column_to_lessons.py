"""Add recall_bot_id column to lessons

Revision ID: e2ba01d3ab64
Revises: af6aaa42e05d
Create Date: 2025-06-29 18:46:17.034020

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2ba01d3ab64'
down_revision: Union[str, Sequence[str], None] = 'af6aaa42e05d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('lessons', sa.Column('recall_bot_id', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('lessons', 'recall_bot_id')
    # ### end Alembic commands ###
