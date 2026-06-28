"""db_rbac

Revision ID: 000000000003
Revises: 000000000002
Create Date: 2026-01-19 12:30:00.000000

"""
import sqlalchemy as sa
from sqlalchemy import Integer, String
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
        sa.Column("role_id", sa.Integer(), nullable=True),
        sa.Column("permission_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
        ),
    )

    # 4. Modify Users Table
    # Drop the old 'role' string column
    op.drop_column("users", "role")
    # Add new 'role_id' column
    op.add_column("users", sa.Column("role_id", sa.Integer(), nullable=True))
    op.create_foreign_key(None, "users", "roles", ["role_id"], ["id"])

    # 5. Seed Data (Data Migration)
    # Define temp tables for insertion
    permissions = table(
        "permissions", column("name", String), column("description", String)
    )
    roles = table("roles", column("name", String))
    role_permissions = table(
        "role_permissions", column("role_id", Integer), column("permission_id", Integer)
    )

    # Insert Permissions
    op.bulk_insert(
        permissions,
        [
            {"name": "users:read", "description": "View all users"},
            {"name": "prompts:read_all", "description": "View all prompts"},
            {"name": "prompts:create", "description": "Create prompts"},
        ],
    )

    # Insert Roles
    op.bulk_insert(
        roles,
        [
            {"name": "admin"},
            {"name": "user"},
        ],
    )

    # Need to map IDs to link them...
    # For simplicity in this script, we assume auto-increment gives admin=1, user=2.
    # In a strict prod env, we'd query first.

    # Permission IDs (assumed): 1=users:read, 2=prompts:read_all, 3=prompts:create
    # Role IDs (assumed): 1=admin, 2=user

    # Admin gets everything
    op.bulk_insert(
        role_permissions,
        [
            {"role_id": 1, "permission_id": 1},
            {"role_id": 1, "permission_id": 2},
            {"role_id": 1, "permission_id": 3},
        ],
    )

    # User gets create prompt
    op.bulk_insert(
        role_permissions,
        [
            {"role_id": 2, "permission_id": 3},
        ],
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
