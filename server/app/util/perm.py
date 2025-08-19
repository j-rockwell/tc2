from typing import List
from app.schema.perm import Permission, Role
from app.schema.account import AccountInDB

class Permissions:
    @staticmethod
    async def has_permission(roles: List[Role], permission: Permission) -> bool:
        if not roles:
            return False
        
        all = {p for r in roles for p in r.permissions}
        return permission in all