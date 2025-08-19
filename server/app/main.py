import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

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

    # setup mongo connection
    try:
        app.state.mongodb = Mongo(settings.mongo_uri, settings.mongo_db_name)
        mongo_connected = await app.state.mongodb.ping()
        if mongo_connected:
            logger.info("Successfully established connection to MongoDB")
            await create_indexes(app)
        else:
            raise RuntimeError("MongoDB connection failed")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {e}")
        raise

    # setup redis connection
    app.state.redis = None
    try:
        r = Redis(settings.redis_uri, db=0)
        connected = await r.connect()
        if not connected:
            raise RuntimeError("Redis connection failed")
        if not await r.ping():
            raise RuntimeError("Redis ping failed")
        app.state.redis = r
        logger.info("Successfully established connection to Redis")
    except Exception as e:
        logger.error(f"Redis connection failed: {e} - continuing without Redis")
        
    # setup esms
    if app.state.redis is not None:
        try:
            await init_esms(app.state.mongodb, app.state.redis)
            logger.info("Exercise Session Message Service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Exercise Session Message Service: {e}")
    
    # setup default roles/accounts
    if app.state.redis is not None and app.state.mongodb is not None and settings.environment == "dev":
        logger.info("Attempting to perform initial role and account setup")
        role_repo = RoleRepository(app.state.mongodb)
        account_repo = AccountRepository(app.state.mongodb, app.state.redis)
        await role_repo.perform_role_setup()
        await account_repo.perform_account_setup(role_repo)

    try:
        yield
    finally:
        logger.info("Shutting down application...")

        try:
            await cleanup_esms()
            logger.info("Cleaned up ESMS")
        except Exception as e:
            logger.error(f"Failed to clean up ESMS: {e}")

        try:
            if getattr(app.state, "mongodb", None):
                await app.state.mongodb.close()
                logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Failed to close MongoDB: {e}")

        try:
            if app.state.redis:    
                await app.state.redis.close()
                logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Failed to close Redis: {e}")

app = FastAPI(
    title="tc2",
    description="Core services used for Training Club",
    debug=settings.debug,
    lifespan=lifespan
)

app.include_router(AccountRouter, prefix="/account", tags=["account"])
app.include_router(AuthRouter, prefix="/auth", tags=["authentication"])
app.include_router(ExerciseSessionRouter, prefix="/session", tags=["exercise session"])
app.include_router(ExerciseSessionWebSocketRouter, prefix="/session/ws", tags=["exercise session socket"])
app.include_router(ExerciseRouter, prefix="/exercise", tags=["exercises"])

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
    logger.info("Created MongoDB indexes")
