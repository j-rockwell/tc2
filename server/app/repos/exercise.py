from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import logging
import re

from app.db.redis import Redis
from app.db.mongo import Mongo
from app.schema.exercise import ExerciseMeta, ExerciseMuscleGroup, ExerciseMetaInDB, ExerciseEquipment

logger = logging.getLogger(__name__)
meta_collection_name = "exercise_meta"

class ExerciseMetaRepository:
    def __init__(self, mongo: Mongo, redis: Redis):
        self.mongo = mongo
        self.redis = redis
    
    async def get_exercise_by_id(self, id: str) -> Optional[ExerciseMetaInDB]:
        try:
            doc = await self.mongo.find_one_by_id(
                collection=meta_collection_name, 
                document_id=id
            )
            
            if doc:
                exercise = ExerciseMetaInDB(**doc)
                return exercise
            
            return None
        except Exception as e:
            logger.error(f"Failed to get exercise by ID {id}: {e}")
            return None
    
    async def get_exercise_by_name(self, name: str) -> Optional[ExerciseMeta]:
        try:
            doc = await self.mongo.find_one(
                collection=meta_collection_name,
                filter_dict={"name": {"$regex": f"^{re.escape(name)}$", "$options": "i"}}
            )
            
            if doc:
                exercise = ExerciseMetaInDB(**doc)
                return exercise
            
            return None
        except Exception as e:
            logger.error(f"Failed to get exercise by name {name}: {e}")
            return None
    
    async def get_exercises_by_fuzzy_search(
        self, 
        query: str, 
        limit: int = 20,
        include_aliases: bool = True
    ) -> List[ExerciseMetaInDB]:
        try:
            if len(query.strip()) < 2:
                return []
            
            escaped_query = re.escape(query.strip())
            search_conditions = [
                {"name": {"$regex": escaped_query, "$options": "i"}}
            ]
            
            if include_aliases:
                search_conditions.append(
                    {"aliases": {"$regex": escaped_query, "$options": "i"}}
                )
            
            filter_dict = {"$or": search_conditions}
            
            docs = await self.mongo.find_many(
                collection=meta_collection_name,
                filter_dict=filter_dict,
                sort=[("verified", -1), ("name", 1)],
                limit=limit
            )
            
            exercises = [ExerciseMetaInDB(**doc) for doc in docs]
            return exercises
        except Exception as e:
            logger.error(f"Failed to search exercises with query '{query}': {e}")
            return []
    
    async def get_exercises_by_muscle_group(
        self, 
        muscle_group: ExerciseMuscleGroup,
        limit: int = 50,
        verified_only: bool = False
    ) -> List[ExerciseMetaInDB]:
        try:
            filter_dict = {"muscle_groups": muscle_group.value}
            if verified_only:
                filter_dict["verified"] = True # type: ignore
            
            docs = await self.mongo.find_many(
                collection=meta_collection_name,
                filter_dict=filter_dict,
                sort=[("verified", -1), ("name", 1)],
                limit=limit
            )
            
            exercises = [ExerciseMetaInDB(**doc) for doc in docs]
            return exercises
        except Exception as e:
            logger.error(f"Failed to get exercises by muscle group {muscle_group}: {e}")
            return []

    async def get_exercises_by_equipment(
        self,
        equipment: ExerciseEquipment,
        limit: int = 50
    ) -> List[ExerciseMetaInDB]:
        try:
            docs = await self.mongo.find_many(
                collection=meta_collection_name,
                filter_dict={"equipment": equipment.value},
                sort=[("verified", -1), ("name", 1)],
                limit=limit
            )
            
            exercises = [ExerciseMetaInDB(**doc) for doc in docs]
            
            return exercises
            
        except Exception as e:
            logger.error(f"Failed to get exercises by equipment {equipment}: {e}")
            return []
    
    async def create_exercise(
        self,
        name: str,
        created_by: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        muscle_groups: Optional[List[ExerciseMuscleGroup]] = None,
        equipment: Optional[ExerciseEquipment] = None,
        verified: bool = False,
    ) -> Optional[ExerciseMetaInDB]:
        try:
            existing = await self.get_exercise_by_name(name)
            if existing:
                return None
            
            now = datetime.now(timezone.utc)
            new_meta = ExerciseMeta(
                name=name,
                created_by=created_by,
                aliases=aliases,
                muscle_groups=muscle_groups,
                equipment=equipment,
                verified=verified,
                created_at=now,
                updated_at=now
            )
            
            inserted = await self.mongo.insert(collection=meta_collection_name, document=new_meta.dict(exclude_none=True))
            in_db = await self.mongo.find_one_by_id(collection=meta_collection_name, document_id=inserted)
            
            if in_db:
                return ExerciseMetaInDB(**in_db)
            
            return None
        except Exception as e:
            logger.error(f"Failed to create new exercise meta: {e}")
            return None
    
    
    async def update_exercise(
        self,
        exercise_id: str,
        updates: Dict[str, Any]
    ) -> Optional[ExerciseMetaInDB]:
        try:
            existing = await self.get_exercise_by_id(exercise_id)
            if not existing:
                logger.warning(f"Exercise with ID '{exercise_id}' not found")
                return None
            
            updates["updated_at"] = datetime.now(timezone.utc)
            
            result = await self.mongo.update_by_id(
                collection=meta_collection_name,
                document_id=exercise_id,
                update={"$set": updates}
            )
            
            if result.get("modified_count", 0) > 0:
                doc = await self.mongo.find_one_by_id(
                    collection=meta_collection_name,
                    document_id=exercise_id
                )
                
                if doc:
                    exercise = ExerciseMetaInDB(**doc)
                    return exercise
            
            return existing
            
        except Exception as e:
            logger.error(f"Failed to update exercise {exercise_id}: {e}")
            return None
    
    async def delete_exercise(
        self,
        exercise_id: str
    ) -> bool:
        try:
            existing = await self.get_exercise_by_id(exercise_id)
            if not existing:
                logger.warning(f"Exercise with ID '{exercise_id}' not found")
                return False
            
            result = await self.mongo.update_by_id(
                collection=meta_collection_name,
                document_id=exercise_id,
                update={
                    "$set": {
                        "active": False,
                        "deleted_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.get("modified_count", 0) > 0:
                logger.info(f"Deleted exercise: {existing.name} (ID: {exercise_id})")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Failed to delete exercise {exercise_id}: {e}")
            return False