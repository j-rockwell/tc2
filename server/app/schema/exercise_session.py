from typing import Optional, List
from enum import Enum
from bson import ObjectId
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# For more information about this schema, see:
# /server/schemas/exercise.json

class ExerciseSessionStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"

class ExerciseSessionStateItemType(str, Enum):
    SINGLE = "single"
    COMPOUND = "compound"

class ExerciseType(str, Enum):
    WEIGHT_REPS = "weight_reps"
    WEIGHT_TIME = "weight_time"
    DISTANCE_TIME = "distance_time"
    REPS = "reps"
    TIME = "time"
    DISTANCE = "distance"

class ExerciseSetType(str, Enum):
    WARMUP = "warmup"
    WORKING = "working"
    DROP = "drop"
    SUPER = "super"
    FAILURE = "failure"

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

class Duration(BaseModel):
    value: int  # seconds

class Distance(BaseModel):
    value: float
    unit: DistanceUnit = DistanceUnit.METER

    def to_meters(self) -> float:
        conv = {
            DistanceUnit.METER: 1,
            DistanceUnit.KILOMETER: 1000,
            DistanceUnit.MILE: 1609.34,
            DistanceUnit.YARD: 0.9144,
        }
        return self.value * conv[self.unit]

class ExerciseSessionParticipantCursor(BaseModel):
    exercise_id: str
    exercise_set_id: str

class ExerciseSessionParticipant(BaseModel):
    id: str
    color: str
    cursor: Optional[ExerciseSessionParticipantCursor] = None

class ExerciseSessionInvitation(BaseModel):
    invited_by: str
    invited: str
    expires: Optional[datetime] = None

class ExerciseSession(BaseModel):
    name: Optional[str] = None
    status: ExerciseSessionStatus
    owner_id: str
    created_at: datetime
    updated_at: datetime
    participants: List[ExerciseSessionParticipant] = Field(default_factory=list)
    invitations: List[ExerciseSessionInvitation] = Field(default_factory=list)

class ExerciseSessionItemMeta(BaseModel):
    internal_id: str
    name: str
    type: ExerciseType

class ExerciseSessionStateItemMetric(BaseModel):
    reps: Optional[int] = None
    weight: Optional[Weight] = None
    duration: Optional[Duration] = None
    distance: Optional[Distance] = None

class ExerciseSessionStateItemSet(BaseModel):
    id: str
    order: int = 1
    metrics: ExerciseSessionStateItemMetric
    type: ExerciseSetType
    complete: bool = False

class ExerciseSessionStateItem(BaseModel):
    id: str
    order: int = 1
    participants: List[str] = Field(default_factory=list)
    type: ExerciseSessionStateItemType
    rest: Optional[int] = None
    meta: List[ExerciseSessionItemMeta] = Field(default_factory=list)
    sets: List[ExerciseSessionStateItemSet] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)

class ExerciseSessionState(BaseModel):
    session_id: str
    account_id: str
    version: int = 0
    items: List[ExerciseSessionStateItem] = Field(default_factory=list)

class ExerciseSessionInDB(ExerciseSession):
    id: Optional[str] = Field(default=None, alias="_id")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
        }