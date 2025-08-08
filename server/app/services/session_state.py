from typing import Optional, Dict, Any, List, Set
from app.db.mongo import Mongo
from app.db.redis import Redis
from app.schema.session import ExerciseSessionState
from app.schema.messages.session import SessionStateOperation
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
        pass
    
    async def get_user_state(self, account_id: str) -> Optional[ExerciseSessionState]:
        """Get current session state for a user"""
        pass
    
    async def apply_operation(self, operation: SessionStateOperation) -> Dict[str, Any]:
        """Apply operation to a session"""
        pass
    
    async def _execute_operation(self, operation: SessionStateOperation, current_state: ExerciseSessionState) -> ExerciseSessionState:
        """Execute an operation on an active session"""
        pass
    
    async def _add_exercise(self, state: ExerciseSessionState, operation: SessionStateOperation):
        """Add an exercise to a session"""
        pass
    
    async def _update_exercise(self, state: ExerciseSessionState, operation: SessionStateOperation):
        """Update an exercise in a session"""
        pass
    
    async def _delete_exercise(self, state: ExerciseSessionState, operation: SessionStateOperation):
        """Delete an exercise from a session"""
        pass
    
    async def _add_set(self, state: ExerciseSessionState, operation: SessionStateOperation):
        """Add a set to an exercise in a session"""
        pass
    
    async def _update_set(self, state: ExerciseSessionState, operation: SessionStateOperation):
        """Update a set in an exercise in a session"""
        pass
    
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