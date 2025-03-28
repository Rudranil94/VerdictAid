"""create user devices

Revision ID: 001
Revises: 
Create Date: 2025-03-28 11:05:53.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE devicetype AS ENUM ('web', 'mobile', 'desktop')")
    op.execute("CREATE TYPE notificationchannel AS ENUM ('email', 'web_push', 'fcm')")
    
    # Create user_devices table
    op.create_table(
        'user_devices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('device_type', sa.Enum('web', 'mobile', 'desktop', name='devicetype'), nullable=False),
        sa.Column('device_name', sa.String(length=100), nullable=False),
        sa.Column('notification_channel', sa.Enum('email', 'web_push', 'fcm', name='notificationchannel'), nullable=False),
        sa.Column('push_subscription', sa.String(length=1024), nullable=True),
        sa.Column('fcm_token', sa.String(length=512), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_devices_user_id'), 'user_devices', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_devices_user_id'), table_name='user_devices')
    op.drop_table('user_devices')
    op.execute("DROP TYPE notificationchannel")
    op.execute("DROP TYPE devicetype")
