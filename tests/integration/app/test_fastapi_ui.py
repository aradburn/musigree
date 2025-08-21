from typing import AsyncGenerator

import pytest
from httpx import AsyncClient


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
@pytest.mark.parametrize("is_load_runtime_data_required", [True], scope="class")
class TestFastAPIUI:
    @pytest.mark.asyncio
    async def test_index(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        client: AsyncClient,
    ) -> None:
        response = await client.get("/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_artist_200(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        client: AsyncClient,
    ) -> None:
        response = await client.get("/artist/2239")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_artist_400(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        client: AsyncClient,
    ) -> None:
        response = await client.get("/artist/bad")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_artist_404(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        client: AsyncClient,
    ) -> None:
        response = await client.get("/artist/0")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_label_200(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        client: AsyncClient,
    ) -> None:
        response = await client.get("/label/1")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_label_400(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        client: AsyncClient,
    ) -> None:
        response = await client.get("/label/bad")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_label_404(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        client: AsyncClient,
    ) -> None:
        response = await client.get("/label/2")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_error(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        client: AsyncClient,
    ) -> None:
        response = await client.get("/malformed")
        assert response.status_code == 404
