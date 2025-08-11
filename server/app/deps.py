from bson import ObjectId
from fastapi import Request, WebSocket, HTTPException, status, Request, WebSocketException, Cookie, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from app.db.mongo import Mongo
from app.db.redis import Redis
from app.util.token import Tokenizer
from app.util.session import Sessions, SessionSecurity
from app.util.session import get_client_info

security = HTTPBearer(auto_error=False)

def get_mongo(req: Request) -> Mongo:
    return req.app.state.mongodb

def get_redis(req: Request) -> Redis:
    return req.app.state.redis

def get_ws_mongo(websocket: WebSocket) -> Mongo:
    return websocket.app.state.mongodb

def get_ws_redis(websocket: WebSocket) -> Redis:
    return websocket.app.state.redis

async def read_request_account_id(
    request: Request,
    db: Mongo = Depends(get_mongo),
    redis: Redis = Depends(get_redis),
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
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    payload = Tokenizer.decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    account_id = payload.get("sub")
    if not account_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not await Sessions.is_valid(redis, account_id, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid"
        )
    
    client_info = get_client_info(request)
    
    security_check = await SessionSecurity.detect_suspicious(
        redis, account_id, client_info["ip"], client_info["user_agent"]
    )
    
    if security_check["score"] > 70:
        await SessionSecurity.log_event(
            redis, account_id, "high_suspicion_access",
            security_check, client_info["ip"]
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Additional verification required",
            headers={"X-Challenge-Required": "true"}
        )
    
    await Sessions.update(redis, account_id, "access", client_info["ip"])
    
    user_cache_key = f"user:{account_id}"
    cached_user = await redis.get(user_cache_key, decode_json=True)
    
    if cached_user:
        return {
            "id": cached_user["id"],
            "username": cached_user["username"],
            "email": cached_user["email"],
            "email_confirmed": cached_user.get("email_confirmed", False)
        }
    
    try:
        account = await db.find_one("accounts", {"_id": ObjectId(account_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid account ID"
        )
    
    if not account:
        await Sessions.invalidate(redis, account_id, "access")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found"
        )
    
    user_data = {
        "id": str(account["_id"]),
        "username": account["username"],
        "email": account["email"],
        "email_confirmed": account.get("metadata", {}).get("email_confirmed", False)
    }
    await redis.setex(user_cache_key, 3600, user_data)
    
    return user_data

async def read_request_account_id_optional(
    request: Request,
    db: Mongo = Depends(get_mongo),
    redis: Redis = Depends(get_redis),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token: Optional[str] = Cookie(None)
) -> Optional[Dict[str, Any]]:
    try:
        return await read_request_account_id(request, db, redis, credentials, access_token)
    except HTTPException:
        return None

async def read_ws_account_id(
    websocket: WebSocket,
    db: Mongo           = Depends(get_ws_mongo),
    redis: Redis        = Depends(get_ws_redis),
    access_token: Optional[str] = Cookie(None),
) -> Dict[str, Any]:
    auth: Optional[str] = websocket.headers.get("authorization")
    token = None
    if auth and auth.startswith("Bearer "):
        token = auth.removeprefix("Bearer ").strip()
    elif access_token:
        token = access_token

    if not token:
        await websocket.close(code=1008)
        raise WebSocketException(code=1008)

    payload = Tokenizer.decode_access_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=1008)
        raise WebSocketException(code=1008)

    account_id = payload.get("sub")
    if not account_id:
        await websocket.close(code=1008)
        raise WebSocketException(code=1008)

    if not await Sessions.is_valid(redis, account_id, "access"):
        await websocket.close(code=1008)
        raise WebSocketException(code=1008)

    user_cache_key = f"user:{account_id}"
    user_data      = await redis.get(user_cache_key, decode_json=True)
    if not user_data:
        acct = await db.find_one("accounts", {"_id": ObjectId(account_id)})
        if not acct:
            await Sessions.invalidate(redis, account_id, "access")
            await websocket.close(code=1008)
            raise WebSocketException(code=1008)
        user_data = {
            "id":      str(acct["_id"]),
            "username": acct["username"],
            "email":    acct["email"],
            "email_confirmed": acct.get("metadata", {}).get("email_confirmed", False)
        }
        await redis.setex(user_cache_key, 3600, user_data)

    return user_data