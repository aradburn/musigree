from typing import AsyncGenerator

import pytest
from httpx import AsyncClient


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
@pytest.mark.parametrize("is_load_runtime_data_required", [True], scope="class")
class TestFastAPIHealthcheck:
    @pytest.mark.asyncio
    async def test_artist_200(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.text == '{"status":"OK"}'

    @pytest.mark.asyncio
    async def test_error(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
        response = await client.get("/health/malformed")
        assert response.status_code == 404
        assert (
            response.text == '{"success":false,"status":404,"message":"Bad healthcheck endpoint"}'
        )
