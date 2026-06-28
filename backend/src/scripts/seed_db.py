import asyncio
import logging
import os
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.getcwd())

from src.core.database import AsyncSessionLocal
from src.modules.auth.models import Permission, Role, User
from src.modules.auth.utils import get_password_hash

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def seed_roles_and_permissions(session: AsyncSession):
    # Define Permissions
    permissions_data = [
        {"name": "users:read", "description": "View all users"},
        {"name": "prompts:read_all", "description": "View all prompts"},
        {"name": "prompts:create", "description": "Create prompts"},
    ]

    # Create Permissions
    db_permissions = {}
    for perm in permissions_data:
        stmt = select(Permission).where(Permission.name == perm["name"])
        result = await session.execute(stmt)
        existing_perm = result.scalars().first()

        if not existing_perm:
            new_perm = Permission(name=perm["name"], description=perm["description"])
            session.add(new_perm)
            await session.flush()  # Flush to get ID
            db_permissions[perm["name"]] = new_perm
            logger.info(f"Created Permission: {perm['name']}")
        else:
            db_permissions[perm["name"]] = existing_perm

    # Define Roles
    roles_data = ["admin", "user"]
    db_roles = {}

    for role_name in roles_data:
        stmt = select(Role).where(Role.name == role_name)
        result = await session.execute(stmt)
        existing_role = result.scalars().first()

        if not existing_role:
            new_role = Role(name=role_name)
            session.add(new_role)
            await session.flush()
            db_roles[role_name] = new_role
            logger.info(f"Created Role: {role_name}")
        else:
            # We need to explicitly load permissions to manipulate them if utilizing ORM relationships,
            # or just assume they are there. For seeding, let's load them to ensure associations.
            await session.refresh(existing_role, attribute_names=["permissions"])
            db_roles[role_name] = existing_role

    # Assign Permissions to Roles
    # Admin gets all
    admin_role = db_roles["admin"]
    for name, perm in db_permissions.items():
        if perm not in admin_role.permissions:
            admin_role.permissions.append(perm)
            logger.info(f"Assigned {name} to Admin")

    # User gets specific
    user_role = db_roles["user"]
    user_perms = ["prompts:create"]
    for name in user_perms:
        perm = db_permissions.get(name)
        if perm and perm not in user_role.permissions:
            user_role.permissions.append(perm)
            logger.info(f"Assigned {name} to User")

    await session.commit()


async def seed_users(session: AsyncSession):
    # 1. Fetch Roles
    stmt = select(Role).where(Role.name == "admin")
    result = await session.execute(stmt)
    admin_role = result.scalars().first()

    stmt = select(Role).where(Role.name == "user")
    result = await session.execute(stmt)
    user_role = result.scalars().first()

    # 2. Create Admin User
    admin_email = "admin@example.com"
    stmt = select(User).where(User.email == admin_email)
    result = await session.execute(stmt)
    existing_admin = result.scalars().first()

    if not existing_admin:
        admin_user = User(
            email=admin_email,
            hashed_password=get_password_hash("adminpass"),
            role_id=admin_role.id,
            is_active=True,
        )
        session.add(admin_user)
        logger.info(f"Created Admin user: {admin_email} / adminpass")
    else:
        logger.info(f"Admin user {admin_email} already exists")

    # 3. Create Standard User
    user_email = "user@example.com"
    stmt = select(User).where(User.email == user_email)
    result = await session.execute(stmt)
    existing_user = result.scalars().first()

    if not existing_user:
        startdard_user = User(
            email=user_email,
            hashed_password=get_password_hash("userpass"),
            role_id=user_role.id,
            is_active=True,
        )
        session.add(startdard_user)
        logger.info(f"Created Standard user: {user_email} / userpass")
    else:
        logger.info(f"Standard user {user_email} already exists")

    await session.commit()


async def main():
    async with AsyncSessionLocal() as session:
        try:
            await seed_roles_and_permissions(session)
            await seed_users(session)
        except Exception as e:
            logger.error(f"Error seeding database: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
