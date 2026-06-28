"""add_models_permission

Revision ID: 000000000004
Revises: 000000000003
Create Date: 2026-06-28 12:00:00.000000

"""
import sqlalchemy as sa
from sqlalchemy import Integer, String, text
from sqlalchemy.sql import column, table

from alembic import op

revision = "000000000004"
down_revision = "000000000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Insert the new permission
    conn.execute(
        sa.text(
            "INSERT INTO permissions (name, description) VALUES (:name, :desc) ON CONFLICT (name) DO NOTHING"
        ),
        {"name": "models:manage", "desc": "List, pull, and delete Ollama models"},
    )

    # Grant it to the admin role (id=1 per seed, but we look it up to be safe)
    conn.execute(
        sa.text("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r, permissions p
            WHERE r.name = 'admin' AND p.name = 'models:manage'
            ON CONFLICT DO NOTHING
        """)
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            DELETE FROM role_permissions
            WHERE permission_id = (SELECT id FROM permissions WHERE name = 'models:manage')
        """)
    )
    conn.execute(sa.text("DELETE FROM permissions WHERE name = 'models:manage'"))
