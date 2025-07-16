from fastapi import Request, HTTPException, status, Cookie, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from app.db.mongo import Mongo
from app.db.redis import Redis
from app.util.token import Tokenizer

security = HTTPBearer(auto_error=False)

def get_mongo(req: Request) -> Mongo:
    return req.app.state.mongodb

def get_redis(req: Request) -> Redis:
    return req.app.state.redis

async def read_request_account_id(
    db: Mongo = Depends(get_mongo),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token: Optional[str] = Cookie(None)
) -> Dict[str, Any]:
    token = None
    if credentials:
        token = credentials.credentials
    elif access_token:
        token = access_token
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW_Authenticate": "Bearer"}
        )
    
    payload = Tokenizer.decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate", "Bearer"}
        )
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    id = payload.get("sub")
    if not id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    from bson import ObjectId
    try:
        account = await db.find_one("accounts", {"_id": ObjectId(id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid account ID"
        )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found"
        )
    
    return account

async def read_request_account_id_optional(
    db: Mongo = Depends(get_mongo),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token: Optional[str] = Cookie(None)
) -> Optional[Dict[str, Any]]:
    try:
        return await read_request_account_id(db, credentials, access_token)
    except HTTPException:
        return None