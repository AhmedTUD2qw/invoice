"""Initial migration

Revision ID: initial_migration
Create Date: 2025-07-25
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Check if tables exist before creating them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'users' not in tables:
        op.create_table('users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('username', sa.String(length=80), unique=True, nullable=False),
            sa.Column('password', sa.String(length=120), nullable=False),
            sa.Column('role', sa.String(length=20), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )

    if 'invoices' not in tables:
        op.create_table('invoices',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('image_name', sa.String(length=200), nullable=False),
            sa.Column('model_name', sa.String(length=100), nullable=False),
            sa.Column('branch', sa.String(length=100), nullable=False),
            sa.Column('supervisor', sa.String(length=100), nullable=True),
            sa.Column('upload_date', sa.DateTime(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('cloudinary_url', sa.String(length=500), nullable=True),
            sa.Column('cloudinary_public_id', sa.String(length=200), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

def downgrade():
    op.drop_table('invoices')
    op.drop_table('users')
