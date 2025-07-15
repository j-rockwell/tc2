from fastapi import Request
from app.db.mongo import Mongo

def get_mongo(req: Request) -> Mongo:
    return req.app.state.mongodb