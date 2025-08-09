from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from bson import ObjectId
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from app.schema.session import ExerciseSession, ExerciseSessionStatus, ExerciseSessionInvite, ExerciseSessionInDB, ExerciseSessionParticipant, ExerciseSessionParticipantCursor
from app.models.responses.session import SessionCreateResponse, SessionInviteAcceptResponse, SessionQueryResponse
from app.models.requests.session import SessionInviteRequest, SessionInviteAcceptRequest
from app.models.responses.base import ErrorResponse
from app.db.mongo import Mongo
from app.db.redis import Redis
from app.deps import get_mongo, read_request_account_id

# SOCKET
# /channel          - Access to communication channel for exercise sessions
#
# GET
# /me?query=        - Search for exercise sessions specific to the querying user
# /search?query=    - Search for exercise sessions by query params
# /state/me         - Get session state to the querying user
# /state/:id        - Get all session states for a specific session
#
# POST
# /                 - Create a new session
# /invite           - Invite a user to your current active session
# /invite/accept    - Accept an invitation to join an active session
# /invite/decline   - Decline an invitation to join an active session
#
# DELETE
# /:id              - Delete an exercise session if you have access to it

router = APIRouter()
logger = logging.getLogger(__name__)
security = HTTPBearer()

exercise_sessions_key = "exercise_sessions"

@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=SessionQueryResponse,
)
async def get_own_session(
    status_: Optional[ExerciseSessionStatus] = None,
    limit: int = 20,
    skip: int = 0,
    current_user: Dict[str, Any] = Depends(read_request_account_id),
    db: Mongo = Depends(get_mongo),
) -> SessionQueryResponse:
    try:
        account_id = current_user["id"]
        filter: Dict[str, Any] = {
            "$or": [{"owner_id": account_id}, {"participants.id": account_id}]
        }
        if status_:
            filter["status"] = status_.value

        items = await db.find_many(
            exercise_sessions_key,
            filter,
            sort=[("updated_at", -1), ("_id", -1)],
            skip=skip,
            limit=min(max(limit, 1), 50),
        )

        if not items:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No sessions found")

        return SessionQueryResponse(data=[ExerciseSessionInDB(**i) for i in items])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch own sessions: {e}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")



@router.get(
    "/search",
    status_code=status.HTTP_200_OK,
    response_model=SessionQueryResponse,
)
async def get_sessions(
    participant_id: Optional[str] = None,
    status_: Optional[ExerciseSessionStatus] = None,
    limit: int = 20,
    skip: int = 0,
    db: Mongo = Depends(get_mongo),
) -> SessionQueryResponse:
    try:
        filter: Dict[str, Any] = {}
        if participant_id:
            filter["$or"] = [
                {"owner_id": participant_id},
                {"participants.id": participant_id},
            ]
        if status_:
            filter["status"] = status_.value

        items = await db.find_many(
            exercise_sessions_key,
            filter,
            sort=[("updated_at", -1), ("_id", -1)],
            skip=skip,
            limit=min(max(limit, 1), 50),
        )

        if not items:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No sessions found")

        return SessionQueryResponse(data=[ExerciseSessionInDB(**i) for i in items])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform session query: {e}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")



@router.get(
    "/state/me"
)
async def get_own_state():
    pass



@router.get(
    "/state/{identifier}"
)
async def get_state():
    pass



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
        
        await db.insert("exercise_sessions", created_session.dict(by_alias=True, exclude_none=True))
        
        res = SessionCreateResponse(session=created_session)
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



@router.post(
    "/invite/accept",
    status_code=status.HTTP_200_OK,
    responses={
        409: {"model": ErrorResponse, "description": "User already has an active session"},
        404: {"model": ErrorResponse, "description": "Session or invitation to session not found"},
    }
)
async def accept_session_invite(
    req: SessionInviteAcceptRequest,
    current_user: Dict[str, Any] = Depends(read_request_account_id),
    db: Mongo = Depends(get_mongo)
) -> SessionInviteAcceptResponse:
    try:
        account_id = current_user["id"]
        session_id = req.session_id
        
        # check if user has an active session first
        conflict = await db.find_one(
            exercise_sessions_key,
            {
                "status": ExerciseSessionStatus.ACTIVE.value,
                "$or": [
                    { "owner_id": session_id },
                    { "participants.id": account_id }
                ]
            }
        )
        if conflict:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="You already have an active exercise session")
        
        # get session attached to the invitation they are trying to accept
        found_session = await db.find_one(
            exercise_sessions_key,
            {
                "_id": ObjectId(session_id),
                "status": ExerciseSessionStatus.ACTIVE.value
            }
        )
        if not found_session:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Exercise session not found")
        
        session = ExerciseSessionInDB(**found_session)
        
        # check if user is invited to the session
        if not any(inv.invited_id == account_id for inv in session.invites):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No invitation found for account")
        
        new_participant = ExerciseSessionParticipant(
            id=account_id,
            color="#FFFFFF",
        )
        
        update_result = await db.update_one(
            exercise_sessions_key,
            { "_id": ObjectId(session_id) },
            {
                "$push": {"participants": new_participant.dict()},
                "$pull": {"invites": {"invited_id": account_id}},
                "$set":  {"updated_at": datetime.utcnow()}
            }
        )
        
        if update_result["modified_count"] != 1:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to accept the invitation"
            )
        
        res = SessionInviteAcceptResponse(
            session=session,
            participant=new_participant
        )
        
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to accept session invitation: {e}")


@router.delete(
    "/delete/{identifier}",
    status_code=status.HTTP_200_OK,
)
async def decline_session_invite():
    pass