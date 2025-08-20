from pydantic import BaseModel
from typing import Optional, List

from app.schema.exercise import ExerciseMuscleGroup, ExerciseEquipment
from app.schema.exercise_session import ExerciseType

class ExerciseMetaCreateRequest(BaseModel):
    name: str
    type: ExerciseType
    aliases: Optional[List[str]] = None
    muscle_groups: Optional[List[ExerciseMuscleGroup]] = None
    equipment: Optional[ExerciseEquipment] = None