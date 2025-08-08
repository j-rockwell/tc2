from pydantic import BaseModel, Extra
from typing import Any, Dict, Optional
from enum import Enum
from datetime import datetime, timezone

class SessionOperationType(str, Enum):
    ADD_EXERCISE = "add_exercise"
    UPDATE_EXERCISE = "update_exercise"
    DELETE_EXERCISE = "delete_exercise"
    ADD_SET = "add_set"
    UPDATE_SET = "update_set"
    DELETE_SET = "delete_set"
    UPDATE_STATUS = "update_status"
    UPDATE_PARTICIPANT = "update_participant"

class SessionOperationMessage(BaseModel):
    action: SessionOperationType
    payload: Dict[str, Any]

class AddExercisePayload(BaseModel):
    exercise: str
    
    class Config:
        extra = Extra.forbid

class SessionStateOperation:
    def __init__(
        self,
        operation_id: str,
        session_id: str,
        account_id: str,
        operation_type: SessionOperationType,
        payload: Dict[str, Any],
        target_item_id: Optional[str] = None,
        target_set_id: Optional[str] = None,
        version: int = 0,
        timestamp: Optional[datetime] = None,
    ):
        self.operation_id = operation_id
        self.session_id = session_id
        self.account_id = account_id
        self.operation_type = operation_type
        self.payload = payload or {}
        self.target_item_id = target_item_id
        self.target_set_id = target_set_id
        self.version = version
        self.timestamp = timestamp or datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "session_id": self.session_id,
            "account_id": self.account_id,
            "operation_type": self.operation_type,
            "payload": self.payload,
            "target_item_id": self.target_item_id,
            "target_set_id": self.target_set_id,
            "version": self.version,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionStateOperation":
        return cls(
            operation_id=data["operation_id"],
            session_id=data["session_id"],
            account_id=data["account_id"],
            operation_type=SessionOperationType(data["operation_type"]),
            payload=data.get("data", {}),
            target_item_id=data.get("target_item_id"),
            target_set_id=data.get("target_set_id"),
            version=data.get("version", 0),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None
        )