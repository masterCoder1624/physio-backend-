import pytest
from typing import AsyncGenerator, Dict, Any, List
from httpx import AsyncClient, ASGITransport
from main import app
from app.database.session import get_db


class MockMongoCollection:
    """In-memory mock for MongoDB collections used in tests."""

    def __init__(self):
        self.docs: List[Dict[str, Any]] = []

    async def find_one(self, query: Dict[str, Any]):
        for d in self.docs:
            match = True
            for k, v in query.items():
                if k == "$or":
                    or_match = any(
                        d.get(cond_k) == cond_v
                        for cond in v
                        for cond_k, cond_v in cond.items()
                    )
                    if not or_match:
                        match = False
                        break
                elif d.get(k) != v:
                    match = False
                    break
            if match:
                return dict(d)
        return None

    def find(self, query: Dict[str, Any]):
        return self

    def skip(self, n: int):
        return self

    def limit(self, n: int):
        return self

    async def to_list(self, length: int) -> List[Dict[str, Any]]:
        return [dict(d) for d in self.docs[:length]]

    async def count_documents(self, query: Dict[str, Any]) -> int:
        return len(self.docs)

    async def insert_one(self, doc: Dict[str, Any]):
        self.docs.append(dict(doc))
        return self

    async def find_one_and_update(
        self, query: Dict[str, Any], update: Dict[str, Any], return_document=True
    ):
        doc = await self.find_one(query)
        if doc and "$set" in update:
            for k, v in update["$set"].items():
                doc[k] = v
            for i, d in enumerate(self.docs):
                if d.get("id") == doc.get("id") or d.get("_id") == doc.get("_id"):
                    self.docs[i] = doc
            return dict(doc)
        return None

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any]):
        doc = await self.find_one(query)
        if doc and "$set" in update:
            for k, v in update["$set"].items():
                doc[k] = v
        return self

    async def delete_one(self, query: Dict[str, Any]):
        class DeleteResult:
            deleted_count = 1

        return DeleteResult()

    async def create_index(self, *args, **kwargs):
        """No-op mock for index creation."""
        pass


class MockMongoDatabase:
    """In-memory mock MongoDB database for integration tests."""

    def __init__(self):
        self.collections: Dict[str, MockMongoCollection] = {}

    def __getitem__(self, name: str) -> MockMongoCollection:
        if name not in self.collections:
            self.collections[name] = MockMongoCollection()
        return self.collections[name]


# Shared mock database instance (reset between test sessions by module reload)
mock_db = MockMongoDatabase()


async def override_get_db():
    yield mock_db


# Override FastAPI DB dependency with in-memory mock
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
