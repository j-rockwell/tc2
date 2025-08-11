from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging
import json

from app.services.exercise_session_service import (
    ExerciseSessionMessageService,
    ExerciseSessionOperationType,
    ExerciseSessionOperation,
)
from app.repos.exercise_session import ExerciseSessionRepository
from app.schema.exercise_session import (
    ExerciseSessionParticipantCursor,
    ExerciseSessionStateItem,
    ExerciseSessionItemMeta,
    ExerciseSessionStateItemMetric,
    ExerciseSessionStateItemSet,
)
from app.db.mongo import Mongo
from app.db.redis import Redis
from app.deps import read_ws_account_id, get_ws_mongo, get_ws_redis

router = APIRouter()
logger = logging.getLogger(__name__)

# global instance set during app startup
_esms: Optional[ExerciseSessionMessageService] = None

def get_esms() -> ExerciseSessionMessageService:
    if not _esms:
        raise RuntimeError("Exercise Session Message Service not initialized")
    return _esms

def _make_op(
    *,
    type_: ExerciseSessionOperationType,
    session_id: str,
    account_id: str,
    payload: Dict[str, Any],
    op_id: Optional[str] = None,
    version: int = 0,
    correlation_id: Optional[str] = None,
) -> ExerciseSessionOperation:
    return ExerciseSessionOperation(
        id=op_id or str(uuid4()),
        type=type_,
        session_id=session_id,
        account_id=account_id,
        payload=payload,
        timestamp=datetime.now(timezone.utc),
        version=version,
        correlation_id=correlation_id,
    )

async def _send_error(
    service: ExerciseSessionMessageService,
    connection_id: str,
    account_id: str,
    error_msg: str,
    correlation_id: Optional[str] = None,
) -> None:
    await service.send_to_connection(
        connection_id,
        _make_op(
            type_=ExerciseSessionOperationType.SESSION_UPDATE,
            session_id="",
            account_id=account_id,
            payload={"error": error_msg, "error_type": "client_error"},
            correlation_id=correlation_id,
        ),
    )


async def register_esms_handlers(esms: ExerciseSessionMessageService, mongo: Mongo, redis: Redis) -> None:
    repo = ExerciseSessionRepository(mongo, redis)

    async def handle_session_join(op: ExerciseSessionOperation, conn_id: str):
        session_id = op.payload.get("session_id")
        if not session_id:
            await _send_error(esms, conn_id, op.account_id, "session_id required", op.id)
            return

        session = await repo.get_session_by_id(session_id)
        if not session:
            await _send_error(esms, conn_id, op.account_id, "Session not found", op.id)
            return

        if session.owner_id != op.account_id and not any(p.id == op.account_id for p in session.participants):
            await _send_error(esms, conn_id, op.account_id, "Access denied", op.id)
            return

        await esms.join_session(conn_id, session_id)

        state = await repo.get_active_session_state_by_user(op.account_id) or await repo.create_session_state(
            session_id, op.account_id
        )
        if state:
            await esms.send_to_connection(
                conn_id,
                _make_op(
                    type_=ExerciseSessionOperationType.SESSION_SYNC,
                    session_id=session_id,
                    account_id=op.account_id,
                    payload={"state": state.dict()},
                    version=state.version,
                    correlation_id=op.id,
                ),
            )

    async def handle_session_leave(op: ExerciseSessionOperation, conn_id: str):
        await esms.leave_session(conn_id)

    async def handle_exercise_add(op: ExerciseSessionOperation, conn_id: str):
        if not op.session_id:
            await _send_error(esms, conn_id, op.account_id, "Not in a session", op.id)
            return
        state = await repo.get_active_session_state_by_user(op.account_id)
        if not state:
            await _send_error(esms, conn_id, op.account_id, "No active state", op.id)
            return

        exercise = op.payload.get("exercise", {})
        new_item = ExerciseSessionStateItem(
            id=str(uuid4()),
            order=len(state.items) + 1,
            participants=[op.account_id],
            type=exercise.get("type", "single"),
            rest=exercise.get("rest", 90),
            meta=[ExerciseSessionItemMeta(**m) for m in exercise.get("meta", [])],
            sets=[],
        )
        state.items.append(new_item)
        state.version += 1
        await repo.update_session_state(state)

        op.payload = {"exercise": new_item.dict(), "version": state.version}
        op.version = state.version

    async def handle_exercise_update(op: ExerciseSessionOperation, conn_id: str):
        if not op.session_id:
            await _send_error(esms, conn_id, op.account_id, "Not in a session", op.id)
            return
        exercise_id = op.payload.get("exercise_id")
        if not exercise_id:
            await _send_error(esms, conn_id, op.account_id, "exercise_id required", op.id)
            return

        state = await repo.get_active_session_state_by_user(op.account_id)
        if not state:
            await _send_error(esms, conn_id, op.account_id, "No active state", op.id)
            return

        updates = op.payload.get("updates", {})
        for item in state.items:
            if item.id == exercise_id:
                for k, v in updates.items():
                    if hasattr(item, k):
                        setattr(item, k, v)
                break
        else:
            await _send_error(esms, conn_id, op.account_id, "Exercise not found", op.id)
            return

        state.version += 1
        await repo.update_session_state(state)
        op.version = state.version
        op.payload["version"] = state.version

    async def handle_exercise_delete(op: ExerciseSessionOperation, conn_id: str):
        if not op.session_id:
            await _send_error(esms, conn_id, op.account_id, "Not in a session", op.id)
            return
        exercise_id = op.payload.get("exercise_id")
        if not exercise_id:
            await _send_error(esms, conn_id, op.account_id, "exercise_id required", op.id)
            return

        state = await repo.get_active_session_state_by_user(op.account_id)
        if not state:
            await _send_error(esms, conn_id, op.account_id, "No active state", op.id)
            return

        before = len(state.items)
        state.items = [it for it in state.items if it.id != exercise_id]
        if len(state.items) == before:
            await _send_error(esms, conn_id, op.account_id, "Exercise not found", op.id)
            return

        for i, it in enumerate(state.items, 1):
            it.order = i

        state.version += 1
        await repo.update_session_state(state)
        op.version = state.version
        op.payload["version"] = state.version

    async def handle_set_add(op: ExerciseSessionOperation, conn_id: str):
        if not op.session_id:
            await _send_error(esms, conn_id, op.account_id, "Not in a session", op.id)
            return
        exercise_id = op.payload.get("exercise_id")
        set_data = op.payload.get("set", {})
        if not exercise_id:
            await _send_error(esms, conn_id, op.account_id, "exercise_id required", op.id)
            return

        state = await repo.get_active_session_state_by_user(op.account_id)
        if not state:
            await _send_error(esms, conn_id, op.account_id, "No active state", op.id)
            return

        new_set = None
        for item in state.items:
            if item.id == exercise_id:
                new_set = ExerciseSessionStateItemSet(
                    id=str(uuid4()),
                    order=len(item.sets) + 1,
                    metrics=ExerciseSessionStateItemMetric(**set_data.get("metrics", {})),
                    type=set_data.get("type", "working"),
                    complete=False,
                )
                item.sets.append(new_set)
                break
        else:
            await _send_error(esms, conn_id, op.account_id, "Exercise not found", op.id)
            return

        state.version += 1
        await repo.update_session_state(state)

        op.payload = {"exercise_id": exercise_id, "set": new_set.dict(), "version": state.version}
        op.version = state.version

    async def handle_set_complete(op: ExerciseSessionOperation, conn_id: str):
        if not op.session_id:
            await _send_error(esms, conn_id, op.account_id, "Not in a session", op.id)
            return
        exercise_id = op.payload.get("exercise_id")
        set_id = op.payload.get("set_id")
        if not exercise_id or not set_id:
            await _send_error(esms, conn_id, op.account_id, "exercise_id and set_id required", op.id)
            return

        state = await repo.get_active_session_state_by_user(op.account_id)
        if not state:
            await _send_error(esms, conn_id, op.account_id, "No active state", op.id)
            return

        for item in state.items:
            if item.id == exercise_id:
                for s in item.sets:
                    if s.id == set_id:
                        s.complete = True
                        break
                else:
                    continue
                break
        else:
            await _send_error(esms, conn_id, op.account_id, "Set not found", op.id)
            return

        state.version += 1
        await repo.update_session_state(state)
        op.version = state.version
        op.payload["version"] = state.version

    async def handle_cursor_move(op: ExerciseSessionOperation, conn_id: str):
        if not op.session_id:
            return
        cursor = op.payload.get("cursor", {})
        session = await repo.get_session_by_id(op.session_id)
        if not session:
            return
        for participant in session.participants:
            if participant.id == op.account_id:
                participant.cursor = ExerciseSessionParticipantCursor(
                    exercise_id=cursor.get("exercise_id"),
                    exercise_set_id=cursor.get("set_id"),
                )
                await repo.mongo.update_by_id(
                    collection="exercise_sessions",
                    document_id=op.session_id,
                    update={
                        "$set": {
                            "participants": [p.dict() for p in session.participants],
                            "updated_at": datetime.now(timezone.utc),
                        }
                    },
                )
                break

    async def handle_sync_request(op: ExerciseSessionOperation, conn_id: str):
        if not op.session_id:
            await _send_error(esms, conn_id, op.account_id, "Not in a session", op.id)
            return
        session = await repo.get_session_by_id(op.session_id)
        state = await repo.get_active_session_state_by_user(op.account_id)
        if not session or not state:
            await _send_error(esms, conn_id, op.account_id, "Session or state not found", op.id)
            return
        all_states = await repo.get_session_state_by_session(op.session_id)
        await esms.send_to_connection(
            conn_id,
            _make_op(
                type_=ExerciseSessionOperationType.SYNC_RESPONSE,
                session_id=op.session_id,
                account_id=op.account_id,
                payload={
                    "session": session.dict(),
                    "state": state.dict(),
                    "participant_states": [s.dict() for s in all_states],
                    "version": state.version,
                },
                version=state.version,
                correlation_id=op.id,
            ),
        )

    esms.register_handler(ExerciseSessionOperationType.SESSION_JOIN, handle_session_join)
    esms.register_handler(ExerciseSessionOperationType.SESSION_LEAVE, handle_session_leave)
    esms.register_handler(ExerciseSessionOperationType.EXERCISE_ADD, handle_exercise_add)
    esms.register_handler(ExerciseSessionOperationType.EXERCISE_UPDATE, handle_exercise_update)
    esms.register_handler(ExerciseSessionOperationType.EXERCISE_DELETE, handle_exercise_delete)
    esms.register_handler(ExerciseSessionOperationType.SET_ADD, handle_set_add)
    esms.register_handler(ExerciseSessionOperationType.SET_COMPLETE, handle_set_complete)
    esms.register_handler(ExerciseSessionOperationType.CURSOR_MOVE, handle_cursor_move)
    esms.register_handler(ExerciseSessionOperationType.SYNC_REQUEST, handle_sync_request)
    logger.info("ESMS handlers registered")


async def init_esms(mongo: Mongo, redis: Redis) -> None:
    global _esms
    _esms = ExerciseSessionMessageService(redis=redis)
    await _esms.start()
    await register_esms_handlers(_esms, mongo, redis)

async def cleanup_esms():
    global _esms
    if _esms:
        await _esms.stop()
        _esms = None
    logger.info("Exercise Session Message Service stopped and cleaned up")

@router.websocket("/")
async def websocket_endpoint(
    websocket: WebSocket,
    current_user: Dict[str, Any] = Depends(read_ws_account_id),
    mongo: Mongo = Depends(get_ws_mongo),
    redis: Redis = Depends(get_ws_redis),
):
    service = get_esms()
    connection_id: Optional[str] = None
    account_id = current_user["id"]

    try:
        await websocket.accept()

        repo = ExerciseSessionRepository(mongo, redis)
        active_session = await repo.get_active_session_by_user(account_id)
        session_id = active_session.id if active_session else None

        connection_id = await service.connect(websocket, account_id, session_id)

        await service.send_to_connection(
            connection_id,
            _make_op(
                type_=ExerciseSessionOperationType.SESSION_UPDATE,
                session_id=session_id or "",
                account_id=account_id,
                payload={"status": "connected", "connection_id": connection_id, "session_id": session_id},
                op_id="init",
            ),
        )

        if session_id:
            state = await repo.get_active_session_state_by_user(account_id)
            if state:
                await service.send_to_connection(
                    connection_id,
                    _make_op(
                        type_=ExerciseSessionOperationType.SESSION_SYNC,
                        session_id=session_id,
                        account_id=account_id,
                        payload={"state": state.dict()},
                        op_id="init_state",
                        version=state.version,
                    ),
                )

        while True:
            try:
                raw = await websocket.receive_text()
                try:
                    payload = json.loads(raw)
                    if "type" not in payload:
                        raise ValueError("missing 'type'")
                except (json.JSONDecodeError, ValueError) as e:
                    await _send_error(service, connection_id, account_id, f"Invalid message: {e}")
                    continue

                await service.handle_client_op(connection_id, payload)

            except WebSocketDisconnect:
                logger.info("WebSocket disconnected for user %s", account_id)
                break
            except Exception:
                logger.exception("Error processing message")
                await _send_error(service, connection_id, account_id, "Internal error")
    finally:
        if connection_id:
            await service.disconnect(connection_id)
