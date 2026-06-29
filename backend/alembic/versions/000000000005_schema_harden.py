"""schema_harden

Add ondelete cascades to foreign keys and missing indexes.

Revision ID: 000000000005
Revises: 000000000004
Create Date: 2026-06-28 14:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

revision = "000000000005"
down_revision = "000000000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Drop and recreate prompts.user_id FK with ondelete=SET NULL + add index
    op.drop_constraint("prompts_user_id_fkey", "prompts", type_="foreignkey")
    op.create_foreign_key(
        "prompts_user_id_fkey", "prompts", "users", ["user_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index(op.f("ix_prompts_user_id"), "prompts", ["user_id"], unique=False)

    # 2. Drop and recreate users.role_id FK with ondelete=SET NULL
    op.drop_constraint("users_role_id_fkey", "users", type_="foreignkey")
    op.create_foreign_key(
        "users_role_id_fkey", "users", "roles", ["role_id"], ["id"], ondelete="SET NULL"
    )

    # 3. Drop and recreate role_permissions FKs with ondelete=CASCADE
    op.drop_constraint("role_permissions_role_id_fkey", "role_permissions", type_="foreignkey")
    op.drop_constraint("role_permissions_permission_id_fkey", "role_permissions", type_="foreignkey")
    op.create_foreign_key(
        "role_permissions_role_id_fkey",
        "role_permissions", "roles",
        ["role_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "role_permissions_permission_id_fkey",
        "role_permissions", "permissions",
        ["permission_id"], ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # 1. Drop index and revert prompts FK
    op.drop_index(op.f("ix_prompts_user_id"), table_name="prompts")
    op.drop_constraint("prompts_user_id_fkey", "prompts", type_="foreignkey")
    op.create_foreign_key("prompts_user_id_fkey", "prompts", "users", ["user_id"], ["id"])

    # 2. Revert users FK
    op.drop_constraint("users_role_id_fkey", "users", type_="foreignkey")
    op.create_foreign_key("users_role_id_fkey", "users", "roles", ["role_id"], ["id"])

    # 3. Revert role_permissions FKs
    op.drop_constraint("role_permissions_role_id_fkey", "role_permissions", type_="foreignkey")
    op.drop_constraint("role_permissions_permission_id_fkey", "role_permissions", type_="foreignkey")
    op.create_foreign_key(
        "role_permissions_role_id_fkey", "role_permissions", "roles", ["role_id"], ["id"]
    )
    op.create_foreign_key(
        "role_permissions_permission_id_fkey", "role_permissions", "permissions", ["permission_id"], ["id"]
    )
