"""db_rbac

Revision ID: 000000000003
Revises: 000000000002
Create Date: 2026-01-19 12:30:00.000000

"""
import sqlalchemy as sa
from sqlalchemy import Integer, String, text
from sqlalchemy.sql import column, table

from alembic import op

# revision identifiers, used by Alembic.
revision = "000000000003"
down_revision = "000000000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create Permissions Table
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_permissions_name"), "permissions", ["name"], unique=True)
    op.create_index(op.f("ix_permissions_id"), "permissions", ["id"], unique=False)

    # 2. Create Roles Table
    roles_table = op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)
    op.create_index(op.f("ix_roles_id"), "roles", ["id"], unique=False)

    # 3. Create Association Table
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            ondelete="CASCADE",
        ),
    )

    # 4. Modify Users Table
    # Drop the old 'role' string column
    op.drop_column("users", "role")
    # Add new 'role_id' column
    op.add_column("users", sa.Column("role_id", sa.Integer(), nullable=True))
    op.create_foreign_key(None, "users", "roles", ["role_id"], ["id"], ondelete="SET NULL")

    # 5. Seed Data (Data Migration)
    conn = op.get_bind()

    conn.execute(
        text("INSERT INTO permissions (name, description) VALUES (:name, :desc)"),
        [
            {"name": "users:read", "desc": "View all users"},
            {"name": "prompts:read_all", "desc": "View all prompts"},
            {"name": "prompts:create", "desc": "Create prompts"},
        ],
    )

    conn.execute(
        text("INSERT INTO roles (name) VALUES (:name)"),
        [
            {"name": "admin"},
            {"name": "user"},
        ],
    )

    # Admin gets everything — query actual IDs to avoid auto-increment assumptions
    conn.execute(
        text("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r, permissions p
            WHERE r.name = 'admin' AND p.name IN ('users:read', 'prompts:read_all', 'prompts:create')
        """)
    )

    # User gets create prompt
    conn.execute(
        text("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r, permissions p
            WHERE r.name = 'user' AND p.name = 'prompts:create'
        """)
    )


def downgrade() -> None:
    op.drop_constraint(None, "users", type_="foreignkey")
    op.drop_column("users", "role_id")
    op.add_column("users", sa.Column("role", sa.VARCHAR(), nullable=False))
    op.drop_table("role_permissions")
    op.drop_index(op.f("ix_roles_id"), table_name="roles")
    op.drop_index(op.f("ix_roles_name"), table_name="roles")
    op.drop_table("roles")
    op.drop_index(op.f("ix_permissions_id"), table_name="permissions")
    op.drop_index(op.f("ix_permissions_name"), table_name="permissions")
    op.drop_table("permissions")
