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
            docs = await self.db.find_many(collection=role_collection_name, filter_dict={"permissions": permission.value})
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
            try:
                oids.append(ObjectId(str(rid)))
            except Exception:
                logger.warning(f"Invalid role ID format: {rid}")
                continue
        
        if not oids:
            return []
        
        try:
            docs = await self.db.find_many(role_collection_name, {"_id": {"$in": oids}})
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
        except PermissionDeniedError:
            raise
        except Exception as e:
            logger.error(f"Failed to create new role: {name}: {e}")
            return None
    
    async def add_permission_to_role(self, executor_id: str, role_id: str, permission: Permission) -> Optional[RoleInDB]:
        try:
            # Get the executor's account
            executor_account = await self.db.find_one_by_id("accounts", executor_id)
            if not executor_account:
                raise PermissionDeniedError("Executor account not found")
            
            executor = AccountInDB(**executor_account)
            executor_roles = await self.get_account_roles(executor)
            executor_perms = {p for r in executor_roles for p in r.permissions}
            
            if Permission.ADMIN not in executor_perms and Permission.EDIT_ROLES not in executor_perms:
                raise PermissionDeniedError("Insufficient permissions to modify roles")
            
            role = await self.get_role_by_id(role_id)
            if not role:
                logger.warning(f"Role {role_id} not found")
                return None
        
            if permission in role.permissions:
                logger.info(f"Permission {permission.value} already exists in role {role.name}")
                return role
            
            if permission == Permission.ADMIN and Permission.ADMIN not in executor_perms:
                raise PermissionDeniedError("Only admins can grant admin permission")
            
            result = await self.db.update_by_id(
                collection=role_collection_name,
                document_id=role_id,
                update={
                    "$addToSet": {"permissions": permission.value}
                }
            )
            
            if result.get("modified_count", 0) > 0:
                updated_role = await self.get_role_by_id(role_id)
                logger.info(f"Added permission {permission.value} to role {role.name}")
                return updated_role
            
            return None
        except PermissionDeniedError:
            raise
        except Exception as e:
            logger.error(f"Failed to add permission to role {role_id}: {e}")
            return None
    
    async def remove_permission_from_role(self, executor_id: str, role_id: str, permission: Permission) -> Optional[RoleInDB]:
        try:
            executor_account = await self.db.find_one_by_id("accounts", executor_id)
            if not executor_account:
                raise PermissionDeniedError("Executor account not found")
            
            executor = AccountInDB(**executor_account)
            executor_roles = await self.get_account_roles(executor)
            executor_perms = {p for r in executor_roles for p in r.permissions}
            
            if Permission.ADMIN not in executor_perms and Permission.EDIT_ROLES not in executor_perms:
                raise PermissionDeniedError("Insufficient permissions to modify roles")
            
            role = await self.get_role_by_id(role_id)
            if not role:
                logger.warning(f"Role {role_id} not found")
                return None
            
            if role.name == "admin" and permission == Permission.ADMIN:
                raise PermissionDeniedError("Cannot remove admin permission from admin role")
            
            if permission not in role.permissions:
                logger.info(f"Permission {permission.value} doesn't exist in role {role.name}")
                return role
            
            if permission == Permission.ADMIN and Permission.ADMIN not in executor_perms:
                raise PermissionDeniedError("Only admins can remove admin permission")
            
            result = await self.db.update_by_id(
                collection=role_collection_name,
                document_id=role_id,
                update={
                    "$pull": {"permissions": permission.value}
                }
            )
            
            if result.get("modified_count", 0) > 0:
                updated_role = await self.get_role_by_id(role_id)
                logger.info(f"Removed permission {permission.value} from role {role.name}")
                return updated_role
            
            return None
            
        except PermissionDeniedError:
            raise
        except Exception as e:
            logger.error(f"Failed to remove permission from role {role_id}: {e}")
            return None
    
    async def grant_role(self, executor_id: str, account_id: str, role_id: str) -> bool:
        try:
            executor_account = await self.db.find_one_by_id("accounts", executor_id)
            if not executor_account:
                raise PermissionDeniedError("Executor account not found")
            
            executor = AccountInDB(**executor_account)
            executor_roles = await self.get_account_roles(executor)
            executor_perms = {p for r in executor_roles for p in r.permissions}
            
            if Permission.ADMIN not in executor_perms and Permission.EDIT_ROLES not in executor_perms:
                raise PermissionDeniedError("Insufficient permissions to grant roles")
            
            role = await self.get_role_by_id(role_id)
            if not role:
                logger.warning(f"Role {role_id} not found")
                return False
            
            if Permission.ADMIN in role.permissions and Permission.ADMIN not in executor_perms:
                raise PermissionDeniedError("Only admins can grant roles with admin permission")
            
            target_account = await self.db.find_one_by_id("accounts", account_id)
            if not target_account:
                logger.warning(f"Target account {account_id} not found")
                return False
            
            existing_roles = target_account.get("roles", [])
            if role_id in [str(r) for r in existing_roles]:
                logger.info(f"Account {account_id} already has role {role.name}")
                return True
            
            result = await self.db.update_by_id(
                collection="accounts",
                document_id=account_id,
                update={
                    "$addToSet": {"roles": role_id}
                }
            )
            
            if result.get("modified_count", 0) > 0:
                logger.info(f"Granted role {role.name} to account {account_id} by {executor_id}")
                return True
            
            return False
        except PermissionDeniedError as e:
            logger.warning(f"Permission denied for granting role: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to grant role {role_id} to account {account_id}: {e}")
            return False
    
    async def revoke_role(self, executor_id: str, account_id: str, role_id: str) -> bool:
        try:
            executor_account = await self.db.find_one_by_id("accounts", executor_id)
            if not executor_account:
                raise PermissionDeniedError("Executor account not found")
            
            executor = AccountInDB(**executor_account)
            executor_roles = await self.get_account_roles(executor)
            executor_perms = {p for r in executor_roles for p in r.permissions}
            
            if Permission.ADMIN not in executor_perms and Permission.EDIT_ROLES not in executor_perms:
                raise PermissionDeniedError("Insufficient permissions to revoke roles")
            
            role = await self.get_role_by_id(role_id)
            if not role:
                logger.warning(f"Role {role_id} not found")
                return False
            
            if Permission.ADMIN in role.permissions and Permission.ADMIN not in executor_perms:
                raise PermissionDeniedError("Only admins can revoke roles with admin permission")
            
            # Prevent removing the last admin (check if this would leave no admins)
            if role.name == "admin":
                admin_count = await self.db.count_documents("accounts", {"roles": role_id})
                if admin_count <= 1:
                    raise PermissionDeniedError("Cannot revoke the last admin role")
            
            target_account = await self.db.find_one_by_id("accounts", account_id)
            if not target_account:
                logger.warning(f"Target account {account_id} not found")
                return False
            
            existing_roles = target_account.get("roles", [])
            if role_id not in [str(r) for r in existing_roles]:
                logger.info(f"Account {account_id} doesn't have role {role.name}")
                return True
            
            result = await self.db.update_by_id(
                collection="accounts",
                document_id=account_id,
                update={
                    "$pull": {"roles": role_id}
                }
            )
            
            if result.get("modified_count", 0) > 0:
                logger.info(f"Revoked role {role.name} from account {account_id} by {executor_id}")
                return True
            
            return False
        except PermissionDeniedError as e:
            logger.warning(f"Permission denied for revoking role: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to revoke role {role_id} from account {account_id}: {e}")
            return False
    
    async def delete_role(self, executor_id: str, role_id: str) -> bool:
        try:
            executor_account = await self.db.find_one_by_id("accounts", executor_id)
            if not executor_account:
                raise PermissionDeniedError("Executor account not found")
            
            executor = AccountInDB(**executor_account)
            executor_roles = await self.get_account_roles(executor)
            executor_perms = {p for r in executor_roles for p in r.permissions}
            
            if Permission.ADMIN not in executor_perms:
                raise PermissionDeniedError("Only admins can delete roles")
            
            role = await self.get_role_by_id(role_id)
            if not role:
                logger.warning(f"Role {role_id} not found")
                return False
            
            if role.name == "admin":
                raise PermissionDeniedError("Cannot delete the admin role")
            
            await self.db.update_many(
                collection="accounts",
                filter_dict={"roles": role_id},
                update={"$pull": {"roles": role_id}}
            )
            
            deleted_count = await self.db.delete_by_id(role_collection_name, role_id)
            
            if deleted_count > 0:
                logger.info(f"Deleted role {role.name} (ID: {role_id}) by {executor_id}")
                return True
            
            return False
        except PermissionDeniedError as e:
            logger.warning(f"Permission denied for deleting role: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete role {role_id}: {e}")
            return False
    
    async def has_permission(self, account: AccountInDB, permission: Permission) -> bool:
        try:
            roles = await self.get_account_roles(account)
            if not roles:
                return False
            
            all_permissions = {p for r in roles for p in r.permissions}
            
            if Permission.ADMIN in all_permissions:
                return True
            
            return permission in all_permissions
        except Exception as e:
            logger.error(f"Failed to check permission for account {account.id}: {e}")
            return False