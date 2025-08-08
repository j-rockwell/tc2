from typing import Optional, Dict, Any, List, Set
from app.db.mongo import Mongo
from app.db.redis import Redis
from app.schema.session import ExerciseSessionState, ExerciseItem, ExerciseSet
from app.schema.messages.session import SessionStateOperation, SessionOperationType
from datetime import datetime, timezone
import json
import logging

logger = logging.getLogger(__name__)
session_key = "exercise_sessions"
session_states_key = "exercise_session_states"
session_ops_key = "exercise_session_ops:"
session_updates_key = "exercise_session_updates:"

class SessionStateService:
    def __init__(self, mongo: Mongo, redis: Redis):
        self.mongo = mongo
        self.redis = redis
        self._active_connections: Dict[str, Set[str]] = {}
    
    async def init_user_state(self, session_id, account_id: str) -> ExerciseSessionState:
        """Initialize session state for a user"""
        try:
            existing_state = await self.get_user_state(session_id, account_id)
            if existing_state:
                return existing_state
            
            state = ExerciseSessionState(
                session_id=session_id,
                account_id=account_id,
                version=0,
                items=[],
                updated_at=datetime.now(timezone.utc)
            )
            
            await self.mongo.insert(session_states_key, state)
            await self._cache_state(state)
            
            logger.info(f"Initialized session state for user {account_id} in session {session_id}")
            return state
        except Exception as e:
            logger.error(f"Failed to initialize user state: {e}")
            raise
    
    async def get_user_state(self, session_id: str, account_id: str) -> Optional[ExerciseSessionState]:
        """Get current session state for a user"""
        try:
            cache_key = self._get_state_cache_key(session_id, account_id)
            cached_state = await self.redis.get(cache_key, decode_json=True)
            
            if cached_state:
                return ExerciseSessionState(**cached_state)
            
            doc = await self.mongo.find_one(
                session_states_key,
                { "session_id": session_id, "account_id": account_id }
            )
            
            if doc:
                state = ExerciseSessionState(**doc)
                await self._cache_state(state)
                return state
            
            return None
        except Exception as e:
            logger.error(f"Failed to perform state lookup for user {account_id} in session {session_id}")
            return None
    
    async def apply_operation(self, operation: SessionStateOperation) -> Dict[str, Any]:
        """Apply operation to a session"""
        try:
            current_state = await self.init_user_state(operation.session_id, operation.account_id)
            if not current_state:
                current_state = await self.init_user_state(operation.session_id, operation.account_id)
            
            conflicts = []
            if operation.version > 0 and operation.version < current_state.version:
                conflicts = await self._resolve_conflict(operation, current_state)
            
            new_state = await self._execute_operation(operation, current_state)
            
            await self._save_state(new_state)
            await self._log_op(operation)
            await self._broadcast_op(operation, conflicts)
            
            result = {
                "success": True,
                "operation_id": operation.operation_id,
                "new_version": new_state.version,
                "conflicts_resolved": len(conflicts),
                "conflicts": conflicts,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.debug(f"Applied operation {operation.operation_id} to session {operation.session_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to apply operation {operation.operation_id} to session {operation.session_id}")
            return {
                "success": False,
                "operation_id": operation.operation_id,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def _execute_operation(self, operation: SessionStateOperation, current_state: ExerciseSessionState) -> ExerciseSessionState:
        """Execute an operation on an active session"""
        new_state = ExerciseSessionState(
            session_id=current_state.session_id,
            account_id=current_state.account_id,
            version=current_state.version+1,
            items=current_state.items.copy(),
            updated_at=datetime.now(timezone.utc)
        )
        
        if operation.operation_type == SessionOperationType.ADD_EXERCISE:
            await self._add_exercise(new_state, operation)
        elif operation.operation_type == SessionOperationType.UPDATE_EXERCISE:
            await self._update_exercise(new_state, operation)
        elif operation.operation_type == SessionOperationType.DELETE_EXERCISE:
            await self._delete_exercise(new_state, operation)
        elif operation.operation_type == SessionOperationType.ADD_SET:
            await self._add_set(new_state, operation)
        elif operation.operation_type == SessionOperationType.UPDATE_SET:
            await self._update_set(new_state, operation)
        elif operation.operation_type == SessionOperationType.DELETE_SET:
            await self._delete_set(new_state, operation)
        else:
            raise ValueError(f"Unknown operation type: {operation.operation_type}")
        
        # TODO: Add other operation type support here
        
        return new_state

    async def _add_exercise(self, state: ExerciseSessionState, operation: SessionStateOperation):
        """Add an exercise to a session"""
        if "exercise" not in operation.payload:
            raise ValueError("Invalid payload for add_exercise operation")
        
        exercise_data = operation.payload["exercise"]
        
        new_exercise = ExerciseItem(
            id=exercise_data["id"],
            name=exercise_data["name"],
            type=exercise_data["type"],
            sets=[]
        )
        
        position = operation.payload.get("position", len(state.items))
        
        if 0 <= position <= len(state.items):
            state.items.insert(position, new_exercise)
        else:
            state.items.append(new_exercise)
    
    async def _update_exercise(self, state: ExerciseSessionState, operation: SessionStateOperation):
        """Update an exercise in a session"""
        if not operation.target_item_id:
            raise ValueError("target_item_id required for update_exercise operation")
        
        for item in state.items:
            if hasattr(item, 'id') and item.id == operation.target_item_id:
                for key, value in operation.payload.items():
                    if key in ["name", "note"] and hasattr(item, key):
                        setattr(item, key, value)
                return
        
        raise ValueError(f"Exercise {operation.target_item_id} not found")
    
    async def _delete_exercise(self, state: ExerciseSessionState, operation: SessionStateOperation):
        """Delete an exercise from a session"""
        if not operation.target_item_id:
            raise ValueError("target_item_id required for delete_exercise operation")
        
        original_len = len(state.items)
        state.items = [
            item for item in state.items
            if not (hasattr(item, 'id') and item.id == operation.target_item_id)
        ]
        
        if len(state.items) == original_len:
            raise ValueError(f"Exercise {operation.target_item_id} not found")
        
    async def _add_set(self, state: ExerciseSessionState, operation: SessionStateOperation):
        """Add a set to an exercise in a session"""
        if not operation.target_item_id or "set" not in operation.payload:
            raise ValueError("target_item_id and set data required for add_set operation")
        
        for item in state.items:
            if hasattr(item, 'id') and item.id == operation.target_item_id and hasattr(item, 'sets'):
                set_data = operation.payload["set"]
                
                new_set = ExerciseSet(
                    id=operation.payload.get["id"],
                    order=set_data.get("order", len(item.sets)+1),
                    reps=set_data.get("reps"),
                    weight=set_data.get("weight"),
                    distance=set_data.get("distance"),
                    duration=set_data.get("duration")
                )
                
                position = operation.payload.get("position", len(item.sets))
                
                if 0 <= position <= len(item.sets):
                    item.sets.insert(position, new_set)
                else:
                    item.sets.append(new_set)
                return
        
        raise ValueError(f"Exercise {operation.target_item_id} not found")

    async def _update_set(self, state: ExerciseSessionState, operation: SessionStateOperation):
        """Update a set in an exercise in a session"""
        if not operation.target_item_id or not operation.target_set_id:
            raise ValueError("target_item_id and target_set_id required for update_set operation")
        
        for item in state.items:
            if hasattr(item, 'id') and item.id == operation.target_item_id and hasattr(item, 'sets'):
                for set_item in item.sets:
                    if set_item.id == operation.target_item_id:
                        for key, value in operation.payload.items():
                            if key in ["reps", "weight", "distance", "duration", "order"] and hasattr(set_item, key):
                                setattr(set_item, key, value)
                        return
        
        raise ValueError(f"Set {operation.target_set_id} not found in exercise {operation.target_item_id}")
    
    async def _delete_set(self, state: ExerciseSessionState, operation: SessionStateOperation):
        """Delete a set in an exercise in a session"""
        if not operation.target_item_id or not operation.target_set_id:
            raise ValueError("target_item_id and target_set_id required for delete_set operation")
        
        for item in state.items:
            if hasattr(item, 'id') and item.id == operation.target_item_id and hasattr(item, 'sets'):
                original_length = len(item.sets)
                item.sets = [s for s in item.sets if s.id != operation.target_set_id]
                
                if len(item.sets) < original_length:
                    return
        
        raise ValueError(f"Set {operation.target_set_id} not found in exercise {operation.target_item_id}")
    
    async def _resolve_conflict(self, current_state: ExerciseSessionState, operation: SessionStateOperation):
        """Resolve version conflicts using operational transformation"""
        conflicts = []
        
        try:
            recent_ops = await self._get_operations_since_version(
                operation.session_id, operation.version
            )
            
            for recent_op_data in recent_ops:
                if recent_op_data.get("account_id") != operation.account_id:
                    conflicts.append({
                        "type": "version_conflict",
                        "conflicting_operation": recent_op_data["operation_id"],
                        "resolution": "last_write_wins"
                    })
        except Exception as e:
            logger.error(f"Error resolving version conflict: {e}")
        
        return conflicts
    
    async def _save_state(self, state: ExerciseSessionState):
        """Save session state to both MongoDB and Redis"""
        await self.mongo.update_one(
            session_states_key,
            {
                "session_id": state.session_id,
                "account_id": state.account_id
            },
            state.dict(by_alias=True),
            upsert=True
        )
        
        await self._cache_state(state)
    
    async def _cache_state(self, state: ExerciseSessionState):
        """Cache state in Redis"""
        cache_key = self._get_state_cache_key(state.session_id, state.account_id)
        await self.redis.setex(cache_key, 3600, state.dict())
    
    async def _log_op(self, operation: SessionStateOperation):
        """Log an operation for conflict resolution"""
        log_key = f"session_ops:{operation.session_id}"
        await self.redis.lpush(log_key, operation.to_dict())
        await self.redis.ltrim(log_key, 0, 999)
        await self.redis.expire(log_key, 86400)
    
    async def _get_ops_since_ver(self, session_id: str, version: int) -> List[Dict[str, Any]]:
        """Log operations since a specific version"""
        log_key = f"{session_ops_key}:{session_id}"
        
        operations = []
        try:

            op_count = await self.redis.llen(log_key)
            
            if op_count > 0:
                for i in range(min(op_count, 100)):
                    op_data = await self.redis.lindex(log_key, i)
                    if op_data:
                        try:
                            if isinstance(op_data, str):
                                op_dict = json.loads(op_data)
                            else:
                                op_dict = op_data
                            
                            if op_dict.get("version", 0) > version:
                                operations.append(op_dict)
                        except (json.JSONDecodeError, TypeError):
                            continue
                
                operations.sort(key=lambda x: x.get("version", 0))
        except Exception as e:
            logger.error(f"Error getting operations since version {version}: {e}")
        
        return operations
    
    async def _broadcast_op(self, operation: SessionStateOperation, conflicts: List[Dict[str, Any]]):
        """Broadcast an operation to other participants"""
        try:
            broadcast_data = {
                "type": "operation",
                "operation": operation.to_dict(),
                "conflicts": conflicts,
                "broadcast_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            channel = f"{session_updates_key}:{operation.session_id}"
            await self.redis.publish(channel, broadcast_data)
            
            logger.debug(f"Broadcasted operation {operation.operation_id} to session {operation.session_id}")
        except Exception as e:
            logger.error(f"Error broadcasting operation: {e}")
    
    async def sync_participants(self, session_id: str) -> Dict[str, Any]:
        """Sync state across all participants in a session"""
        try:
            session = await self.mongo.find_one(session_key, { "_id": session_id })
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            participant_states = {}
            latest_version = 0
            
            for participant in session.get("participants", []):
                participant_id = participant["id"]
                state = await self.get_user_state(session_id, participant_id)
                
                if state:
                    participant_states[participant_id] = {
                        "version": state.version,
                        "updated_at": state.updated_at.isoformat(),
                        "item_count": len(state.items)
                    }
                    
                    latest_version = max(latest_version, state.version)
            
            return {
                "success": True,
                "session_id": session_id,
                "participant_count": len(participant_states),
                "latest_version": latest_version,
                "participant_states": participant_states,
                "sync_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to sync session participants: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def cleanup_session_data(self, session_id: str):
        """Clean up session data when session is complete"""
        try:
            deleted_states = await self.mongo.delete_many(
                session_states_key,
                { "session_id": session_id }
            )
            
            log_key = f"{session_ops_key}:{session_id}"
            await self.redis.delete(log_key)
            
            session = await self.mongo.find_one(
                session_key,
                { "_id": session_id }
            )
            
            if session:
                for participant in session.get("participants", []):
                    cache_key = self._get_state_cache_key(session_id, participant["id"])
                    await self.redis.delete(cache_key)
            
            logger.info(f"Cleaned session data for {session_id}: {deleted_states} removed")
        except Exception as e:
            logger.error(f"Failed to clean up session data for: {session_id}: {e}")
    
    def _get_state_cache_key(self, session_id: str, account_id: str) -> str:
        """Generate session state cache key for Redis"""
        return f"session_state:{session_id}:{account_id}"
    
    async def register_connection(self, session_id: str, connection_id: str):
        """Register a Web Socket connection for updates"""
        if session_id not in self._active_connections:
            self._active_connections[session_id] = set()
        
        self._active_connections[session_id].add(connection_id)
        logger.debug(f"Registered connection {connection_id} for session {session_id}")
    
    async def unregister_connection(self, session_id: str, connection_id: str):
        """Unregister a Web Socket connection from updates"""
        if session_id in self._active_connections:
            self._active_connections[session_id].discard(connection_id)
        
        if not self._active_connections[session_id]:
            del self._active_connections[session_id]
    
    def get_active_connections(self, session_id: str) -> Set[str]:
        """Get all active Web Socket connections for a session"""
        return self._active_connections.get(session_id, set())