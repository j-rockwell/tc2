from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
import os

from app.db.mongo import Mongo
from app.db.redis import Redis
from app.routers.account import router as AccountRouter
from app.routers.auth import router as AuthRouter
from app.routers.exercise_session import router as ExerciseSessionRouter
from app.routers.exercise_session_ws import router as ExerciseSessionWebSocketRouter
from app.routers.exercise import router as ExerciseRouter
from app.routers.exercise_session_ws import init_esms, cleanup_esms
from app.config import settings
from app.repos.perm import RoleRepository
from app.repos.account import AccountRepository

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting in {settings.environment} mode")

    # establish connections
    await _prepare_db(app)
    await _prepare_redis(app)
    
    # force shutdown if connections are not established
    if app.state.mongodb is None or app.state.redis is None:
        logger.fatal("Failed to establish necessary connections. Shutting down application.")
        os.kill(os.getpid(), 1)
    
    await _prepare_dev_data(app)
    await _prepare_esms(app)

    try:
        yield
    finally:
        logger.info("Shutting down application...")
        
        await _close_esms()
        await _close_db(app)
        await _close_redis(app)

async def _prepare_db(app: FastAPI):
    try:
        app.state.mongodb = Mongo(settings.mongo_uri, settings.mongo_db_name, auto_convert_objectids=True)
        connected = await app.state.mongodb.ping()
        if connected:
            logger.info("Successfully established a connection to the database. Now attempting to create database indexes...")
            await create_indexes(app)
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

async def _prepare_redis(app: FastAPI):
    try:
        redis = Redis(settings.redis_uri, db=0)
        connected = await redis.connect()
        if not connected:
            raise RuntimeError("Failed to initialize redis: connection failed")
        if not await redis.ping():
            raise RuntimeError("Failed to initialize redis: ping failed")
        app.state.redis = redis
        logger.info("Successfully established a connection to Redis")
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e} ")
        app.state.redis = None

async def _prepare_esms(app: FastAPI):
    try:
        if app.state.redis is None:
            raise RuntimeError("Failed to initialize ESMS: redis connection is not established")
        
        await init_esms(app.state.mongodb, app.state.redis)
        logger.info("Successfully initialized Exercise Session Message Service (ESMS)")
    except Exception as e:
        logger.error(f"Failed to initialize ESMS: {e}")
        app.state.redis = None

async def _prepare_dev_data(app: FastAPI):
    logger.info("Preparing to generate dev environment data...")
    
    if settings.environment != "dev":
        logger.info("Skipping dev data preparation")
    
    if app.state.redis is None or app.state.mongodb is None:
        raise RuntimeError("Failed to prepare dev data: Redis or MongoDB connection is not established")
    
    role_repo = RoleRepository(app.state.mongodb)
    account_repo = AccountRepository(app.state.mongodb, app.state.redis)
    await role_repo.perform_role_setup()
    await account_repo.perform_account_setup(role_repo)

async def _close_db(app: FastAPI):
    try:
        if getattr(app.state, "mongodb", None):
            await app.state.mongodb.close()
            logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"Failed to close MongoDB: {e}")

async def _close_redis(app: FastAPI):
    try:
        if getattr(app.state, "redis", None):
            await app.state.redis.close()
            logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Failed to close Redis: {e}")

async def _close_esms():
    try:
        await cleanup_esms()
        logger.info("Cleaned up ESMS data")
    except Exception as e:
        logger.error(f"Failed to close ESMS: {e}")

app = FastAPI(
    title="tc2",
    description="Core services used for Training Club",
    debug=settings.debug,
    lifespan=lifespan
)

app.include_router(AccountRouter, prefix="/account", tags=["account"])
app.include_router(AuthRouter, prefix="/auth", tags=["authentication"])
app.include_router(ExerciseRouter, prefix="/exercise", tags=["exercises"])
app.include_router(ExerciseSessionRouter, prefix="/session", tags=["exercise session"])
app.include_router(ExerciseSessionWebSocketRouter, prefix="/session/ws", tags=["exercise session socket"])

async def create_indexes(app: FastAPI):
    await app.state.mongodb.db.accounts.create_index("email", unique=True)
    await app.state.mongodb.db.accounts.create_index("username", unique=True)
    await app.state.mongodb.db.exercise_sessions.create_index("owner_id")
    await app.state.mongodb.db.exercise_sessions.create_index("participants.id")
    await app.state.mongodb.db.exercise_sessions.create_index("status")
    await app.state.mongodb.db.exercise_sessions.create_index([("status", 1), ("owner_id", 1)])
    await app.state.mongodb.db.exercise_sessions.create_index([("status", 1), ("participants.id", 1)])
    await app.state.mongodb.db.exercise_sessions.create_index([("updated_at", -1)])
    await app.state.mongodb.db.exercise_sessions.create_index("invitations.invited")
    logger.info("Finished creating database indexes")
