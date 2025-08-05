from uuid import uuid4
from enum import Enum
from bson import ObjectId
from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict, Any, Set
from datetime import datetime
import time

class ExerciseType(str, Enum):
    WEIGHT_REPS = "weight_reps"
    WEIGHT_TIME = "weight_time"
    DISTANCE_TIME = "distance_time"
    REPS = "reps"
    TIME = "time"
    DISTANCE = "distance"

class SessionStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETE = "complete"

class SessionType(str, Enum):
    INDIVIDUAL = "individual"
    COLLABORATE = "collaborate"

class ParticipantRole(str, Enum):
    OWNER = "owner"
    EDITOR = "editor"
    PARTICIPANT = "participant"
    VIEWER = "viewer"

class ParticipantStatus(str, Enum):
    INVITED = "invited"
    JOINED = "joined"
    ACTIVE = "active"
    RESTING = "resting"
    DISCONNECTED = "disconnected"
    COMPLETED = "completed"

class ParticipantInviteStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"

class OperationType(str, Enum):
    INSERT_EXERCISE = "insert_exercise"
    UPDATE_EXERCISE = "update_exercise"
    DELETE_EXERCISE = "delete_exercise"
    INSERT_SET = "insert_set"
    UPDATE_SET = "update_set"
    DELETE_SET = "delete_set"
    UPDATE_STATUS = "update_status"
    UPDATE_PARTICIPANT = "update_participant"

class WeightUnit(str, Enum):
    KILOGRAM = "kg"
    POUND = "lb"

class DistanceUnit(str, Enum):
    METER = "m"
    KILOMETER = "km"
    MILE = "mi"
    YARD = "yd"

@dataclass
class Participant:
    user_id: ObjectId
    username: str
    avatar_url: Optional[str] = None
    role: ParticipantRole = ParticipantRole.PARTICIPANT
    status: ParticipantStatus = ParticipantStatus.INVITED
    invited_at: datetime = field(default_factory=datetime.now)
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None
    last_seen: datetime = field(default_factory=datetime.now)
    current_exercise_id: Optional[str] = None
    current_set_id: Optional[str] = None
    color: str = "#3B82F6"  # For collaborative UI
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.user_id),
            "username": self.username,
            "avatar_url": self.avatar_url,
            "role": self.role.value,
            "status": self.status.value,
            "invited_at": self.invited_at.isoformat(),
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "left_at": self.left_at.isoformat() if self.left_at else None,
            "last_seen": self.last_seen.isoformat(),
            "current_exercise_id": self.current_exercise_id,
            "current_set_id": self.current_set_id,
            "color": self.color
        }

@dataclass
class Operation:
    id: str = field(default_factory=lambda: str(uuid4()))
    type: OperationType
    user_id: str
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)
    version: int = 0
    parent_version: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "user_id": self.user_id,
            "timestamp": self.timestamp,
            "data": self.data,
            "version": self.version,
            "parent_version": self.parent_version
        }

@dataclass
class Weight:
    value: float
    unit: WeightUnit = WeightUnit.POUND
    
    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Weight must be a non-negative value")
    
    def to_kg(self) -> float:
        if self.unit == WeightUnit.POUND:
            return self.value * 0.453592
        return self.value
    
    def to_lb(self) -> float:
        if self.unit == WeightUnit.KILOGRAM:
            return self.value * 2.20462
        return self.value
    
    def __str__(self) -> str:
        return f"{self.value}{self.unit.value}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value, "unit": self.unit}

@dataclass
class Distance:
    value: float
    unit: DistanceUnit = DistanceUnit.METER
    
    def __post__init__(self):
        if self.value < 0:
            raise ValueError("Distance must be a non-negative value")
    
    def to_meters(self) -> float:
        conversions = {
            DistanceUnit.METER: 1,
            DistanceUnit.KILOMETER: 1000,
            DistanceUnit.MILE: 1609.34,
            DistanceUnit.YARD: 0.9144
        }
        return self.value * conversions[self.unit]
    
    def __str__(self) -> str:
        return f"{self.value}{self.unit.value}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value, "unit": self.unit}

class Duration:
    value: int
    
    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Duration must be a non-negative value")
    
    @classmethod
    def from_time(cls, hours: int = 0, minutes: int = 0, seconds: int = 0, milliseconds: int = 0) -> 'Duration':
        total_ms = (hours * 3600 * 1000) + (minutes * 60 * 1000) + (seconds * 1000) + milliseconds
        return cls(milliseconds=total_ms)
    
    def __str__(self) -> str:
        if self.hours > 0:
            return f"{self.hours}h {self.minutes}m {self.seconds}s"
        elif self.minutes > 0:
            if self.ms > 0:
                return f"{self.minutes}m {self.seconds}.{self.ms:03d}s"
            return f"{self.minutes}m {self.seconds}s"
        elif self.seconds > 0:
            if self.ms > 0:
                return f"{self.seconds}.{self.ms:03d}s"
            return f"{self.seconds}s"
        else:
            return f"0.{self.ms:03d}s"
    
    def format(self, include_ms: bool = True) -> str:
        if not include_ms:
            if self.hours > 0:
                return f"{self.hours}:{self.minutes:02d}:{self.seconds:02d}"
            else:
                return f"{self.minutes}:{self.seconds:02d}"
        else:
            if self.hours > 0:
                return f"{self.hours}:{self.minutes:02d}:{self.seconds:02d}.{self.ms:03d}"
            else:
                return f"{self.minutes}:{self.seconds:02d}.{self.ms:03d}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {"milliseconds": self.value}

@dataclass
class DropsetItem:
    reps: int
    weight: Optional[Weight] = None
    order: int = 1
    
    def __post_init__(self):
        if self.reps < 0:
            raise ValueError("Reps must be a non-negative value")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "reps": self.reps,
            "weight": self.weight.to_dict() if self.weight else None,
            "order": self.order
        }

@dataclass
class SupersetItem:
    exercise_name: str
    exercise_type: ExerciseType
    reps: Optional[int] = None
    weight: Optional[Weight] = None
    distance: Optional[Distance] = None
    duration: Optional[Duration] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "exercise_name": self.exercise_name,
            "exercise_type": self.exercise_type.value,
            "reps": self.reps,
            "weight": self.weight.to_dict() if self.weight else None,
            "distance": self.distance.to_dict() if self.distance else None,
            "duration": self.duration.to_dict() if self.duration else None
        }

@dataclass
class SetData:
    id: str = field(default_factory=lambda: str(uuid4()))
    set_number: int = 1
    reps: Dict[ObjectId, int] = field(default_factory=dict)
    weight: Dict[ObjectId, Weight] = field(default_factory=dict)
    distance: Dict[ObjectId, Distance] = field(default_factory=dict)
    duration: Dict[ObjectId, Duration] = field(default_factory=dict)
    dropsets: Dict[ObjectId, List[DropsetItem]] = field(default_factory=dict)
    supersets: Dict[ObjectId, List[SupersetItem]] = field(default_factory=dict)
    completed_at: Dict[ObjectId, datetime] = field(default_factory=dict)
    notes: Dict[ObjectId, str] = field(default_factory=dict)
    rest_time: Dict[ObjectId, int] = field(default_factory=dict)
    locked_by: Optional[ObjectId] = None
    locked_at: Optional[datetime] = None
    version: int = 0
    
    def set_data_for_user(self, user_id: ObjectId, reps: Optional[int] = None, 
                         weight: Optional[Weight] = None, distance: Optional[Distance] = None,
                         duration: Optional[Duration] = None, rest_time: Optional[int] = None):
        if reps is not None:
            self.reps[user_id] = reps
        if weight is not None:
            self.weight[user_id] = weight
        if distance is not None:
            self.distance[user_id] = distance
        if duration is not None:
            self.duration[user_id] = duration
        if rest_time is not None:
            self.rest_time[user_id] = rest_time
        self.version += 1
    
    def add_dropset(self, user_id: ObjectId, reps: int, weight: Optional[Weight] = None) -> DropsetItem:
        if user_id not in self.dropsets:
            self.dropsets[user_id] = []
        
        order = len(self.dropsets[user_id]) + 1
        dropset = DropsetItem(reps=reps, weight=weight, order=order)
        self.dropsets[user_id].append(dropset)
        self.version += 1
        return dropset
    
    def add_superset(self, user_id: ObjectId, exercise_name: str, exercise_type: ExerciseType,
                    reps: Optional[int] = None, weight: Optional[Weight] = None,
                    distance: Optional[Distance] = None, duration: Optional[Duration] = None) -> SupersetItem:
        if user_id not in self.supersets:
            self.supersets[user_id] = []
        
        superset = SupersetItem(
            exercise_name=exercise_name,
            exercise_type=exercise_type,
            reps=reps,
            weight=weight,
            distance=distance,
            duration=duration
        )
        self.supersets[user_id].append(superset)
        self.version += 1
        return superset
    
    def mark_completed(self, user_id: ObjectId):
        self.completed_at[user_id] = datetime.now()
        self.version += 1
    
    def is_completed_by(self, user_id: ObjectId) -> bool:
        return user_id in self.completed_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "set_number": self.set_number,
            "reps": {str(uid): val for uid, val in self.reps.items()},
            "weight": {str(uid): w.to_dict() for uid, w in self.weight.items()},
            "distance": {str(uid): d.to_dict() for uid, d in self.distance.items()},
            "duration": {str(uid): d.to_dict() for uid, d in self.duration.items()},
            "dropsets": {str(uid): [ds.to_dict() for ds in dsets] for uid, dsets in self.dropsets.items()},
            "supersets": {str(uid): [ss.to_dict() for ss in ssets] for uid, ssets in self.supersets.items()},
            "completed_at": {str(uid): dt.isoformat() for uid, dt in self.completed_at.items()},
            "rest_time": {str(uid): time for uid, time in self.rest_time.items()},
            "locked_by": str(self.locked_by) if self.locked_by else None,
            "locked_at": self.locked_at.isoformat() if self.locked_at else None,
            "version": self.version
        }

@dataclass
class Exercise:
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str
    type: ExerciseType
    sets: List[SetData] = field(default_factory=list)
    created_by: ObjectId = None
    assigned_to: Set[ObjectId] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    modified_by: ObjectId = None
    modified_at: datetime = field(default_factory=datetime.now)
    order: int = 0
    version: int = 0
    muscle_groups: List[str] = field(default_factory=list)
    equipment: Optional[str] = None
    user_notes: Dict[ObjectId, str] = field(default_factory=dict)
    
    def add_set(self) -> SetData:
        set_number = len(self.sets) + 1
        new_set = SetData(set_number=set_number)
        self.sets.append(new_set)
        self.version += 1
        return new_set
    
    def remove_set(self, set_id: str) -> bool:
        initial_length = len(self.sets)
        self.sets = [s for s in self.sets if s.id != set_id]
        
        for i, set_data in enumerate(self.sets):
            set_data.set_number = i + 1
        
        if len(self.sets) < initial_length:
            self.version += 1
            return True
        return False
    
    def assign_to_user(self, user_id: ObjectId):
        self.assigned_to.add(user_id)
        self.version += 1
    
    def add_note(self, user_id: ObjectId, note: str):
        self.user_notes[user_id] = note
        self.modified_by = user_id
        self.modified_at = datetime.now()
        self.version += 1
    
    def get_note(self, user_id: ObjectId) -> Optional[str]:
        return self.user_notes.get(user_id)
    
    def get_user_progress(self, user_id: ObjectId) -> Dict[str, Any]:
        completed_sets = sum(1 for s in self.sets if s.is_completed_by(user_id))
        return {
            "completed_sets": completed_sets,
            "total_sets": len(self.sets),
            "percentage": (completed_sets / len(self.sets) * 100) if self.sets else 0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "sets": [s.to_dict() for s in self.sets],
            "created_by": str(self.created_by) if self.created_by else None,
            "assigned_to": [str(uid) for uid in self.assigned_to],
            "created_at": self.created_at.isoformat(),
            "modified_by": str(self.modified_by) if self.modified_by else None,
            "modified_at": self.modified_at.isoformat(),
            "order": self.order,
            "version": self.version,
            "muscle_groups": self.muscle_groups,
            "equipment": self.equipment,
            "notes": {str(uid): note for uid, note in self.user_notes.items()}
        }

@dataclass
class SessionInvite:
    id: str = field(default_factory=lambda: str(uuid4()))
    session_id: str
    invited_by: ObjectId
    invited_user: ObjectId
    role: ParticipantRole = ParticipantRole.PARTICIPANT
    status: ParticipantInviteStatus = ParticipantInviteStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "invited_by": str(self.invited_by),
            "invited_user": str(self.invited_user),
            "role": self.role.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }
        
@dataclass
class TrainingSession:
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str
    type: SessionType = SessionType.INDIVIDUAL
    status: SessionStatus = SessionStatus.DRAFT
    owner_id: ObjectId = None
    participants: Dict[ObjectId, Participant] = field(default_factory=dict)
    exercises: List[Exercise] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    is_template: bool = False
    allow_participant_edits: bool = False
    sync_required: bool = False
    version: int = 0
    last_modified: datetime = field(default_factory=datetime.now)
    
    def is_collaborative(self) -> bool:
        return self.type == SessionType.COLLABORATIVE
    
    def add_participant(self, user_id: ObjectId, username: str, 
                       role: ParticipantRole = ParticipantRole.PARTICIPANT) -> Optional[Participant]:
        if not self.is_collaborative():
            return None
            
        if len(self.participants) >= 4:
            raise ValueError(f"Session has reached maximum participants")
        
        participant = Participant(
            user_id=user_id,
            username=username,
            role=role,
            status=ParticipantStatus.ACCEPTED,
            joined_at=datetime.now()
        )
        self.participants[user_id] = participant
        self.version += 1
        self.last_modified = datetime.now()
        
        if self.sync_required:
            for exercise in self.exercises:
                exercise.assign_to_user(user_id)
        
        return participant
    
    def remove_participant(self, user_id: ObjectId):
        if user_id in self.participants:
            self.participants[user_id].status = ParticipantStatus.LEFT
            self.participants[user_id].left_at = datetime.now()
            
            for exercise in self.exercises:
                exercise.unassign_from_user(user_id)
            
            self.version += 1
            self.last_modified = datetime.now()
    
    def can_user_edit_exercises(self, user_id: ObjectId) -> bool:
        if user_id == self.owner_id:
            return True
        
        if not self.is_collaborative():
            return False
        
        participant = self.participants.get(user_id)
        if not participant:
            return False
        
        if participant.role in [ParticipantRole.OWNER, ParticipantRole.EDITOR]:
            return True
        
        return participant.role == ParticipantRole.PARTICIPANT and self.allow_participant_edits
    
    def add_exercise(self, exercise: Exercise, assign_to_all: bool = True) -> Exercise:
        exercise.order = len(self.exercises)
        
        if not self.is_collaborative():
            exercise.assigned_to = {self.owner_id}
        elif assign_to_all and self.sync_required:
            exercise.assigned_to = {self.owner_id}
            for uid, participant in self.participants.items():
                if participant.status in [ParticipantStatus.ACCEPTED, ParticipantStatus.ACTIVE]:
                    exercise.assigned_to.add(uid)
        
        self.exercises.append(exercise)
        self.version += 1
        self.last_modified = datetime.now()
        return exercise
    
    def remove_exercise(self, exercise_id: str) -> bool:
        initial_length = len(self.exercises)
        self.exercises = [e for e in self.exercises if e.id != exercise_id]
        
        for i, exercise in enumerate(self.exercises):
            exercise.order = i
        
        if len(self.exercises) < initial_length:
            self.version += 1
            self.last_modified = datetime.now()
            return True
        return False
    
    def get_user_exercises(self, user_id: ObjectId) -> List[Exercise]:
        return [e for e in self.exercises if user_id in e.assigned_to]
    
    def get_progress_summary(self) -> Dict[str, Any]:
        if not self.is_collaborative():
            total_exercises = len(self.exercises)
            completed_exercises = 0
            total_sets = 0
            completed_sets = 0
            
            for exercise in self.exercises:
                progress = exercise.get_user_progress(self.owner_id)
                if progress["percentage"] == 100:
                    completed_exercises += 1
                total_sets += progress["totalSets"]
                completed_sets += progress["completedSets"]
            
            return {
                "total_exercises": total_exercises,
                "completed_exercises": completed_exercises,
                "total_sets": total_sets,
                "completed_sets": completed_sets,
                "overall_percentage": (completed_sets / total_sets * 100) if total_sets else 0
            }
        else:
            progress_by_user = {}
            
            for uid in [self.owner_id] + list(self.participants.keys()):
                user_exercises = self.get_user_exercises(uid)
                total_exercises = len(user_exercises)
                completed_exercises = 0
                total_sets = 0
                completed_sets = 0
                
                for exercise in user_exercises:
                    progress = exercise.get_user_progress(uid)
                    if progress["percentage"] == 100:
                        completed_exercises += 1
                    total_sets += progress["total_sets"]
                    completed_sets += progress["completed_sets"]
                
                progress_by_user[str(uid)] = {
                    "total_exercises": total_exercises,
                    "completed_exercises": completed_exercises,
                    "total_sets": total_sets,
                    "completed_sets": completed_sets,
                    "overall_percentage": (completed_sets / total_sets * 100) if total_sets else 0
                }
            
            return progress_by_user
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "status": self.status.value,
            "owner_id": str(self.owner_id) if self.owner_id else None,
            "exercises": [e.to_dict() for e in self.exercises],
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "description": self.description,
            "tags": self.tags,
            "template": self.is_template,
            "version": self.version,
            "last_modified": self.last_modified.isoformat(),
            "progress": self.get_progress_summary()
        }
        
        if self.is_collaborative():
            base_dict.update({
                "participants": {str(uid): p.to_dict() for uid, p in self.participants.items()},
                "allow_participant_edits": self.allow_participant_edits,
                "sync_required": self.sync_required,
                "active_participants": sum(1 for p in self.participants.values() 
                                        if p.status == ParticipantStatus.ACTIVE)
            })
        
        return base_dict