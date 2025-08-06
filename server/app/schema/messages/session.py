from pydantic import BaseModel, Extra
from typing import Any, Dict, Optional
from enum import Enum

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