from bson import ObjectId
from typing import List, Optional
import logging

from app.db.mongo import Mongo
from app.schema.account import AccountInDB
from app.schema.perm import Permission, Role, RoleInDB
from app.util.errors import PermissionDeniedError
from app.config import settings

logger = logging.getLogger(__name__)
role_collection_name = "roles"

class RoleRepository:
    def __init__(self, db: Mongo):
        self.db = db
    
    async def perform_role_setup(self):
        if not settings.environment == "dev":
            logger.info("Skipping role setup in non-dev environment")
            return
        
        try:
            admin = await self.get_role_by_name("admin")
            if admin:
                logger.info("Admin role already exists, skipping setup")
                return
            
            admin_role = Role(
                name="admin",
                permissions=[
                    Permission.ADMIN,
                ]
            )
            
            await self.db.insert(collection=role_collection_name, document=admin_role.dict())
            logger.info("Created default admin role")
        except Exception as e:
            logger.error(f"Failed to perform role setup: {e}")
            raise RuntimeError("Failed to perform role setup in the database")
    
    async def get_role_by_id(self, role_id: str) -> Optional[RoleInDB]:
        try:
            doc = await self.db.find_one_by_id(role_collection_name, role_id)
            if not doc:
                return None
            
            return RoleInDB(**doc)
        except Exception as e:
            logger.error(f"Failed to get role by ID {role_id}: {e}")
            return None

    async def get_role_by_name(self, name: str) -> Optional[RoleInDB]:
        try:
            doc = await self.db.find_one(collection=role_collection_name, filter_dict={"name": name.lower()})
            if not doc:
                return None
            
            return RoleInDB(**doc)
        except Exception as e:
            logger.error(f"Failed to get role by name {name}: {e}")
            return None
    
    async def get_role_by_perm(self, permission: Permission) -> List[RoleInDB]:
        try:
            docs = await self.db.find_many(collection=role_collection_name, filter_dict={"permission": permission.value})
            if not docs:
                return []
            
            roles = [RoleInDB(**doc) for doc in docs]
            return roles
        except Exception as e:
            logger.error(f"Failed to get roles by permission {permission.value}: {e}")
            return []
    
    async def get_account_roles(self, account: AccountInDB) -> List[RoleInDB]:
        role_ids = getattr(account, "roles", None) or []
        if not role_ids:
            return []
        
        oids: List[ObjectId] = []
        for rid in role_ids:
            oids.append(ObjectId(str(rid)))
        
        if not oids:
            return []
        
        try:
            docs = await self.db.find_many(role_collection_name, {"$in": oids})
            roles = [RoleInDB(**doc) for doc in docs]
            return roles
        except Exception as e:
            logger.error(f"Failed to get account roles for {account.id}: {e}")
            return []

    async def create_role(self, author: AccountInDB, name: str, permissions: List[Permission]) -> Optional[RoleInDB]:
        try:
            existing = await self.db.find_one(role_collection_name, {"name": name.lower()})
            if existing:
                logger.warning("Attempted to create a duplicate role name")
                return None
            
            author_roles = await self.get_account_roles(author)
            if not author_roles:
                raise PermissionDeniedError(
                    "Insufficient permissions to create a role"
                )
            
            author_perms = {p for r in author_roles for p in r.permissions}
            if Permission.ADMIN not in author_perms and Permission.ADMIN in permissions:
                raise PermissionDeniedError(
                    "Insufficient permissions to create a role with admin privileges"
                )
            
            if Permission.EDIT_ROLES not in author_perms and Permission.ADMIN not in author_perms:
                raise PermissionDeniedError(
                    "Insufficient permissions to create a role"
                )
            
            new_role = Role(name=name.lower(), permissions=permissions)
            inserted = await self.db.insert(collection=role_collection_name, document=new_role.dict(exclude_none=True))
            in_db = await self.db.find_one_by_id(collection=role_collection_name, document_id=inserted)
            
            if not in_db:
                logger.error(f"Failed to insert new role in the database")
                return None
            
            return RoleInDB(**in_db)
        except Exception as e:
            logger.error(f"Failed to create new role: {name}: {e}")
    
    async def add_permission_to_role(self, role_id: str, permission: Permission) -> Optional[RoleInDB]:
        pass
    
    async def remove_permission_from_role(self, role_id: str, permission: Permission) -> Optional[RoleInDB]:
        pass
    
    async def grant_role(self, executor_id: str, account_id: str, role_id: str) -> bool:
        return False
    
    async def revoke_role(self, executor_id: str, account_id: str, role_id: str) -> bool:
        return False