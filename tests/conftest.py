from operator import add
from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from app.database.session import get_session
from app.main import app
from app.database import models

# create a new getsession function
test_engine = create_async_engine(
    url="sqlite+aiosqlite:///:memory:",
)

test_session = async_sessionmaker(
    bind=test_engine,
    expire_on_commit=False,
)


async def get_session_override():
    # create teh session object
    async with test_session() as session:
        yield session


@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="session")
async def seller_token(client: AsyncClient):
    response = await client.post(
        url="/seller/login",
        data={
            "username": "seller1@gmail.com",
            "password": "password"
        }
    )
    assert "access_token" in response.json()
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture(scope="session")
async def delivery_partner_token(client: AsyncClient):
    response = await client.post(
        url="/partner/login",
        data={
            "username": "partner1@gmail.com",
            "password": "password"
        },
    )
    assert "access_token" in response.json()
    return response.json()["access_token"]


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_and_teardown():
    print("Setting up resources before tests...")
    # now override it at the test startup
    app.dependency_overrides[get_session] = get_session_override
    # let's now create the tables
    # import the tables
    from sqlmodel import SQLModel
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    # now clear the overrdies
    # create the test data
    from tests.example_data import add_data_to_database
    # add data to the database
    async with test_session() as session:
        await add_data_to_database(session)
    yield
    app.dependency_overrides.clear()
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    print("Tearing down resources after tests...")
