"""Add monetization fields to bundles table

Revision ID: add_monetization_fields
Revises: 
Create Date: 2026-03-17 23:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_monetization_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to bundles table
    op.add_column('bundles', sa.Column('is_public', sa.Boolean(), nullable=True, server_default='true'))
    op.add_column('bundles', sa.Column('owner_user_id', sa.String(), nullable=True))
    
    # Create indexes
    op.create_index('idx_bundles_owner_user_id', 'bundles', ['owner_user_id'])
    op.create_index('idx_bundles_is_public', 'bundles', ['is_public'])


def downgrade() -> None:
    # Remove indexes
    op.drop_index('idx_bundles_is_public', table_name='bundles')
    op.drop_index('idx_bundles_owner_user_id', table_name='bundles')
    
    # Remove columns
    op.drop_column('bundles', 'owner_user_id')
    op.drop_column('bundles', 'is_public')
