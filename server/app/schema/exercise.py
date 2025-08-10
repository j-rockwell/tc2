from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional, List
from enum import Enum
from datetime import datetime

class ExerciseEquipment(str, Enum):
    BARBELL = "barbell"
    DUMBBELL = "dumbbell"
    MACHINE = "machine"
    KETTLEBELL = "kettlebell"

class ExerciseMuscleGroup(str, Enum):
    NECK = "neck"
    SHOULDERS = "shoulders"
    UPPER_ARMS = "upper_arms"
    FOREARMS = "forearms"
    BACK = "back"
    CHEST = "chest"
    THIGHTS = "thighs"
    GLUTES = "glutes"
    CALVES = "calves"

class ExerciseMeta(BaseModel):
    name: str
    created_by: Optional[str]
    aliases: Optional[List[str]]
    muscle_groups = Optional[List[ExerciseMuscleGroup]]
    equipment = Optional[ExerciseEquipment]
    verified: bool
    created_at: datetime
    updated_at: datetime

class ExerciseMetaInDB(ExerciseMeta):
    id: Optional[str] = Field(default=None, alias="_id")
    uses: int = 0

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
        }