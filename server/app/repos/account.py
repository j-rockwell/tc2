from typing import Optional, Dict, Any, List, Tuple, Union
from datetime import datetime, timezone
import logging

from app.db.redis import Redis
from app.db.mongo import Mongo
from app.repos.perm import RoleRepository
from app.schema.account import AccountBase, AccountMeta, AccountInDB
from app.util.hash import Hasher
from app.config import settings

logger = logging.getLogger(__name__)
collection_name = "accounts"

class AccountRepository:
    def __init__(self, mongo: Mongo, redis: Redis):
        self.mongo = mongo
        self.redis = redis
    
    async def perform_account_setup(self, role_repo: RoleRepository):
        if not settings.environment == "dev":
            logger.info("Skipping account setup in non-dev environment")
            return
        
        try:            
            admin_role = await role_repo.get_role_by_name("admin")
            if not admin_role:
                logger.fatal("Admin role not found, cannot create default admin account")
                raise RuntimeError("Admin role not found, cannot create default admin account")
            
            admin = await self.get_account_by_key_value("username", "admin")
            if admin:
                logger.info("Admin account already exists, skipping setup")
                return
            
            admin_account = AccountBase(
                username=settings.default_admin_username,
                email=settings.default_admin_email,
                password=Hasher.make(settings.default_admin_password),
                metadata=AccountMeta(
                    created_at=datetime.now(timezone.utc),
                    last_active=datetime.now(timezone.utc),
                        email_confirmed=True
                ),
                bio=None,
                profile=None,
                privacy=None,
                roles=[admin_role.id]
            )
                
            await self.mongo.insert(collection=collection_name, document=admin_account.dict(by_alias=True, exclude_none=True))
            logger.info("Created default admin account")
        except Exception as e:
            logger.error(f"Failed to perform account setup: {e}")
            raise RuntimeError("Failed to perform account setup in the database")
    
    async def get_account_by_id(self, account_id: str) -> Optional[AccountInDB]:
        account = await self.mongo.find_one_by_id(collection=collection_name, document_id=account_id)   
        return AccountInDB(**account) if account else None
    
    async def get_account_by_key_value(self, key: str, value: str) -> Optional[AccountInDB]:
        account = await self.mongo.find_one(collection=collection_name, filter_dict={key: value})
        return AccountInDB(**account) if account else None
    
    async def get_many_accounts_by_filter(
        self,
        filter: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Tuple[str, Union[int, str]]]] = None,
        skip: int = 0,
        limit: int = 0,
    ) -> List[AccountInDB]:
        query = await self.mongo.find_many(collection=collection_name, filter_dict=filter)
        return [AccountInDB(**q) for q in (query or [])]
    
    async def get_profile(self, account_id: str) -> Optional[AccountInDB]:
        account = await self.get_account_by_id(account_id)
        return account if account and account.profile else None
    
    async def get_bio(self, account_id: str) -> Optional[AccountInDB]:
        account = await self.get_account_by_id(account_id)
        return account if account and account.bio else None
    
    async def get_privacy(self, account_id: str) -> Optional[AccountInDB]:
        account = await self.get_account_by_id(account_id)
        return account if account and account.privacy else None
    
    async def create_account(self, username: str, email: str, password: str) -> Optional[AccountInDB]:
        pwd = Hasher.make(password)
        now = datetime.now(timezone.utc)
        
        new_account = AccountBase(
            email=email,
            username=username,
            password=pwd,
            metadata=AccountMeta(
                created_at=now,
                last_active=now,
                email_confirmed=False),
            bio=None,
            profile=None,
            privacy=None,
        )
        
        inserted = await self.mongo.insert(collection=collection_name, document=new_account.dict(by_alias=True, exclude_none=True))
        account = await self.mongo.find_one_by_id(collection=collection_name, document_id=inserted)
        return AccountInDB(**account) if account else None