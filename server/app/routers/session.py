from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer
from app.schema.messages.session import SessionOperationMessage
from pydantic import ValidationError
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
security = HTTPBearer()

@router.websocket("/channel")
async def session_channel(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            
            try:
                msg = SessionOperationMessage(**payload)
            except ValidationError as e:
                await websocket.send_json({"error": "invalid format", "details": e.errors()})
                continue
            
            logger.debug("session=%s account=%s data=%r", msg.session_id, msg.account_id, msg.data)
            
            await websocket.send_json({
                "status": "ok",
                "session_id": msg.session_id,
                "received_at": msg.timestamp
            })
    except WebSocketDisconnect:
        logger.info("Websocket Disconnected")