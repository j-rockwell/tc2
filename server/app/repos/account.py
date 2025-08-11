from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from app.db.redis import Redis
from app.db.mongo import Mongo
from app.schema.account import AccountInDB
from app.util.hash import Hasher

collection_name = "accounts"

class AccountRepository:
    def __init__(self, mongo: Mongo, redis: Redis):
        self.mongo = mongo
        self.redis = redis
    
    async def get_account_by_id(self, account_id: str) -> Optional[AccountInDB]:
        account = await self.mongo.find_one_by_id(collection=collection_name, document_id=account_id)   
        return AccountInDB(**account) if account else None
    
    async def get_account_by_key_value(self, key: str, value: str) -> Optional[AccountInDB]:
        account = await self.mongo.find_one(collection=collection_name, filter_dict={key: value})
        return AccountInDB(**account) if account else None
    
    async def get_many_accounts_by_filter(self, filter: Dict[str, Any]) -> List[AccountInDB]:
        query = await self.mongo.find_many(collection=collection_name, filter_dict=filter)
        return [AccountInDB(**q) for q in (query or [])]
    
    async def create_account(self, username: str, email: str, password: str) -> Optional[AccountInDB]:
        pwd = Hasher.make(password)
        now = datetime.now(timezone.utc)
        
        doc = {
            "email": email,
            "username": username,
            "password": pwd,
            "metadata": {
                "email_confirmed": False,
                "created_at": now,
                "last_active": now
            }
        }
        
        inserted = await self.mongo.insert(collection=collection_name, document=doc)
        account = await self.mongo.find_one_by_id(collection=collection_name, document_id=inserted)
        return AccountInDB(**account) if account else None
    