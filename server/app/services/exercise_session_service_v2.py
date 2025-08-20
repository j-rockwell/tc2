from operator import add
from fastapi import WebSocket
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum
from uuid import uuid4
import asyncio
import logging
import json

from app.db.mongo import Mongo
from app.db.redis import Redis
from app.repos.account import AccountRepository
from app.repos.exercise import ExerciseMetaRepository
from app.repos.exercise_session import ExerciseSessionRepository
from app.schema.exercise import ExerciseMeta
from app.schema.exercise_session import ExerciseSessionItemMeta, ExerciseSessionStateItem, ExerciseSessionStateItemType, ExerciseSessionStatus

logger = logging.getLogger(__name__)
psub_prefix = "esms"

def _makelog(msg: str) -> str:
    return f"ESMS: {msg}"

# operation models start
class ExerciseSessionOperationType(str, Enum):
    JOIN = "join"
    LEAVE = "leave"
    ADD_EXERCISE = "add_exercise"
    UPDATE_EXERCISE = "update_exercise"
    REMOVE_EXERCISE = "remove_exercise"
    ADD_SET = "add_set"
    UPDATE_SET = "update_set"
    REMOVE_SET = "remove_set"
    COMPLETE_SET = "complete_set"
    UPDATE_CURSOR = "update_cursor"

class ExerciseSessionOperation(BaseModel):
    id: str
    session_id: str
    author_id: str
    op_type: ExerciseSessionOperationType
    instance_id: str
    payload: Dict[str, Any]
    timestamp: datetime
    version: int = 0

class AddExerciseOperation(BaseModel):
    meta: Dict[str, Any]
    set_type: ExerciseSessionStateItemType
    rest: int = -1
    participants: Optional[List[str]] = []
# operation models end

# socket data start
class ESMConnectionInfo(BaseModel):
    websocket: WebSocket
    account_id: str
    session_id: str
    instance_id: str
    connected_at: datetime
    last_activity: datetime
# socket data end

class ESMService:
    def __init__(self, db: Mongo, redis: Redis, instance_id: Optional[str] = None):
        self.instance_id = instance_id or str(uuid4())
        self.db = db
        self.redis = redis
        self.pubsub = None
        self.pubsub_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self.running = False
        self.connections: dict[str, ESMConnectionInfo] = {}
        self.session_connections: dict[str, set[str]] = {}
        self.account_connections: dict[str, set[str]] = {}
        self.session_repo = ExerciseSessionRepository(db, redis)
        self.account_repo = AccountRepository(db, redis)
        self.exercise_meta_repo = ExerciseMetaRepository(db, redis)
        logger.info(_makelog("init"))
    
    
    
    def _validate_operation(self, operation: ExerciseSessionOperation):
        # join
        if operation.op_type == ExerciseSessionOperationType.JOIN:
            if not operation.payload:
                raise ValueError("Payload must be provided for JOIN operation")
            elif operation.payload.get("session_id") is None:
                raise ValueError("Session ID must be provided in payload for JOIN operation")
        
        # leave
        if operation.op_type == ExerciseSessionOperationType.LEAVE:
            if not operation.payload:
                raise ValueError("Payload must be provided for LEAVE operation")
            elif operation.payload.get("session_id") is None:
                raise ValueError("Session ID must be provided in payload for LEAVE operation")
        
        # add_exercise
        if operation.op_type == ExerciseSessionOperationType.ADD_EXERCISE:
            if not operation.payload:
                raise ValueError("Payload must be provided for ADD_EXERCISE operation")
            elif operation.payload.get("exercise_id") is None:
                raise ValueError("Exercise ID must be provided in payload for ADD_EXERCISE operation")
        
        # update_exercise
        if operation.op_type == ExerciseSessionOperationType.UPDATE_EXERCISE:
            if not operation.payload:
                raise ValueError("Payload must be provided for UPDATE_EXERCISE operation")
            elif operation.payload.get("exercise_id") is None:
                raise ValueError("Exercise ID must be provided in payload for UPDATE_EXERCISE operation")
        
        # remove_exercise
        if operation.op_type == ExerciseSessionOperationType.REMOVE_EXERCISE:
            if not operation.payload:
                raise ValueError("Payload must be provided for REMOVE_EXERCISE operation")
            elif operation.payload.get("exercise_id") is None:
                raise ValueError("Exercise ID must be provided in payload for REMOVE_EXERCISE operation")
        
        # add_set
        if operation.op_type == ExerciseSessionOperationType.ADD_SET:
            if not operation.payload:
                raise ValueError("Payload must be provided for ADD_SET operation")
            elif operation.payload.get("exercise_id") is None:
                raise ValueError("Exercise ID must be provided in payload for ADD_SET operation")
        
        # update_set
        if operation.op_type == ExerciseSessionOperationType.UPDATE_SET:
            if not operation.payload:
                raise ValueError("Payload must be provided for UPDATE_SET operation")
            elif operation.payload.get("exercise_id") is None:
                raise ValueError("Exercise ID must be provided in payload for UPDATE_SET operation")
            elif operation.payload.get("set_id") is None:
                raise ValueError("Set ID must be provided in payload for UPDATE_SET operation")
        
        # remove_set
        if operation.op_type == ExerciseSessionOperationType.REMOVE_SET:
            if not operation.payload:
                raise ValueError("Payload must be provided for REMOVE_SET operation")
            elif operation.payload.get("exercise_id") is None:
                raise ValueError("Exercise ID must be provided in payload for REMOVE_SET operation")
            elif operation.payload.get("set_id") is None:
                raise ValueError("Set ID must be provided in payload for REMOVE_SET operation")
        
        # complete_set
        if operation.op_type == ExerciseSessionOperationType.COMPLETE_SET:
            if not operation.payload:
                raise ValueError("Payload must be provided for COMPLETE_SET operation")
            elif operation.payload.get("exercise_id") is None:
                raise ValueError("Exercise ID must be provided in payload for COMPLETE_SET operation")
            elif operation.payload.get("set_id") is None:
                raise ValueError("Set ID must be provided in payload for COMPLETE_SET operation")
        
        # update_cursor
        if operation.op_type == ExerciseSessionOperationType.UPDATE_CURSOR:
            if not operation.payload:
                raise ValueError("Payload must be provided for UPDATE_CURSOR operation")
            elif operation.payload.get("exercise_id") is None:
                raise ValueError("Exercise ID must be provided in payload for UPDATE_CURSOR operation")
            elif operation.payload.get("set_id") is None:
                raise ValueError("Exercise Set ID must be provided in payload for UPDATE_CURSOR operation")
        
        operation.timestamp = datetime.now(timezone.utc)
    
    
    
    async def _listen(self):
        """Listen for messages on the pubsub channel and process them"""
        while self.running and self.pubsub is not None:
            try:
                msg = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if msg and msg.get("type") == "message":
                    await self._read_op(msg)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(_makelog("pubsub listener error: %s"), e)
                await asyncio.sleep(1)
    
    
    
    async def _read_op(self, op: Dict[str, Any]):
        """Read an operation from the pubsub channel and send it to the appropriate connections"""
        try:
            raw = op.get("data")
            if not raw:
                raise RuntimeError("Could not find data in pubsub")
            if isinstance(raw, (bytes, bytearray)):
                raw = raw.decode("utf-8")
            
            converted = ExerciseSessionOperation.parse_raw(raw)
            
            if converted.instance_id == self.instance_id:
                return
            
            async with self._lock:
                connections: set[str] = self.session_connections.get(converted.session_id, set())
                targets = tuple(connections)
            
            if not targets:
                return
            
            if not connections:
                return
            
            await asyncio.gather(*(self.send_to_connection(cid, converted) for cid in targets), return_exceptions=True)
        except Exception as e:
            logger.error(_makelog("read_op failed: %s"), e)
            raise
    
    
    
    async def _update_connection_registry(self, connection_id: str, connection: ESMConnectionInfo):
        """Update the connection registry in redis"""
        key = f"{psub_prefix}:connection:{connection_id}"
        data = {
            "account_id": connection.account_id,
            "session_id": connection.session_id,
            "instance_id": connection.instance_id,
            "connected_at": connection.connected_at.isoformat(),
            "last_activity": connection.last_activity.isoformat(),
        }
        await self.redis.setex(key, 300, json.dumps(data))
    
    
    
    async def _remove_connection_registry(self, connection_id: str):
        """Remove the connection registry from redis"""
        await self.redis.delete(f"{psub_prefix}:connection:{connection_id}")
        
    

    async def _assert_session_active(self, session_id: str):
        session = await self.session_repo.get_session_by_id(session_id)
        if not session:
            raise ValueError(f"Session with ID {session_id} does not exist")

        status_val = getattr(session, "status", None)
        if isinstance(status_val, ExerciseSessionStatus):
            is_active = status_val == ExerciseSessionStatus.ACTIVE
        else:
            is_active = str(status_val) == ExerciseSessionStatus.ACTIVE.value
        if not is_active:
            raise ValueError(f"Session with ID {session_id} is not active")
        return session



    async def _assert_connection_in_session(self, connection_id: str, session_id: str) -> ESMConnectionInfo:
        async with self._lock:
            conn = self.connections.get(connection_id)
        if not conn:
            raise ValueError("Connection not found")
        if conn.session_id != session_id:
            raise ValueError("Connection is not joined to the target session")
        return conn
    
    
    
    async def get_session_connections(self, session_id: str) -> list[dict[str, Any]]:
        """Get all connections for a specific session"""
        pattern = f"{psub_prefix}:connection:*"
        results: list[dict[str, Any]] = []
        async for key in self.redis.get_client().scan_iter(match=pattern):
            raw = await self.redis.get(key)
            if not raw:
                continue
            s = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
            try:
                data = json.loads(s)
                if data.get("session_id") == session_id:
                    results.append(data)
            except json.JSONDecodeError:
                continue
        return results
    
    
    
    async def start(self):
        """Start the ESM service"""
        if self.running:
            return
        
        self.pubsub = self.redis.get_client().pubsub()
        await self.pubsub.subscribe(f"{psub_prefix}:global")
        self.pubsub_task = asyncio.create_task(self._listen())
        logger.info(_makelog("started"))
    
    
    
    async def stop(self):
        """Stop the ESM service"""
        if not self.running:
            return
        
        async with self._lock:
            connections = self.connections
            
        for cid in connections:
            await self.close_connection(cid)
        
        if self.pubsub:
            try:
                await self.pubsub.unsubscribe()
            except Exception:
                pass
            
            try:
                await self.pubsub.close()
            except Exception:
                pass
            
            self.pubsub = None
        
        if self.pubsub_task:
            self.pubsub_task.cancel()
            try:
                await self.pubsub_task
            except asyncio.CancelledError:
                pass
            self.pubsub_task = None
        
        logger.info(_makelog("stopped"))
    
    
    
    async def open_connection(self, websocket: WebSocket, account_id: str, session_id: str) -> str:
        """Open a new connection and register it"""
        if not self.running or self.pubsub is None:
            raise RuntimeError("start() must be called before open_connection()")
        
        connection_id = str(uuid4())
        now = datetime.now(timezone.utc)
        connection = ESMConnectionInfo(
            websocket=websocket,
            account_id=account_id,
            session_id=session_id,
            connected_at=now,
            last_activity=now,
            instance_id=self.instance_id
        )
        
        async with self._lock:
            self.connections[connection_id] = connection
            self.account_connections.setdefault(account_id, set()).add(connection_id)
            
            if session_id:
                created = session_id not in self.session_connections
                self.session_connections.setdefault(session_id, set()).add(connection_id)
                if created:
                    await self.pubsub.subscribe(f"{psub_prefix}:session:{session_id}")
            
        await self._update_connection_registry(connection_id, connection)
        logger.info(_makelog("opened connection id=%s account=%s session=%s"), connection_id, account_id, session_id)
        return connection_id
    
    
    
    async def close_connection(self, connection_id: str):
        """Close an existing connection and remove it from the registry"""
        async with self._lock:
            connection = self.connections.get(connection_id)
            if not connection:
                return
            
            account_id = connection.account_id
            session_id = connection.session_id
            connections = self.account_connections.get(account_id)
            
            if connections:
                connections.discard(connection_id)
                if not connections:
                    self.account_connections.pop(account_id, None)
            
            if session_id:
                session_connections = self.session_connections.get(session_id)
                if session_connections:
                    session_connections.discard(connection_id)
                    if not session_connections:
                        self.session_connections.pop(session_id, None)
                        if self.pubsub:
                            await self.pubsub.unsubscribe(f"{psub_prefix}:session:{session_id}")
            
            self.connections.pop(connection_id, None)
        
        await self._remove_connection_registry(connection_id)
        
        try:
            await connection.websocket.close()
        except Exception:
            pass
        
        logger.info(_makelog("closed connection id=%s, account=%s, session=%s"), connection_id, account_id, session_id)
    
    
    
    async def send_to_connection(self, connection_id: str, operation: ExerciseSessionOperation):
        """Send an operation to a specific connection"""
        async with self._lock:
            connection = self.connections.get(connection_id)
        
        if not connection:
            return
        
        try:
            await connection.websocket.send_text(operation.json())
            connection.last_activity = datetime.now(timezone.utc)
        except Exception as e:
            logger.error(_makelog("send_to_connection failed id=%s err=%s"), connection_id, e)
            await self.close_connection(connection_id)
    
    
    
    async def send_to_account(self, account_id: str, operation: ExerciseSessionOperation):
        """Send an operation to all connections of a specific account"""
        async with self._lock:
            connections = list(self.account_connections.get(account_id, set()))
        
        if not connections:
            return
        
        await asyncio.gather(*(self.send_to_connection(cid, operation) for cid in connections), return_exceptions=True)
    
    
    
    async def broadcast_operation(self, operation: ExerciseSessionOperation, exclude_connection: Optional[str] = None):
        """Broadcast an operation to all connections, excluding a specific one"""
        if operation.instance_id is None:
            operation.instance_id = self.instance_id
        
        channel = f"{psub_prefix}:session:{operation.session_id}"
        await self.redis.publish(channel, operation.json())
        
        async with self._lock:
            connections = list(self.connections.keys())
        
        if not connections:
            return
        
        tasks = []
        for cid in connections:
            if cid == exclude_connection:
                continue
            tasks.append(self.send_to_connection(cid, operation))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    

    
    async def join_session(self, connection_id: str, operation: ExerciseSessionOperation):
        """Handle a join session operation"""
        assert operation.op_type == ExerciseSessionOperationType.JOIN, "Invalid operation type for join_session"
        assert operation.payload, "Payload must be provided"
        
        if not self.running or self.pubsub is None:
            raise RuntimeError("start() must be called before join_session()")
        
        async with self._lock:
            connection = self.connections.get(operation.id)
            if not connection:
                raise
            old_session_id = connection.session_id
        
        if old_session_id and old_session_id != operation.payload.get("session_id"):
            await self.leave_session(connection_id)
        
        try:
            self._validate_operation(operation)
        except Exception as e:
            logger.error(f"Validation failed for operation {operation.id}: {e}")
            raise ValueError(f"Validation failed: {e}")
        
        session_id = operation.payload.get("session_id")
        if not session_id:
            raise ValueError("Session ID must be provided in payload for JOIN operation")
        
        author_id = operation.author_id
        author = await self.account_repo.get_account_by_id(author_id)
        if not author:
            raise ValueError(f"Account with ID {author_id} does not exist")
        
        session = await self.session_repo.get_session_by_id(session_id)
        if not session:
            raise ValueError(f"Session with ID {session_id} does not exist")
        
        if session.status != ExerciseSessionStatus.ACTIVE:
            raise ValueError(f"Session with ID {session_id} is not active")
        
        if author_id in session.participants:
            raise ValueError(f"Account with ID {author_id} is already a participant of this session")
        
        async with self._lock:
            connection = self.connections.get(connection_id)
            if not connection:
                return
            connection.session_id = session_id
            created = session_id not in self.session_connections
            self.session_connections.setdefault(session_id, set()).add(connection_id)
            if created:
                await self.pubsub.subscribe(f"{psub_prefix}:session:{session_id}")
        
        await self._update_connection_registry(connection_id, connection)
        await self.broadcast_operation(operation, exclude_connection=connection_id)


    
    async def leave_session(self, connection_id: str):
        """Handle a leave session operation - force user to leave any current session"""
        if not self.running or self.pubsub is None:
            raise RuntimeError("start() must be called before leave_session()")
        
        async with self._lock:
            connection = self.connections.get(connection_id)
            if not connection:
                return
            
            session_id = connection.session_id
            account_id = connection.account_id
            
            if not session_id:
                return

            connection.session_id = ""
            
            session_connections = self.session_connections.get(session_id)
            if session_connections:
                session_connections.discard(connection_id)
                if not session_connections:
                    self.session_connections.pop(session_id, None)
                    if self.pubsub:
                        await self.pubsub.unsubscribe(f"{psub_prefix}:session:{session_id}")
        
        await self._update_connection_registry(connection_id, connection)
        
        leave_op = ExerciseSessionOperation(
            id=str(uuid4()),
            op_type=ExerciseSessionOperationType.LEAVE,
            session_id=session_id,
            author_id=account_id,
            payload={"account_id": account_id, "session_id": session_id},
            timestamp=datetime.now(timezone.utc),
            version=0,
            instance_id=self.instance_id,
        )
        await self.broadcast_operation(leave_op, exclude_connection=connection_id)


    
    async def add_exercise(self, connection_id: str, operation: ExerciseSessionOperation):
        """Handle adding an exercise to the session"""
        if not self.running or self.pubsub is None:
            raise RuntimeError("start() must be called before add_exercise()")
        
        self._validate_operation(operation)
        session = await self._assert_session_active(operation.session_id)
        await self._assert_connection_in_session(connection_id, operation.session_id)
        
        try:
            add_exercise_data = AddExerciseOperation(**operation.payload)
        except Exception as e:
            raise ValueError(f"Invalid payload for ADD_EXERCISE operation: {e}")
        
        state = await self.session_repo.get_active_session_state_by_user(operation.author_id)
        if not state:
            state = await self.session_repo.create_session_state(operation.session_id, operation.author_id)
        if not state:
            raise ValueError(f"Session state for user {operation.author_id} not found")
        
        if add_exercise_data.participants:
            valid_participants = []
            for participant_id in add_exercise_data.participants:
                is_in_session = any(p.id == participant_id for p in session.participants)
                if is_in_session:
                    valid_participants.append(participant_id)
            
            participants = valid_participants if valid_participants else [operation.author_id]
        else:
            participants = [operation.author_id]
        
        new_item = ExerciseSessionStateItem(
            id=str(uuid4()),
            order=len(state.items) + 1,
            participants=participants,
            type=add_exercise_data.set_type,
            rest=-1,
            meta=[ExerciseSessionItemMeta(**m) if isinstance(m, dict) else m 
                  for m in add_exercise_data.meta.get("meta", [])],
            sets=[]
        )
        
        state.items.append(new_item)
        state.version += 1
        
        await self.session_repo.update_session_state(state)
        
        operation.payload = {
            "exercise": new_item.dict(),
            "version": state.version
        }
        operation.version = state.version
        
        await self.broadcast_operation(operation, exclude_connection=connection_id)

    

    async def update_exercise(self):
        pass


    
    async def remove_exercise(self):
        pass


    
    async def add_set(self):
        pass


    
    async def update_set(self):
        pass


    
    async def remove_set(self):
        pass


    
    async def complete_set(self):
        pass


    
    async def update_cursor(self):
        pass