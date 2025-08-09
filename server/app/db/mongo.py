import logging
from typing import Any, Optional, Dict, List, Tuple, Union
from bson import CodecOptions, ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo.errors import PyMongoError
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class MongoError(Exception):
    """Custom exception for MongoDB operations"""
    pass

class Mongo:
    def __init__(self, uri: str, db_name: str, auto_convert_objectids: bool = True):
        logger.info("Initializing Mongo Instance")
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[db_name]
        self.auto_convert_objectids = auto_convert_objectids
    
    def _convert_objectids(self, obj: Any) -> Any:
        if not self.auto_convert_objectids:
            return obj
            
        if isinstance(obj, dict):
            return {k: self._convert_objectids(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_objectids(item) for item in obj]
        elif isinstance(obj, ObjectId):
            return str(obj)
        else:
            return obj
    
    def _prepare_filter(self, filter_dict: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not filter_dict:
            return {}
        
        prepared = filter_dict.copy()
        
        if '_id' in prepared and isinstance(prepared['_id'], str):
            if ObjectId.is_valid(prepared['_id']):
                prepared['_id'] = ObjectId(prepared['_id'])
        
        for operator in ['$or', '$and', '$nor']:
            if operator in prepared and isinstance(prepared[operator], list):
                prepared[operator] = [self._prepare_filter(item) for item in prepared[operator]]
        
        return prepared
    
    async def ping(self) -> bool:
        try:
            result = await self._client.admin.command("ping")
            logger.info("Ping to MongoDB Succeeded")
            return True
        except Exception as e:
            logger.error(f"Ping to MongoDB Failed: {e}")
            return False
    
    def get_collection(self, collection: str, codec_options: Optional[CodecOptions] = None) -> AsyncIOMotorCollection:
        return self.db.get_collection(collection, codec_options=codec_options)
    
    async def insert(self, collection: str, document: Dict[str, Any]) -> str:
        try:
            result = await self.db[collection].insert_one(document)
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"Insert failed for collection {collection}: {e}")
            raise MongoError(f"Insert operation failed: {e}") from e
    
    async def insert_many(self, collection: str, documents: List[Dict[str, Any]]) -> List[str]:
        try:
            result = await self.db[collection].insert_many(documents)
            return [str(id_) for id_ in result.inserted_ids]
        except PyMongoError as e:
            logger.error(f"Insert many failed for collection {collection}: {e}")
            raise MongoError(f"Insert many operation failed: {e}") from e
    
    async def find_one(
        self,
        collection: str,
        filter_dict: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        try:
            prepared_filter = self._prepare_filter(filter_dict)
            result = await self.db[collection].find_one(prepared_filter, projection)
            return self._convert_objectids(result) if result else None
        except PyMongoError as e:
            logger.error(f"Find one failed for collection {collection}: {e}")
            raise MongoError(f"Find one operation failed: {e}") from e
    
    async def find_many(
        self,
        collection: str,
        filter_dict: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Tuple[str, Union[int, str]]]] = None,
        skip: int = 0,
        limit: int = 0
    ) -> List[Dict[str, Any]]:
        try:
            prepared_filter = self._prepare_filter(filter_dict)
            cursor = self.db[collection].find(prepared_filter or {}, projection)
            
            if sort:
                cursor = cursor.sort(sort)
            if skip > 0:
                cursor = cursor.skip(skip)
            if limit > 0:
                cursor = cursor.limit(limit)
            
            results = await cursor.to_list(length=limit or None)
            return [self._convert_objectids(doc) for doc in results]
        except PyMongoError as e:
            logger.error(f"Find many failed for collection {collection}: {e}")
            raise MongoError(f"Find many operation failed: {e}") from e
    
    async def find_one_by_id(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        if not ObjectId.is_valid(document_id):
            logger.warning(f"Invalid ObjectId format: {document_id}")
            return None
        
        return await self.find_one(collection, {"_id": document_id})
    
    async def exists(self, collection: str, filter_dict: Dict[str, Any]) -> bool:
        try:
            prepared_filter = self._prepare_filter(filter_dict)
            result = await self.db[collection].find_one(prepared_filter, {"_id": 1})
            return result is not None
        except PyMongoError as e:
            logger.error(f"Exists check failed for collection {collection}: {e}")
            raise MongoError(f"Exists operation failed: {e}") from e
    
    async def update_one(
        self,
        collection: str,
        filter_dict: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False
    ) -> Dict[str, Any]:
        try:
            prepared_filter = self._prepare_filter(filter_dict)
            
            if not any(key.startswith('$') for key in update):
                update_doc = {'$set': update}
            else:
                update_doc = update

            result = await self.db[collection].update_one(
                prepared_filter,
                update_doc,
                upsert=upsert
            )
            
            return {
                'matched_count': result.matched_count,
                'modified_count': result.modified_count,
                'upserted_id': str(result.upserted_id) if result.upserted_id else None
            }
        except PyMongoError as e:
            logger.error(f"Update one failed for collection {collection}: {e}")
            raise MongoError(f"Update one operation failed: {e}") from e
    
    async def update_many(
        self,
        collection: str,
        filter_dict: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False
    ) -> Dict[str, Any]:
        try:
            prepared_filter = self._prepare_filter(filter_dict)
            
            if not any(key.startswith('$') for key in update):
                update_doc = {'$set': update}
            else:
                update_doc = update

            result = await self.db[collection].update_many(
                prepared_filter,
                update_doc,
                upsert=upsert
            )
            
            return {
                'matched_count': result.matched_count,
                'modified_count': result.modified_count,
                'upserted_id': str(result.upserted_id) if result.upserted_id else None
            }
        except PyMongoError as e:
            logger.error(f"Update many failed for collection {collection}: {e}")
            raise MongoError(f"Update many operation failed: {e}") from e
    
    async def update_by_id(
        self,
        collection: str,
        document_id: str,
        update: Dict[str, Any],
        upsert: bool = False
    ) -> Dict[str, Any]:
        if not ObjectId.is_valid(document_id):
            raise MongoError(f"Invalid ObjectId format: {document_id}")
        
        return await self.update_one(collection, {"_id": document_id}, update, upsert)
    
    async def replace_one(
        self,
        collection: str,
        filter_dict: Dict[str, Any],
        replacement: Dict[str, Any],
        upsert: bool = False
    ) -> Dict[str, Any]:
        try:
            prepared_filter = self._prepare_filter(filter_dict)
            result = await self.db[collection].replace_one(
                prepared_filter, replacement, upsert=upsert
            )
            return {
                'matched_count': result.matched_count,
                'modified_count': result.modified_count,
                'upserted_id': str(result.upserted_id) if result.upserted_id else None
            }
        except PyMongoError as e:
            logger.error(f"Replace one failed for collection {collection}: {e}")
            raise MongoError(f"Replace one operation failed: {e}") from e
    
    async def delete_one(self, collection: str, filter_dict: Dict[str, Any]) -> int:
        try:
            prepared_filter = self._prepare_filter(filter_dict)
            result = await self.db[collection].delete_one(prepared_filter)
            return result.deleted_count
        except PyMongoError as e:
            logger.error(f"Delete one failed for collection {collection}: {e}")
            raise MongoError(f"Delete one operation failed: {e}") from e

    async def delete_many(self, collection: str, filter_dict: Dict[str, Any]) -> int:
        try:
            prepared_filter = self._prepare_filter(filter_dict)
            result = await self.db[collection].delete_many(prepared_filter)
            return result.deleted_count
        except PyMongoError as e:
            logger.error(f"Delete many failed for collection {collection}: {e}")
            raise MongoError(f"Delete many operation failed: {e}") from e
    
    async def delete_by_id(self, collection: str, document_id: str) -> int:
        if not ObjectId.is_valid(document_id):
            raise MongoError(f"Invalid ObjectId format: {document_id}")
        
        return await self.delete_one(collection, {"_id": document_id})

    async def count_documents(self, collection: str, filter_dict: Optional[Dict[str, Any]] = None) -> int:
        try:
            prepared_filter = self._prepare_filter(filter_dict)
            return await self.db[collection].count_documents(prepared_filter or {})
        except PyMongoError as e:
            logger.error(f"Count documents failed for collection {collection}: {e}")
            raise MongoError(f"Count documents operation failed: {e}") from e
    
    async def aggregate(self, collection: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        try:
            cursor = self.db[collection].aggregate(pipeline)
            results = await cursor.to_list(length=None)
            return [self._convert_objectids(doc) for doc in results]
        except PyMongoError as e:
            logger.error(f"Aggregation failed for collection {collection}: {e}")
            raise MongoError(f"Aggregation operation failed: {e}") from e
    
    async def distinct(self, collection: str, field: str, filter_dict: Optional[Dict[str, Any]] = None) -> List[Any]:
        try:
            prepared_filter = self._prepare_filter(filter_dict)
            results = await self.db[collection].distinct(field, prepared_filter or {})
            return [self._convert_objectids(value) for value in results]
        except PyMongoError as e:
            logger.error(f"Distinct failed for collection {collection}: {e}")
            raise MongoError(f"Distinct operation failed: {e}") from e
    
    @asynccontextmanager
    async def transaction(self):
        async with await self._client.start_session() as session:
            async with session.start_transaction():
                yield session
    
    async def create_index(self, collection: str, keys: Union[str, List[Tuple[str, int]]], **kwargs):
        try:
            result = await self.db[collection].create_index(keys, **kwargs)
            logger.info(f"Index created on collection {collection}: {result}")
            return result
        except PyMongoError as e:
            logger.error(f"Create index failed for collection {collection}: {e}")
            raise MongoError(f"Create index operation failed: {e}") from e
    
    async def list_indexes(self, collection: str) -> List[Dict[str, Any]]:
        try:
            cursor = self.db[collection].list_indexes()
            return await cursor.to_list(length=None)
        except PyMongoError as e:
            logger.error(f"List indexes failed for collection {collection}: {e}")
            raise MongoError(f"List indexes operation failed: {e}") from e
    
    async def close(self):
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()