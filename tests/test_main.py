import re
from httpx import AsyncClient
import pytest


# @pytest.mark.asyncio
async def test_main(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
