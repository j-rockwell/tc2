from json import JSONDecodeError, dumps, loads
from typing import Optional, Any, Dict
import redis.asyncio as aioredis
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Redis:
    def __init__(self, uri: str, db: int = 0):
        logger.info("Initializing Redis Instance")
        self.uri = uri
        self.db = db
        self._client: Optional[aioredis.Redis] = None
    
    async def connect(self) -> bool:
        try:
            self._client = aioredis.from_url(
                self.uri,
                db=self.db,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            return False
    
    async def ping(self) -> bool:
        assert self._client
        
        try:
            if not self._client:
                await self.connect()
            
            result = await self._client.ping()
            logger.info("Ping to Redis Succeeded")
            return result
        except Exception as e:
            logger.error(f"Ping to Redis Failed: {e}")
            return False
    
    def get_client(self) -> aioredis.Redis:
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            logger.info("Redis connection has been closed")
    
    async def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        assert self._client
        
        try:
            if isinstance(value, (dict, list)):
                value = dumps(value)
            
            result = await self._client.set(
                key, value, ex=ex, px=px, nx=nx, xx=xx
            )
            
            return result is not None
        except Exception as e:
            logger.error(f"Failed to set key {key}: {e}")
            return False
    
    async def get(self, key: str, decode_json: bool = False) -> Optional[Any]:
        assert self._client
        
        try:
            result = await self._client.get(key)
            if result is None:
                return None
            
            if decode_json:
                try:
                    return loads(result)
                except JSONDecodeError:
                    return result
            
            return result
        except Exception as e:
            logger.error(f"Failed to get key {key}: {e}")
            return None
    
    async def delete(self, *keys: str) -> int:
        assert self._client
        
        try:
            return await self._client.delete(*keys)
        except Exception as e:
            logger.error(f"Failed to delete keys {keys}: {e}")
            return 0
    
    async def exists(self, *keys: str) -> int:
        assert self._client
        
        try:
            return await self._client.exists(*keys)
        except Exception as e:
            logger.error(f"Failed to check key existence for {keys}: {e}")
            return 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        assert self._client
        
        try:
            return await self._client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Failed setting expiration for {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        assert self._client
        
        try:
            return await self._client.ttl(key)
        except Exception as e:
            logger.error(f"Failed getting TTL for key {key}: {e}")
            return -1
    
    async def setex(self, key: str, seconds: int, value: Any) -> bool:
        assert self._client
        
        try:
            if isinstance(value, (dict, list)):
                value = dumps(value)
            
            result = await self._client.setex(key, seconds, value)
            return result is not None
        except Exception as e:
            logger.error(f"Failed setting key {key} with expiration: {e}")
            return False
    
    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        assert self._client
        
        try:
            return await self._client.incr(key, amount)
        except Exception as e:
            logger.error(f"Failed incrementing key {key}: {e}")
            return None
    
    async def decr(self, key: str, amount: int = 1) -> Optional[int]:
        assert self._client
        
        try:
            return await self._client.decr(key, amount)
        except Exception as e:
            logger.error(f"Failed decrementing key {key}: {e}")
            return None
    
    async def flushdb(self) -> bool:
        assert self._client
        
        try:
            result = await self._client.flushdb()
            logger.info("Redis database flushed")
            return result
        except Exception as e:
            logger.error(f"Failed flushing database: {e}")
            return False
    
    async def info(self, section: Optional[str] = None) -> Dict[str, Any]:
        assert self._client
        
        try:
            return await self._client.info(section)
        except Exception as e:
            logger.error(f"Failed getting Redis info: {e}")
            return {}
    
    def pipeline(self, transaction: bool = True):
        assert self._client
        
        return self._client.pipeline(transaction=transaction)
    
    async def publish(self, channel: str, message: Any) -> int:
        assert self._client
        
        try:
            if isinstance(message, (dict, list)):
                message = dumps(message)
            
            return await self._client.publish(channel, message)
        except Exception as e:
            logger.error(f"Failed publishing to channel {channel}: {e}")
            return 0
    
    def pubsub(self):
        assert self._client
        return self._client.pubsub()
    
    async def lpush(self, key: str, *values: Any) -> int:
        assert self._client
        
        try:
            processed_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    processed_values.append(dumps(value))
                else:
                    processed_values.append(str(value))
            
            return await self._client.lpush(key, *processed_values) # type: ignore
        except Exception as e:
            logger.error(f"Failed left pushing to list {key}: {e}")
            return 0

    async def llen(self, key: str) -> int:
        assert self._client
        
        try:
            return await self._client.llen(key) # type: ignore
        except Exception as e:
            logger.error(f"Failed getting length of list {key}: {e}")
            return 0
    
    async def ltrim(self, key: str, start: int, end: int) -> bool:
        assert self._client
        
        try:
            result = await self._client.ltrim(key, start, end) # type: ignore
            return result is not None
        except Exception as e:
            logger.error(f"Failed trimming list {key}: {e}")
            return False
    
    async def sadd(self, key: str, *values: Any) -> int:
        assert self._client
        
        try:
            processed_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    processed_values.append(dumps(value))
                else:
                    processed_values.append(value)
            
            return await self._client.sadd(key, *processed_values) # type: ignore
        except Exception as e:
            logger.error(f"Failed adding to set {key}: {e}")
            return 0
    
    async def srem(self, key: str, *values: Any) -> int:
        assert self._client
        
        try:
            processed_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    processed_values.append(dumps(value))
                else:
                    processed_values.append(value)
            
            return await self._client.srem(key, *processed_values) # type: ignore
        except Exception as e:
            logger.error(f"Failed removing from set {key}: {e}")
            return 0
    
    async def smembers(self, key: str, decode_json: bool = False) -> set: # type: ignore
        assert self._client
        
        try:
            result = await self._client.smembers(key) # type: ignore
            if not decode_json:
                return result
            
            decoded_result = set()
            for value in result:
                try:
                    decoded_result.add(loads(value))
                except (JSONDecodeError, TypeError):
                    decoded_result.add(value)
            
            return decoded_result
        except Exception as e:
            logger.error(f"Failed getting set members from {key}: {e}")
            return set()