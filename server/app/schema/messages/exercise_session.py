from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timezone
from uuid import uuid4

from app.schema.exercise_session import ExerciseSessionStateItemType, ExerciseSessionItemMeta, ExerciseSessionStateItemMetric, ExerciseSessionParticipantCursor, ExerciseType
from app.services.exercise_session_service import ExerciseSessionOperationType

class ExerciseSessionBasePayload(BaseModel):
    class Config:
        extra="forbid"
        validate_assignment=True
        use_enum_values=True

class SessionJoinPayload(ExerciseSessionBasePayload):
    session_id: str = Field(..., min_length=1, max_length=100)

class SessionLeavePayload(ExerciseSessionBasePayload):
    session_id: str = Field(..., min_length=1, max_length=100)

class SessionUpdatePayload(ExerciseSessionBasePayload):
    session_id: str = Field(..., min_length=1, max_length=100)
    status: Optional[str] = None
    connection_id: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None

class ExercisePayloadData(BaseModel):
    type: ExerciseSessionStateItemType
    rest: Optional[int] = Field(None, ge=0, le=3600)
    meta: List[ExerciseSessionItemMeta]
    participants: Optional[List[str]] = None
    
    class Config:
        use_enum_values=True

class ExerciseSetPayloadData(BaseModel):
    type: ExerciseType
    complete: bool = False
    metrics: ExerciseSessionStateItemMetric
    
    class Config:
        use_enum_values=True

class ExerciseAddPayload(ExerciseSessionBasePayload):
    exercise: ExercisePayloadData

class ExerciseUpdatePayload(ExerciseSessionBasePayload):
    exercise_id: str = Field(..., min_length=1, max_length=100)
    updates: Dict[str, Any] = Field(..., min_items=1)
    
    @validator("updates")
    def validate_updates(cls, v):
        if not isinstance(v, dict):
            raise ValueError("updates must be a dictionary")
        for key in v:
            if key not in {"type", "rest", "meta", "participants"}:
                raise ValueError(f"Invalid update key: {key}")
        return v

class ExerciseDeletePayload(ExerciseSessionBasePayload):
    exercise_id: str = Field(..., min_length=1, max_length=100)

class ExerciseReorderPayload(ExerciseSessionBasePayload):
    exercise_id: str = Field(..., min_length=1, max_length=100)
    new_index: int = Field(..., ge=0)

class SetAddPayload(ExerciseSessionBasePayload):
    exercise_id: str = Field(..., min_length=1, max_length=100)
    set: ExerciseSetPayloadData

class SetUpdatePayload(ExerciseSessionBasePayload):
    exercise_id: str = Field(..., min_length=1, max_length=100)
    set_id: str = Field(..., min_length=1, max_length=100)
    updates: Dict[str, Any] = Field(..., min_items=1)
    
    @validator("updates")
    def validate_updates(cls, v):
        if not isinstance(v, dict):
            raise ValueError("updates must be a dictionary")
        for key in v:
            if key not in {"type", "complete", "metrics"}:
                raise ValueError(f"Invalid update key: {key}")
        return v

class SetDeletePayload(ExerciseSessionBasePayload):
    exercise_id: str = Field(..., min_length=1, max_length=100)
    set_id: str = Field(..., min_length=1, max_length=100)

class SetCompletePayload(ExerciseSessionBasePayload):
    exercise_id: str = Field(..., min_length=1, max_length=100)
    set_id: str = Field(..., min_length=1, max_length=100)

class SetReorderPayload(ExerciseSessionBasePayload):
    exercise_id: str = Field(..., min_length=1, max_length=100)
    set_id: str = Field(..., min_length=1, max_length=100)
    new_index: int = Field(..., ge=0)

class CursorMovePayload(ExerciseSessionBasePayload):
    cursor: ExerciseSessionParticipantCursor

class SyncRequestPayload(ExerciseSessionBasePayload):
    pass

class SyncResponsePayload(ExerciseSessionBasePayload):
    session: Dict[str, Any] = Field(...)
    state: Dict[str, Any] = Field(...)
    participant_states: List[Dict[str, Any]] = Field(default_factory=list)
    version: int = Field(..., ge=0)

class ExerciseSessionOperationPayload(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: ExerciseSessionOperationType
    session_id: str = Field(..., min_length=1, max_length=100)
    account_id: str = Field(..., min_length=1, max_length=100)
    payload: Union[
        SessionJoinPayload,
        SessionLeavePayload,
        SessionUpdatePayload,
        ExerciseAddPayload,
        ExerciseUpdatePayload,
        ExerciseDeletePayload,
        ExerciseReorderPayload,
        SetAddPayload,
        SetUpdatePayload,
        SetDeletePayload,
        SetCompletePayload,
        SetReorderPayload,
        CursorMovePayload,
        SyncRequestPayload,
        SyncResponsePayload,
        Dict[str, Any],
    ]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = Field(default=0, ge=0)
    correlation_id: Optional[str] = None
    instance_id: Optional[str] = None
    
    class Config:
        extra="forbid"
        validate_assignment=True
        use_enum_values=True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

    @root_validator
    def validate_payload_type(cls, values):
        """Validate payload matches operation type"""
        op_type = values.get('type')
        payload = values.get('payload')
        
        if not op_type or payload is None:
            return values
        
        # Map operation types to expected payload types
        payload_mapping = {
            ExerciseSessionOperationType.SESSION_JOIN: SessionJoinPayload,
            ExerciseSessionOperationType.SESSION_LEAVE: SessionLeavePayload,
            ExerciseSessionOperationType.SESSION_UPDATE: SessionUpdatePayload,
            ExerciseSessionOperationType.EXERCISE_ADD: ExerciseAddPayload,
            ExerciseSessionOperationType.EXERCISE_UPDATE: ExerciseUpdatePayload,
            ExerciseSessionOperationType.EXERCISE_DELETE: ExerciseDeletePayload,
            ExerciseSessionOperationType.EXERCISE_REORDER: ExerciseReorderPayload,
            ExerciseSessionOperationType.SET_ADD: SetAddPayload,
            ExerciseSessionOperationType.SET_UPDATE: SetUpdatePayload,
            ExerciseSessionOperationType.SET_DELETE: SetDeletePayload,
            ExerciseSessionOperationType.SET_COMPLETE: SetCompletePayload,
            ExerciseSessionOperationType.SET_REORDER: SetReorderPayload,
            ExerciseSessionOperationType.CURSOR_MOVE: CursorMovePayload,
            ExerciseSessionOperationType.SYNC_REQUEST: SyncRequestPayload,
            ExerciseSessionOperationType.SYNC_RESPONSE: SyncResponsePayload,
        }
        
        expected_payload_type = payload_mapping.get(op_type)
        
        if expected_payload_type and isinstance(payload, expected_payload_type):
            return values
        
        if expected_payload_type and isinstance(payload, dict):
            try:
                validated_payload = expected_payload_type(**payload)
                values['payload'] = validated_payload
            except Exception as e:
                raise ValueError(f"Invalid payload for operation {op_type}: {e}")
        
        return values

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = self.dict()
        data['type'] = self.type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data

    def to_json(self) -> str:
        """Convert to JSON string"""
        return self.json(exclude_none=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExerciseSessionOperationPayload":
        """Create from dictionary with validation"""
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "ExerciseSessionOperationPayload":
        """Create from JSON string with validation"""
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)