from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status, Depends
from typing import Optional, Dict, Any
import logging
import json

from app.repos.exercise_session import ExerciseSessionRepository
from app.schema.exercise_session import ExerciseSessionStatus
from app.services.exercise_session_service_v2 import ESMService, ExerciseSessionOperation, ExerciseSessionOperationType
from app.db.mongo import Mongo
from app.db.redis import Redis
from app.deps import get_ws_mongo, get_ws_redis, read_ws_account_id

router = APIRouter()
logger = logging.getLogger(__name__)

_esms: Optional[ESMService] = None
def get_esms() -> ESMService:
    global _esms
    if _esms is None:
        raise RuntimeError("ESMService is not initialized.")
    return _esms

async def init_esms(db, redis) -> None:
    global _esms
    _esms = ESMService(db, redis)
    await _esms.start()
    _esms.register_default_handlers()
    logger.info("Exercise Session Message Service (ESMS) initialized")

async def cleanup_esms():
    global _esms
    if _esms:
        await _esms.stop()
        _esms = None
    logger.info("Exercise Session Message Service (ESMS) stopped and cleaned up")

@router.get(
    "/stats",
    summary="Get statistics related to the exercise session websocket connection"
)
async def ws_stats():
    if _esms is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="esms not initialized")
    stats = _esms.get_stats()
    return { "stats": stats }

@router.websocket("/")
async def ws_endpoint(
    websocket: WebSocket,
    current_user: Dict[str, Any] = Depends(read_ws_account_id),
    db: Mongo = Depends(get_ws_mongo),
    redis: Redis = Depends(get_ws_redis)
):
    service = get_esms()
    connection_id: Optional[str] = None
    
    account_id = current_user["id"]
    if not account_id:
        await websocket.close(code=4000, reason="Missing account_id")
        return
    
    try:
        await websocket.accept()
        
        repo = ExerciseSessionRepository(db, redis)
        
        session = await repo.get_active_session_by_user(account_id)
        if not session:
            await websocket.close(code=4000, reason="No active session found")
            return
        elif not session.id:
            await websocket.close(code=4001, reason="Session ID is missing")
            return
        elif not session.status == ExerciseSessionStatus.ACTIVE:
            await websocket.close(code=4002, reason="Session is not active")
            return
        
        connection_id = await service.open_connection(websocket, account_id, session.id)
        
        while True:
            try:
                raw = await websocket.receive_text()
                try:
                    payload = json.loads(raw)
                    if "op_type" not in payload:
                        raise ValueError("missing type")
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Failed to read payload: {e}")
                    logger.error(f"received payload: {raw}")
                    continue
                
                await service.handle_client_op(connection_id, payload)
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected for account: %s", account_id)
                break
            except Exception:
                logger.error("Error processing WebSocket message")
    except Exception as e:
        logger.error(f"WebSocket accept failed: {e}")
        return
    finally:
        if connection_id:
            await service.close_connection(connection_id=connection_id)