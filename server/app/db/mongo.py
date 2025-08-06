import logging
from typing import Any, Optional, Dict, List, Tuple, Union
from bson import CodecOptions
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Mongo:
    def __init__(self, uri: str, db_name: str):
        logger.info("Initializing Mongo Instance")
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[db_name]
    
    async def ping(self) -> bool:
        try:
            result = await self._client.admin.command("ping")
            logger.info("Ping to MongoDB Succeeded")
            return True
        except Exception as e:
            logger.error("Ping to MongoDB Failed")
            return False
    
    def get_collection(self, collection: str, codec_options: Optional[CodecOptions] = None) -> AsyncIOMotorCollection:
        return self.db.get_collection(collection, codec_options=codec_options)
    
    async def insert(self, collection: str, document: Any) -> Any:
        result = await self.db[collection].insert_one(document)
        return result.inserted_id
    
    async def find_one(
        self,
        collection: str,
        filter: Dict[str, Any] | None = None,
        projection: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        return await self.db[collection].find_one(filter, projection)
    
    async def find_many(
        self,
        collection: str,
        filter: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Tuple[str, Union[int, str]]]] = None,
        skip: int = 0,
        limit: int = 0
    ) -> List[Dict[str, Any]]:
        cursor = self.db[collection].find(filter, projection)
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return await cursor.to_list(length=limit or 100)
    
    async def update_one(
        self,
        collection: str,
        filter: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False
    ) -> Dict[str, Any]:
        if any(key.startswith('$') for key in update):
            update_doc = update
        else:
            update_doc = {'$set': update}

        result = await self.db[collection].update_one(
            filter,
            update_doc,
            upsert=upsert
        )
        
        return {
            'matched_count': result.matched_count,
            'modified_count': result.modified_count,
            'upserted_id': result.upserted_id
        }

    
    async def replace_one(
        self,
        collection: str,
        filter: Dict[str, Any],
        replacement: Dict[str, Any],
        upsert: bool = False
    ) -> Dict[str, Any]:
        result = await self.db[collection].replace_one(
            filter, replacement, upsert=upsert
        )
        return {
            'matched_count': result.matched_count,
            'modified_count': result.modified_count,
            'upserted_id': result.upserted_id
        }
    
    async def delete_one(self, collection: str, filter: Dict[str, Any]) -> int:
        result = await self.db[collection].delete_one(filter)
        return result.deleted_count

    async def delete_many(self, collection: str, filter: Dict[str, Any]) -> int:
        result = await self.db[collection].delete_many(filter)
        return result.deleted_count

    async def count_documents(self, collection: str, filter: Dict[str, Any]) -> int:
        return await self.db[collection].count_documents(filter)