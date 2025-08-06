from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status, Response, Depends
from fastapi.security import HTTPBearer
from pydantic import ValidationError
from bson import ObjectId
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.schema.messages.session import SessionOperationMessage
from app.schema.session import ExerciseSession, ExerciseSessionStatus, ExerciseSessionInvite, ExerciseSessionInDB, ExerciseSessionParticipant, ExerciseSessionParticipantCursor
from app.models.responses.session import SessionCreateResponse
from app.models.requests.session import SessionInviteRequest
from app.models.responses.base import ErrorResponse
from app.db.mongo import Mongo
from app.db.redis import Redis
from app.deps import get_mongo, read_request_account_id
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
security = HTTPBearer()

exercise_sessions_key = "exercise_sessions"

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


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new exercise session",
    responses={
        409: {"model": ErrorResponse, "description": "Active user session already exists"},
    }
)
async def create_session(
    current_user: Dict[str, Any] = Depends(read_request_account_id),
    db: Mongo = Depends(get_mongo),
) -> SessionCreateResponse:
    try:
        account_id = current_user["id"]
        filter_ = {
            "status": ExerciseSessionStatus.ACTIVE.value,
            "$or": [
                { "owner_id": account_id },
                { "participants.id": account_id }
            ]
        }
        
        if await db.find_one("exercise_sessions", filter_):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have an active session in-progress"
            )
        
        created_session = ExerciseSession(
            owner_id=account_id,
            status=ExerciseSessionStatus.ACTIVE,
            participants=[
                ExerciseSessionParticipant(
                    id=account_id,
                    color='#FFFFFF',
                    cursor=None
                )
            ]
        )
        
        inserted = await db.insert("exercise_sessions", created_session.dict(by_alias=True, exclude_none=True))
        session_id = str(inserted)
        
        res = SessionCreateResponse(
            id=session_id
        )
        
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post(
    "/invite",
    status_code=status.HTTP_201_CREATED,
)
async def send_session_invite(
    req: SessionInviteRequest,
    current_user: Dict[str, Any] = Depends(read_request_account_id),
    db: Mongo = Depends(get_mongo)
):
    try:
        account_id = current_user["id"]
        invited_account_id = req.account_id
        
        # TODO: Friend check here - user should not be able to invite anyone
        
        if account_id == invited_account_id:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="You can not invite yourself to the session")
        
        invited_account = await db.find_one("accounts", { "_id": ObjectId(invited_account_id) })
        if not invited_account:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Invited account not found")
        
        found_session = await db.find_one(
            exercise_sessions_key,
            {
                "status": ExerciseSessionStatus.ACTIVE.value,
                "owner_id": account_id
            }
        )
        if not found_session:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Exercise session not found")
        
        session = ExerciseSessionInDB(**found_session)
        
        if len(session.participants) >= 4:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Session is full")
        
        if any(p.id == invited_account_id for p in session.participants):
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Account is already a participant")
        
        if any(inv.invited_id == invited_account_id for inv in session.invites):
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Account has already been invited")
        
        new_invite = ExerciseSessionInvite(
            invited_id=invited_account_id,
            invited_by=account_id
        )
        
        update_result = await db.update_one(
            "exercise_sessions",
            {"_id": found_session["_id"]},
            {
                "$push": {"invites": new_invite.dict()},
                "$set":  {"updated_at": datetime.utcnow()}
            }
        )
        
        if update_result["modified_count"] != 1:
            raise RuntimeError("Database update did not modify any document")
        
        return new_invite
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send session invitation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")