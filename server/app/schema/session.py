from enum import Enum
from bson import ObjectId
from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class ExerciseType(str, Enum):
    WEIGHT_REPS = "weight_reps"
    WEIGHT_TIME = "weight_time"
    DISTANCE_TIME = "distance_time"
    REPS = "reps"
    TIME = "time"
    DISTANCE = "distance"

class ExerciseSessionStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETE = "complete"

class WeightUnit(str, Enum):
    KILOGRAM = "kg"
    POUND = "lb"

class DistanceUnit(str, Enum):
    METER = "m"
    KILOMETER = "km"
    MILE = "mi"
    YARD = "yd"

class Weight(BaseModel):
    value: float
    unit: WeightUnit = WeightUnit.POUND
    
    def to_kg(self) -> float:
        return self.value * 0.453592 if self.unit == WeightUnit.POUND else self.value
    
    def to_lb(self) -> float:
        return self.value * 2.20462 if self.unit == WeightUnit.KILOGRAM else self.value
    
    def __str__(self) -> str:
        return f"{self.value}{self.unit.value}"
    
    class Config:
        use_enum_values = True

class Distance(BaseModel):
    value: float = Field(..., ge=0, description="Non-negative distance")
    unit: DistanceUnit = Field(DistanceUnit.METER)

    def to_meters(self) -> float:
        conv = {
            DistanceUnit.METER:     1,
            DistanceUnit.KILOMETER: 1000,
            DistanceUnit.MILE:      1609.34,
            DistanceUnit.YARD:      0.9144,
        }
        return self.value * conv[self.unit]

    def __str__(self) -> str:
        return f"{self.value}{self.unit.value}"

    class Config:
        use_enum_values = True

class Duration(BaseModel):
    value: int
    
class ExerciseSet(BaseModel):
    id: str
    order: int = Field(1, ge=1, description="Position in exercise sequence")
    reps: Optional[int] = None
    weight: Optional[Weight] = None
    distance: Optional[Distance] = None
    duration: Optional[Duration] = None
    drop_sets: List['ExerciseSet'] = Field(default_factory=list, description="Nested drop sets")
    
    class Config:
        arbitrary_types_allowed = True
        orm_mode = True

ExerciseSet.update_forward_refs()
    
class ExerciseItem(BaseModel):
    kind: Literal['exercise'] = Field('exercise', const=True)
    id: str
    name: str
    sets: List[ExerciseSet] = Field(default_factory=list)
    note: Optional[str] = None

class ExerciseSuperSetItem(BaseModel):
    kind: Literal['superset'] = Field('superset', const=True)
    id: str
    exercises: List[ExerciseItem] = Field(..., description="Exercises in this superset in order")
    note: Optional[str] = None

SessionItem = Union[ExerciseItem, ExerciseSuperSetItem]

class ExerciseSessionState(BaseModel):
    session_id: str = Field(..., description="Session ID")
    account_id: str = Field(..., description="Account this state belongs to")
    version: int = Field(0, description="Optimistic concurrency version")
    items: List[SessionItem] = Field(default_factory=list, description="Exercises stored in this state")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of last state update")
    
    class Config:
        orm_mode = True

class ExerciseSessionParticipantCursor(BaseModel):
    item_id: str = Field(..., description="ID of current session item selected")
    set_id: Optional[str] = Field(None, description="ID of the current set within the exercise item")

class ExerciseSessionParticipant(BaseModel):
    id: str = Field(..., description="Owner ID")
    color: str = Field(..., description="Hex color code for participant")
    cursor: Optional[ExerciseSessionParticipantCursor] = Field(None, description="Participant's current cursor position")

class ExerciseSessionInvite(BaseModel):
    invited_id: str = Field(..., description="Account ID of the user that has been invited")
    invited_by: str = Field(..., description="Account ID of the user that sent the invite")
    invited_at: datetime = Field(default_factory=datetime.utcnow)
    
class ExerciseSession(BaseModel):
    owner_id: str = Field(..., description="Session Owner ID")
    status: ExerciseSessionStatus = Field(ExerciseSessionStatus.DRAFT, description="This sessions current status")
    participants: List[ExerciseSessionParticipant] = Field(default_factory=list, description="Participants in this Session")
    invites: List[ExerciseSessionInvite] = Field(default_factory=list, description="List of users that have been invited to this session")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of session creation")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of last session update")
    
    class Config:
        orm_mode = True

class ExerciseSessionInDB(ExerciseSession):
    id: Optional[str] = Field(default=None, alias="_id")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
        }