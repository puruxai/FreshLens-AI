import os
import sys
import asyncio
from typing import AsyncGenerator
from datetime import datetime
from unittest.mock import MagicMock, patch

# 1. Set environment variables for testing before importing settings
os.environ["SECRET_KEY"] = "test_secret_key_for_testing_purposes_only_1234"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["MODEL_PATH"] = "ml/models/freshness_model.pt"
os.environ["DEMO_MODE"] = "False"

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import Base, get_db

@pytest_asyncio.fixture(scope="session")
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(
        bind=db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture(autouse=True)
async def auto_clean_db(db_engine):
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

@pytest.fixture(autouse=True)
def mock_cv_pipeline():
    from app.modules.image_analysis.router import model_pipeline
    original_analyze = model_pipeline.analyze_image
    
    def dummy_analyze(image_path: str):
        return {
            "freshness_score": 92.5,
            "color_degradation": 0.05,
            "texture_roughness": 0.08,
            "mold_detected": False,
            "mold_confidence": 0.0,
            "bruising_detected": False,
            "bruising_confidence": 0.0,
            "damage_detected": False,
            "damage_confidence": 0.0,
            "classification_label": "FRESH",
            "status_message": "Food is fresh",
            "confidence": 0.95,
            "model_version": "1.0.0"
        }
    
    model_pipeline.analyze_image = dummy_analyze
    yield
    model_pipeline.analyze_image = original_analyze

@pytest_asyncio.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    async def _get_test_db():
        yield db_session
        
    app.dependency_overrides[get_db] = _get_test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
