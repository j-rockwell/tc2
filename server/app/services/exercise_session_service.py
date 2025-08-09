from fastapi import WebSocket
from enum import Enum
from typing import Dict, Any, Optional, Set, Callable, Awaitable, List
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from uuid import uuid4
import json
import asyncio
import logging

from app.db.redis import Redis

logger = logging.getLogger(__name__)
esms_prefix = "esms"

class ExerciseSessionOperationType(str, Enum):
    SESSION_JOIN = "session_join"
    SESSION_LEAVE = "session_leave"
    SESSION_UPDATE = "session_update"
    SESSION_SYNC = "session_sync"

    EXERCISE_ADD = "exercise_add"
    EXERCISE_UPDATE = "exercise_update"
    EXERCISE_DELETE = "exercise_delete"
    EXERCISE_REORDER = "exercise_reorder"

    SET_ADD = "set_add"
    SET_UPDATE = "set_update"
    SET_DELETE = "set_delete"
    SET_COMPLETE = "set_complete"
    SET_REORDER = "set_reorder"

    CURSOR_MOVE = "cursor_move"
    PARTICIPANT_JOIN = "participant_join"
    PARTICIPANT_LEAVE = "participant_leave"
    PARTICIPANT_UPDATE = "participant_update"

    HEARTBEAT = "heartbeat"
    SYNC_REQUEST = "sync_request"
    SYNC_RESPONSE = "sync_response"


@dataclass
class ExerciseSessionOperation:
    id: str
    type: ExerciseSessionOperationType
    session_id: str
    account_id: str
    payload: Dict[str, Any]
    timestamp: datetime
    version: int = 0
    correlation_id: Optional[str] = None
    instance_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["type"] = self.type.value
        d["timestamp"] = self.timestamp.isoformat()
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"))

    @classmethod
    def from_json(cls, data: str) -> "ExerciseSessionOperation":
        obj = json.loads(data)
        obj["type"] = ExerciseSessionOperationType(obj["type"])
        ts = obj.get("timestamp")
        if isinstance(ts, str):
            obj["timestamp"] = datetime.fromisoformat(ts)
        return cls(**obj)


@dataclass
class ESMSConnectionInfo:
    websocket: WebSocket
    account_id: str
    session_id: Optional[str]
    connected_at: datetime
    last_activity: datetime
    instance_id: str


Handler = Callable[[ExerciseSessionOperation, str], Awaitable[None]]

class ExerciseSessionMessageService:
    def __init__(self, redis: Redis, instance_id: Optional[str] = None):
        self.redis = redis
        self.instance_id = instance_id or str(uuid4())
        self.connections: Dict[str, ESMSConnectionInfo] = {}
        self.session_connections: Dict[str, Set[str]] = {}
        self.account_connections: Dict[str, Set[str]] = {}
        self.handlers: Dict[ExerciseSessionOperationType, List[Handler]] = {}
        self.pubsub = None
        self.pubsub_task: Optional[asyncio.Task] = None
        self.running = False
        self._lock = asyncio.Lock()
        self.stats = {
            "outgoing_messages": 0,
            "incoming_messages": 0,
            "connections_active": 0,
            "errors": 0,
        }
        logger.info("ExerciseSessionMessageService initialized instance_id=%s", self.instance_id)

    async def start(self):
        if self.running:
            return
        self.running = True
        client = self.redis.get_client()
        self.pubsub = client.pubsub()
        await self.pubsub.subscribe(f"{esms_prefix}:global")
        self.pubsub_task = asyncio.create_task(self._pubsub_listener())
        logger.info("ExerciseSessionMessageService started")

    async def stop(self):
        self.running = False
        
        async with self._lock:
            conn_ids = list(self.connections.keys())
        
        for cid in conn_ids:
            await self.disconnect(cid)
        
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
        
        logger.info("ExerciseSessionMessageService stopped")

    async def connect(self, websocket: WebSocket, account_id: str, session_id: Optional[str] = None) -> str:
        if not self.running or self.pubsub is None:
            raise RuntimeError("ExerciseSessionMessageService.start() must be called before connect()")
        
        connection_id = str(uuid4())
        now = datetime.now(timezone.utc)
        info = ESMSConnectionInfo(
            websocket=websocket,
            account_id=account_id,
            session_id=session_id,
            connected_at=now,
            last_activity=now,
            instance_id=self.instance_id,
        )
        
        async with self._lock:
            self.connections[connection_id] = info
            self.account_connections.setdefault(account_id, set()).add(connection_id)
            if session_id:
                created = session_id not in self.session_connections
                self.session_connections.setdefault(session_id, set()).add(connection_id)
                if created:
                    await self.pubsub.subscribe(f"{esms_prefix}:session:{session_id}")
            self.stats["connections_active"] += 1
        
        await self._update_connection_registry(connection_id, info)
        logger.info("WS connected id=%s account=%s session=%s", connection_id, account_id, session_id)
        return connection_id

    async def disconnect(self, connection_id: str):
        async with self._lock:
            info = self.connections.get(connection_id)
            if not info:
                return
            
            acct = info.account_id
            sess = info.session_id
            conns = self.account_connections.get(acct)
            if conns:
                conns.discard(connection_id)
                if not conns:
                    self.account_connections.pop(acct, None)
            
            if sess:
                s_conns = self.session_connections.get(sess)
                if s_conns:
                    s_conns.discard(connection_id)
                    if not s_conns:
                        self.session_connections.pop(sess, None)
                        if self.pubsub:
                            await self.pubsub.unsubscribe(f"{esms_prefix}:session:{sess}")
            
            self.connections.pop(connection_id, None)
            self.stats["connections_active"] -= 1
        
        await self._remove_connection_registry(connection_id)
        
        try:
            await info.websocket.close()
        except Exception:
            pass
        
        logger.info("WS disconnected id=%s", connection_id)

    async def join_session(self, connection_id: str, session_id: str):
        if not self.running or self.pubsub is None:
            raise RuntimeError("ExerciseSessionMessageService.start() must be called before join_session()")
        
        async with self._lock:
            info = self.connections.get(connection_id)
            if not info:
                return
            old = info.session_id
        
        if old and old != session_id:
            await self.leave_session(connection_id)
        
        async with self._lock:
            info = self.connections.get(connection_id)
            if not info:
                return
            info.session_id = session_id
            created = session_id not in self.session_connections
            self.session_connections.setdefault(session_id, set()).add(connection_id)
            if created:
                await self.pubsub.subscribe(f"{esms_prefix}:session:{session_id}")
        
        await self._update_connection_registry(connection_id, info)
        await self.broadcast_to_session(
            session_id,
            ExerciseSessionOperation(
                id=str(uuid4()),
                type=ExerciseSessionOperationType.PARTICIPANT_JOIN,
                session_id=session_id,
                account_id=info.account_id,
                payload={"account_id": info.account_id},
                timestamp=datetime.now(timezone.utc),
                version=0,
                instance_id=self.instance_id,
            ),
            exclude_connection=connection_id,
        )

    async def leave_session(self, connection_id: str):
        if not self.running or self.pubsub is None:
            raise RuntimeError("ExerciseSessionMessageService.start() must be called before leave_session()")
    
        async with self._lock:
            info = self.connections.get(connection_id)
            if not info:
                return
            session_id = info.session_id
            if not session_id:
                return
            info.session_id = None
            s_conns = self.session_connections.get(session_id)
            if s_conns:
                s_conns.discard(connection_id)
                if not s_conns:
                    self.session_connections.pop(session_id, None)
                    await self.pubsub.unsubscribe(f"{esms_prefix}:session:{session_id}")
        
        await self._update_connection_registry(connection_id, info)
        await self.broadcast_to_session(
            session_id,
            ExerciseSessionOperation(
                id=str(uuid4()),
                type=ExerciseSessionOperationType.PARTICIPANT_LEAVE,
                session_id=session_id,
                account_id=info.account_id,
                payload={"account_id": info.account_id},
                timestamp=datetime.now(timezone.utc),
                version=0,
                instance_id=self.instance_id,
            ),
        )

    async def send_to_connection(self, connection_id: str, op: ExerciseSessionOperation):
        async with self._lock:
            info = self.connections.get(connection_id)
        
        if not info:
            return
    
        try:
            await info.websocket.send_text(op.to_json())
            info.last_activity = datetime.now(timezone.utc)
            self.stats["outgoing_messages"] += 1
        except Exception as e:
            logger.error("send_to_connection failed id=%s err=%s", connection_id, e)
            self.stats["errors"] += 1
            await self.disconnect(connection_id)

    async def send_to_account(self, account_id: str, op: ExerciseSessionOperation):
        async with self._lock:
            conn_ids = list(self.account_connections.get(account_id, ()))
            
        if not conn_ids:
            return
        
        await asyncio.gather(*(self.send_to_connection(cid, op) for cid in conn_ids), return_exceptions=True)

    async def broadcast_to_session(self, session_id: str, op: ExerciseSessionOperation, exclude_connection: Optional[str] = None):
        if op.instance_id is None:
            op.instance_id = self.instance_id
        
        channel = f"{esms_prefix}:session:{session_id}"
        await self.redis.publish(channel, op.to_json())
        
        async with self._lock:
            conn_ids = list(self.session_connections.get(session_id, ()))
        
        if not conn_ids:
            return
    
        tasks = []
        for cid in conn_ids:
            if cid == exclude_connection:
                continue
            tasks.append(self.send_to_connection(cid, op))
        
        await asyncio.gather(*tasks, return_exceptions=True)

    async def handle_client_op(self, connection_id: str, payload: Dict[str, Any]):
        async with self._lock:
            info = self.connections.get(connection_id)
            
        if not info:
            return
        
        info.last_activity = datetime.now(timezone.utc)
        
        try:
            op = ExerciseSessionOperation(
                id=payload.get("id", str(uuid4())),
                type=ExerciseSessionOperationType(payload["type"]),
                session_id=payload.get("session_id", info.session_id or ""),
                account_id=info.account_id,
                payload=payload.get("payload", {}),
                timestamp=datetime.now(timezone.utc),
                version=payload.get("version", 0),
                correlation_id=payload.get("correlation_id"),
                instance_id=self.instance_id,
            )
            
            self.stats["incoming_messages"] += 1
            await self._route_op(op, connection_id)
        except Exception as e:
            logger.error("handle_client_op error: %s", e)
            self.stats["errors"] += 1
            err = ExerciseSessionOperation(
                id=str(uuid4()),
                type=ExerciseSessionOperationType.SESSION_UPDATE,
                session_id=info.session_id or "",
                account_id=info.account_id,
                payload={"error": str(e)},
                timestamp=datetime.now(timezone.utc),
                version=0,
                correlation_id=payload.get("id"),
                instance_id=self.instance_id,
            )
            
            await self.send_to_connection(connection_id, err)

    async def _route_op(self, op: ExerciseSessionOperation, connection_id: str):
        for handler in self.handlers.get(op.type, []):
            try:
                await handler(op, connection_id)
            except Exception as e:
                logger.exception("handler failed for %s: %s", op.type, e)
                self.stats["errors"] += 1
        
        if op.session_id and op.type not in {
            ExerciseSessionOperationType.HEARTBEAT,
            ExerciseSessionOperationType.SYNC_REQUEST,
            ExerciseSessionOperationType.SYNC_RESPONSE,
        }:
            await self.broadcast_to_session(op.session_id, op, exclude_connection=connection_id)

    def register_handler(self, op_type: ExerciseSessionOperationType, handler: Handler):
        self.handlers.setdefault(op_type, []).append(handler)

    async def _pubsub_listener(self):
        while self.running and self.pubsub is not None:
            try:
                msg = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if msg and msg.get("type") == "message":
                    await self._handle_pubsub_op(msg)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("pubsub listener error: %s", e)
                await asyncio.sleep(1)

    async def _handle_pubsub_op(self, redis_op: Dict[str, Any]):
        try:
            raw = redis_op.get("data")
            
            if isinstance(raw, (bytes, bytearray)):
                raw = raw.decode("utf-8")
                
            op = ExerciseSessionOperation.from_json(raw)
            
            if op.instance_id == self.instance_id:
                return
            
            async with self._lock:
                conn_ids = list(self.session_connections.get(op.session_id, ()))
                
            if not conn_ids:
                return
            
            await asyncio.gather(*(self.send_to_connection(cid, op) for cid in conn_ids), return_exceptions=True)
        except Exception as e:
            logger.error("handle_pubsub_op error: %s", e)

    async def _update_connection_registry(self, connection_id: str, connection_info: ESMSConnectionInfo):
        key = f"{esms_prefix}:connection:{connection_id}"
        data = {
            "account_id": connection_info.account_id,
            "session_id": connection_info.session_id,
            "instance_id": connection_info.instance_id,
            "connected_at": connection_info.connected_at.isoformat(),
            "last_activity": connection_info.last_activity.isoformat(),
        }
        await self.redis.setex(key, 300, json.dumps(data))

    async def _remove_connection_registry(self, connection_id: str):
        await self.redis.delete(f"{esms_prefix}:connection:{connection_id}")

    async def get_session_connections(self, session_id: str) -> List[Dict[str, Any]]:
        client = self.redis.get_client()
        pattern = f"{esms_prefix}:connection:*"
        results: List[Dict[str, Any]] = []
        async for key in client.scan_iter(match=pattern):
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

    def get_stats(self) -> Dict[str, Any]:
        with_sessions = {sid: len(conns) for sid, conns in self.session_connections.items()}
        with_accounts = {aid: len(conns) for aid, conns in self.account_connections.items()}
        return {
            **self.stats,
            "instance_id": self.instance_id,
            "connections_by_session": with_sessions,
            "connections_by_account": with_accounts,
        }
