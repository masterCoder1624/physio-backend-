import uuid
from datetime import datetime, timezone
from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from app.models.mongo_models import utc_now

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Generic MongoDB repository exposing clean async CRUD operations via Motor."""

    def __init__(self, model: Type[ModelType], db: AsyncIOMotorDatabase, collection_name: str) -> None:
        self.model = model
        self.db = db
        self.collection = db[collection_name]

    async def get_by_id(self, id_val: Any) -> Optional[ModelType]:
        """Fetch a single document by string UUID or ObjectId."""
        doc = await self.collection.find_one({"_id": str(id_val)})
        if not doc:
            doc = await self.collection.find_one({"id": str(id_val)})
        if not doc:
            return None
        return self._doc_to_model(doc)

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ModelType]:
        """Fetch multiple documents with optional query filters and pagination."""
        query = self._clean_filters(filters or {})
        cursor = self.collection.find(query).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._doc_to_model(d) for d in docs]

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count total matching documents in collection."""
        query = self._clean_filters(filters or {})
        return await self.collection.count_documents(query)

    async def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """Insert a new document into collection."""
        doc_data = dict(obj_in)
        if "id" not in doc_data or not doc_data["id"]:
            doc_data["id"] = str(uuid.uuid4())
        doc_data["_id"] = doc_data["id"]
        if "created_at" not in doc_data:
            doc_data["created_at"] = utc_now()
        if "updated_at" not in doc_data:
            doc_data["updated_at"] = utc_now()

        # Convert Pydantic enums or custom objects to primitive values
        cleaned_doc = self._serialize_dict(doc_data)
        await self.collection.insert_one(cleaned_doc)
        return self.model.model_validate(cleaned_doc)

    async def update(
        self, id_val: Any, obj_in: Dict[str, Any]
    ) -> Optional[ModelType]:
        """Update an existing document by ID."""
        doc_data = self._serialize_dict(obj_in)
        doc_data["updated_at"] = utc_now()

        result = await self.collection.find_one_and_update(
            {"$or": [{"_id": str(id_val)}, {"id": str(id_val)}]},
            {"$set": doc_data},
            return_document=True,
        )
        if not result:
            return None
        return self._doc_to_model(result)

    async def delete(self, id_val: Any) -> bool:
        """Delete a document by ID."""
        result = await self.collection.delete_one(
            {"$or": [{"_id": str(id_val)}, {"id": str(id_val)}]}
        )
        return result.deleted_count > 0

    def _doc_to_model(self, doc: Dict[str, Any]) -> ModelType:
        """Map Mongo document dict to Pydantic Model."""
        clean = dict(doc)
        if "_id" in clean and "id" not in clean:
            clean["id"] = str(clean["_id"])
        return self.model.model_validate(clean)

    def _clean_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize query parameters for MongoDB filters."""
        query = {}
        for key, val in filters.items():
            if val is not None:
                query[key] = val
        return query

    def _serialize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize dict elements (enums, datetimes) for PyMongo compatibility."""
        serialized = {}
        for k, v in data.items():
            if hasattr(v, "value"):
                serialized[k] = v.value
            elif isinstance(v, datetime):
                serialized[k] = v
            else:
                serialized[k] = v
        return serialized
