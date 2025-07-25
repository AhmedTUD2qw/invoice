"""Update invoice model fields

Revision ID: update_invoice_fields
Create Date: 2025-07-26
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'update_invoice_fields'
down_revision = 'initial_migration'
branch_labels = None
depends_on = None

def upgrade():
    # Update nullable constraints
    op.alter_column('invoices', 'supervisor',
        existing_type=sa.String(length=100),
        nullable=False
    )
    op.alter_column('invoices', 'cloudinary_url',
        existing_type=sa.String(length=500),
        nullable=False
    )
    op.alter_column('invoices', 'cloudinary_public_id',
        existing_type=sa.String(length=200),
        nullable=False
    )

def downgrade():
    # Revert nullable constraints
    op.alter_column('invoices', 'supervisor',
        existing_type=sa.String(length=100),
        nullable=True
    )
    op.alter_column('invoices', 'cloudinary_url',
        existing_type=sa.String(length=500),
        nullable=True
    )
    op.alter_column('invoices', 'cloudinary_public_id',
        existing_type=sa.String(length=200),
        nullable=True
    )
