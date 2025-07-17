import logging
from fastapi import FastAPI
from app.db.mongo import Mongo
from app.db.redis import Redis
from app.routers.account import router as AccountRouter
from app.routers.auth import router as AuthRouter
from app.config import settings

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="tc2",
    debug=settings.debug
)

app.include_router(
    AccountRouter,
    prefix="/account",
    tags=["account", "user"],
)

app.include_router(
    AuthRouter,
    prefix="/auth",
    tags="auth, authentication"
)

async def create_indexes():
    await app.state.mongodb.db.accounts.create_index("email", unique=True)
    await app.state.mongodb.db.accounts.create_index("username", unique=True)

@app.on_event("startup")
async def on_startup():
    logger.info(f"Starting in {settings.environment} mode")
    
    try:
        app.state.mongodb = Mongo(settings.mongo_uri, settings.mongo_db_name)
        mongo_connected = await app.state.mongodb.ping()
        
        if mongo_connected:
            logger.info("Successfully established connection to MongoDB")
            await create_indexes()
        else:
            logger.error("Failed to establish connection to MongoDB")
            raise Exception("MongoDB connection failed")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {e}")
        raise
    
    try:
        app.state.redis = Redis(settings.redis_uri, db=0)
        
        redis_connected = await app.state.redis.connect()
        if not redis_connected:
            raise Exception("Redis connection failed")
        
        ping_result = await app.state.redis.ping()
        if ping_result:
            logger.info("Successfully established connection to Redis")
        else:
            logger.error("Redis ping failed")
            raise Exception("Redis ping failed")
            
    except Exception as e:
        logger.error(f"Redis connection failed: {e} - continuing without Redis")
        app.state.redis = None

@app.on_event("shutdown")
async def on_shutdown():
    if hasattr(app.state, 'mongodb'):
        app.state.mongodb._client.close()
        logger.info("MongoDB connection closed")
    
    if hasattr(app.state, 'redis'):
        app.state.redis.close()
        logger.info("Redis connection closed")
