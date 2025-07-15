import logging
from fastapi import FastAPI
from app.db.mongo import Mongo
from app.routers.account import router as AccountRouter

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app = FastAPI(title="tc2")

app.include_router(
    AccountRouter,
    prefix="/account",
    tags=["account", "user"],
)

@app.on_event("startup")
async def on_startup():
    app.state.mongodb = Mongo("mongodb://0.0.0.0:55001", "tc2")
    ok = await app.state.mongodb.ping()
    if ok:
        logger.info("Successfully established a connection to MongoDB")
    else:
        logger.error("Could not establish a connection to MongoDB")

@app.on_event("shutdown")
async def on_shutdown():
    app.state.mongodb._client.close()
    logger.info("MongoDB connection has been closed")
