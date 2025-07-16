import logging
from fastapi import FastAPI
from app.db.mongo import Mongo
from app.routers.account import router as AccountRouter
from app.config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app = FastAPI(
    title="tc2",
    debug=settings.debug
)

app.include_router(
    AccountRouter,
    prefix="/account",
    tags=["account", "user"],
)

async def create_indexes():
    await app.state.mongodb.db.accounts.create_index("email", unique=True)
    await app.state.mongodb.db.accounts.create_index("username", unique=True)

@app.on_event("startup")
async def on_startup():
    app.state.mongodb = Mongo(settings.mongo_uri, settings.mongo_db_name)
    ok = await app.state.mongodb.ping()
    if ok:
        logger.info("Successfully established a connection to MongoDB")
        await create_indexes()
    else:
        logger.error("Could not establish a connection to MongoDB")

@app.on_event("shutdown")
async def on_shutdown():
    app.state.mongodb._client.close()
    logger.info("MongoDB connection has been closed")
