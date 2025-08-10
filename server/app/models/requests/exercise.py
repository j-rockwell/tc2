from pydantic import BaseModel
from typing import Optional, List

from app.schema.exercise import ExerciseMuscleGroup, ExerciseEquipment

class ExerciseMetaCreateRequest(BaseModel):
    name: str
    aliases: Optional[List[str]] = None
    muscle_groups: Optional[List[ExerciseMuscleGroup]] = None
    equipment: Optional[List[ExerciseEquipment]] = None