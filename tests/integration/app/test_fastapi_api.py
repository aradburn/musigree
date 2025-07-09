"""Integration tests for the FastAPI API endpoints."""
import pytest
from httpx import AsyncClient

from musigree.utils import normalize_dict_list


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
@pytest.mark.parametrize("is_load_runtime_data_required", [True], scope="class")
class TestFastAPIAPI:
    """Test class for FastAPI API endpoints."""

    @pytest.mark.asyncio
    async def test_network_01(self, offline_database_setup, runtime_database_setup, client: AsyncClient) -> None:
        """Test network endpoint with valid artist ID."""
        response = await client.get("/api/artist/network/2239")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_network_02(self, offline_database_setup, runtime_database_setup, client: AsyncClient) -> None:
        """Test network endpoint with invalid artist ID."""
        response = await client.get("/api/artist/network/999999999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_network_03(self, offline_database_setup, runtime_database_setup, client: AsyncClient) -> None:
        """Test network endpoint with valid label ID."""
        response = await client.get("/api/label/network/1")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_01(self, offline_database_setup, runtime_database_setup, client: AsyncClient) -> None:
        """Test search endpoint with basic query."""
        response = await client.get("/api/search/Morris")
        print(f"response: {response}")
        assert response.status_code == 200

        actual = response.json()
        print(f"actual: {actual}")
        expected = {
            "results": [
                {"key": "artist-496270", "name": "Morris Gould"},
                {"key": "artist-33927", "name": "Stephen Morris"},
                {"key": "artist-3723", "name": "Chris Morris"},
                {"key": "artist-3985", "name": "Mixmaster Morris"},
                {"key": "artist-27005", "name": "Morris Nightingale"},
                {"key": "artist-444670", "name": "Craig Morris"},
                {"key": "artist-2922503", "name": "Paul Morris (17)"},
                {"key": "artist-175123", "name": 'Leo "Swift" Morris'},
                {"key": "artist-249982", "name": "Leo Swift Morris"},
            ]
        }
        # We are not testing results sort order here, so we can just check the results
        actual_str = normalize_dict_list(actual["results"])
        expected_str = normalize_dict_list(expected["results"])
        assert actual_str == expected_str

    @pytest.mark.asyncio
    async def test_search_02(self, offline_database_setup, runtime_database_setup, client: AsyncClient) -> None:
        """Test search endpoint with URL encoded query."""
        response = await client.get("/api/search/Chris%20Morris")
        assert response.status_code == 200

        actual = response.json()
        expected = {"results": [{"key": "artist-3723", "name": "Chris Morris"}]}
        assert actual == expected

    @pytest.mark.asyncio
    async def test_relations_01(self, offline_database_setup, runtime_database_setup, client: AsyncClient) -> None:
        """Test relations endpoint."""
        response = await client.get("/api/artist/relations/32613")
        assert response.status_code == 200

        actual = response.json()
        expected = {
            "results": [
                {"releases": {}, "role": "Turntables"},
                {"releases": {}, "role": "Producer"},
                {"releases": {}, "role": "Producer"},
                {"releases": {}, "role": "Producer"},
                {"releases": {}, "role": "Producer"},
                {"releases": {}, "role": "Producer"},
                {"releases": {}, "role": "Compiled On"},
                {"releases": {}, "role": "Compiled On"},
                {"releases": {}, "role": "Compiled On"},
                {"releases": {}, "role": "Compiled On"},
                {"releases": {}, "role": "Compiled On"},
                {"releases": {}, "role": "Compiled On"},
                {"releases": {}, "role": "Remix"},
                {"releases": {}, "role": "Remix"},
                {"releases": {}, "role": "Remix"},
                {"releases": {}, "role": "Remix"},
                {"releases": {}, "role": "Mixed By"},
                {"releases": {}, "role": "Written By"},
                {"releases": {}, "role": "Written By"},
                {"releases": {}, "role": "Written By"},
                {"releases": {}, "role": "Written By"},
            ]
        }
        # expected = {
        #     "results": [
        #         {
        #             "releases": {"2267734": 1990, "4625": 1990, "61862": 1993},
        #             "role": "Turntables",
        #         },
        #         {"releases": {"2455278": 2010}, "role": "Producer"},
        #         {"releases": {"2455278": 2010}, "role": "Producer"},
        #         {"releases": {"102382": 1995, "134822": 1996}, "role": "Producer"},
        #         {
        #             "releases": {
        #                 "1530077": 2002,
        #                 "1741441": None,
        #                 "2317370": 2009,
        #                 "29372": 1992,
        #                 "29373": 1992,
        #                 "315067": 1992,
        #                 "3564784": 1992,
        #                 "549": 1992,
        #             },
        #             "role": "Producer",
        #         },
        #         {
        #             "releases": {
        #                 "1530077": 2002,
        #                 "1741441": None,
        #                 "2317370": 2009,
        #                 "29372": 1992,
        #                 "29373": 1992,
        #                 "315067": 1992,
        #                 "3564784": 1992,
        #                 "549": 1992,
        #             },
        #             "role": "Producer",
        #         },
        #         {"releases": {"315067": 1992}, "role": "Compiled On"},
        #         {"releases": {"51781": 1993}, "role": "Compiled On"},
        #         {"releases": {"51781": 1993}, "role": "Compiled On"},
        #         {
        #             "releases": {
        #                 "1530077": 2002,
        #                 "1741441": None,
        #                 "2317370": 2009,
        #                 "29372": 1992,
        #                 "29373": 1992,
        #                 "3564784": 1992,
        #                 "548125": 1992,
        #                 "549": 1992,
        #             },
        #             "role": "Compiled On",
        #         },
        #         {"releases": {"170322": 1994}, "role": "Compiled On"},
        #         {"releases": {"548125": 1992}, "role": "Compiled On"},
        #         {"releases": {"2455278": 2010}, "role": "Remix"},
        #         {"releases": {"2455278": 2010}, "role": "Remix"},
        #         {
        #             "releases": {"2267734": 1990, "4625": 1990, "61862": 1993},
        #             "role": "Remix",
        #         },
        #         {"releases": {"89013": 1995}, "role": "Remix"},
        #         {
        #             "releases": {"102382": 1995, "134822": 1996, "3097008": 1996},
        #             "role": "Mixed By",
        #         },
        #         {
        #             "releases": {"102382": 1995, "134822": 1996, "89013": 1995},
        #             "role": "Written By",
        #         },
        #         {
        #             "releases": {
        #                 "1530077": 2002,
        #                 "1741441": None,
        #                 "2317370": 2009,
        #                 "29372": 1992,
        #                 "29373": 1992,
        #                 "315067": 1992,
        #                 "3564784": 1992,
        #                 "549": 1992,
        #             },
        #             "role": "Written By",
        #         },
        #         {"releases": {"85213": 1994, "89013": 1995}, "role": "Written By"},
        #         {
        #             "releases": {
        #                 "1530077": 2002,
        #                 "1741441": None,
        #                 "2317370": 2009,
        #                 "29372": 1992,
        #                 "29373": 1992,
        #                 "315067": 1992,
        #                 "3564784": 1992,
        #                 "549": 1992,
        #             },
        #             "role": "Written By",
        #         },
        #     ]
        # }
        actual_str = normalize_dict_list(actual["results"])
        expected_str = normalize_dict_list(expected["results"])
        assert actual_str == expected_str

    @pytest.mark.asyncio
    async def test_roles_01(self, offline_database_setup, runtime_database_setup, client: AsyncClient) -> None:
        """Test roles endpoint."""
        response = await client.get("/api/roles")
        assert response.status_code == 200

        actual = response.json()
        assert actual is not None
        assert actual["roles"] is not None
        expected = 4119
        assert len(actual["roles"]) == expected

    @pytest.mark.asyncio
    async def test_entity_details_01(self, offline_database_setup, runtime_database_setup, client: AsyncClient) -> None:
        """Test getting entity details for an artist."""
        response = await client.get("/api/artist/details/2239")
        assert response.status_code == 200

        actual = response.json()
        assert actual is not None
        
        # Verify required fields are present
        assert "id" in actual
        assert "type" in actual
        assert "name" in actual
        assert "metadata" in actual
        assert "entities" in actual
        assert "relation_counts" in actual
        
        # Verify correct types
        assert actual["id"] == 2239
        assert actual["type"] == "artist"
        assert isinstance(actual["name"], str)
        assert isinstance(actual["metadata"], dict)
        assert isinstance(actual["entities"], dict)
        assert isinstance(actual["relation_counts"], dict)

    @pytest.mark.asyncio
    async def test_entity_details_02(self, offline_database_setup, runtime_database_setup, client: AsyncClient) -> None:
        """Test getting entity details for a label."""
        response = await client.get("/api/label/details/1")
        assert response.status_code == 200

        actual = response.json()
        assert actual is not None
        
        # Verify required fields are present
        assert "id" in actual
        assert "type" in actual
        assert "name" in actual
        
        # Verify correct types
        assert actual["id"] == 1
        assert actual["type"] == "label"

    @pytest.mark.asyncio
    async def test_entity_details_03(self, offline_database_setup, runtime_database_setup, client: AsyncClient) -> None:
        """Test entity details endpoint with invalid entity ID."""
        response = await client.get("/api/artist/details/999999999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_entity_details_04(self, offline_database_setup, runtime_database_setup, client: AsyncClient) -> None:
        """Test entity details endpoint with invalid entity type."""
        response = await client.get("/api/invalidtype/details/1")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_entity_details_05(self, offline_database_setup, runtime_database_setup, client: AsyncClient) -> None:
        """Test entity details endpoint with non-numeric entity ID."""
        response = await client.get("/api/artist/details/abc")
        assert response.status_code == 400
