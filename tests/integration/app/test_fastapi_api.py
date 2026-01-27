"""Integration tests for the FastAPI API endpoints."""

from typing import AsyncGenerator

import pytest
from httpx import AsyncClient

from musigree.utils import normalize_dict_list


# noinspection HttpUrlsUsage
@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
@pytest.mark.parametrize("is_load_runtime_data_required", [True], scope="class")
class TestFastAPIAPI:
    """Test class for FastAPI API endpoints."""

    @pytest.mark.asyncio
    async def test_entity_details_01(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
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

        expected = {
            "id": 2239,
            "type": "artist",
            "name": "Seefeel",
            "metadata": {
                "profile": "British electronic/rock group formed in the early 1990s. They are currently signed to Warp Records.",
                "real_name": "Sarah Peacock, Mark Clifford, Darren Seymour & Justin Fletcher",
                "urls": [
                    "http://www.myspace.com/seefeelmyspace", "http://en.wikipedia.org/wiki/Seefeel",
                    "http://www.facebook.com/pages/Seefeel/146206372061290", "http://twitter.com/#!/_Seefeel_",
                    "http://bit.ly/mQ9t3F", "http://www.seefeel.org",
                ],
            },
            "entities": {
                "members": {
                    "Daren Seymour": 66803,
                    "Justin Fletcher": 489350,
                    "Mark Clifford": 51674,
                    "Mark Van Hoen": 41103,
                    "Sarah Peacock": 115880,
                },
            },
            "relation_counts": {
                "Copyright": 2,
                "Designed At": 1,
                "Phonographic Copyright": 2,
                "Published By": 1,
                "DJ Mix": 7,
                "Performer": 1,
                "Producer": 2,
                "Compiled On": 15,
                "Released On": 1,
                "Remix": 6,
                "Design": 1,
                "Film Director": 1,
                "Written By": 5,
            },
            "countries": "UK",
            "genres": "Electronic",
            "styles": "Ambient,IDM,Leftfield",
        }
        assert actual == expected

    @pytest.mark.asyncio
    async def test_entity_details_cached_01(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
        """Test getting entity details for an artist."""
        response = await client.get("/api/artist/details/2239")
        assert response.status_code == 200

        response = await client.get("/api/artist/details/2239")
        assert response.status_code == 200

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

        expected = {
            "id": 2239,
            "type": "artist",
            "name": "Seefeel",
            "metadata": {
                "profile": "British electronic/rock group formed in the early 1990s. They are currently signed to Warp Records.",
                "real_name": "Sarah Peacock, Mark Clifford, Darren Seymour & Justin Fletcher",
                "urls": [
                    "http://www.myspace.com/seefeelmyspace", "http://en.wikipedia.org/wiki/Seefeel",
                    "http://www.facebook.com/pages/Seefeel/146206372061290", "http://twitter.com/#!/_Seefeel_",
                    "http://bit.ly/mQ9t3F", "http://www.seefeel.org",
                ],
            },
            "entities": {
                "members": {
                    "Daren Seymour": 66803,
                    "Justin Fletcher": 489350,
                    "Mark Clifford": 51674,
                    "Mark Van Hoen": 41103,
                    "Sarah Peacock": 115880,
                },
            },
            "relation_counts": {
                "Copyright": 2,
                "Designed At": 1,
                "Phonographic Copyright": 2,
                "Published By": 1,
                "DJ Mix": 7,
                "Performer": 1,
                "Producer": 2,
                "Compiled On": 15,
                "Released On": 1,
                "Remix": 6,
                "Design": 1,
                "Film Director": 1,
                "Written By": 5,
            },
            "countries": "UK",
            "genres": "Electronic",
            "styles": "Ambient,IDM,Leftfield",
        }
        assert actual == expected

    @pytest.mark.asyncio
    async def test_entity_details_02(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
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

        expected = {
            "id": 1,
            "type": "label",
            "name": "Planet E",
            "metadata": {
                "profile": "Classic Techno label from Detroit, USA.\r\n[b]Label owner:[/b] [a871=Carl Craig].\r\n",
                "urls": [
                    "http://www.planet-e.net/",
                    "http://www.myspace.com/planetecom",
                    "http://www.facebook.com/planetedetroit ",
                    "http://twitter.com/planetedetroit",
                    "http://soundcloud.com/planetedetroit",
                ],
            },
            "entities": {},
            "relation_counts": {
                "Released On": 1,
            },
            "countries": "Belgium,US",
            "genres": "Electronic",
            "styles": "Experimental,House,Techno",
        }
        assert actual == expected

    @pytest.mark.asyncio
    async def test_entity_details_cached_02(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
        """Test getting entity details for a label."""
        response = await client.get("/api/label/details/1")
        assert response.status_code == 200

        response = await client.get("/api/label/details/1")
        assert response.status_code == 200

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

        expected = {
            "id": 1,
            "type": "label",
            "name": "Planet E",
            "metadata": {
                "profile": "Classic Techno label from Detroit, USA.\r\n[b]Label owner:[/b] [a871=Carl Craig].\r\n",
                "urls": [
                    "http://www.planet-e.net/",
                    "http://www.myspace.com/planetecom",
                    "http://www.facebook.com/planetedetroit ",
                    "http://twitter.com/planetedetroit",
                    "http://soundcloud.com/planetedetroit",
                ],
            },
            "entities": {},
            "relation_counts": {
                "Released On": 1,
            },
            "countries": "Belgium,US",
            "genres": "Electronic",
            "styles": "Experimental,House,Techno",
        }
        assert actual == expected

    @pytest.mark.asyncio
    async def test_entity_details_03(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
        """Test entity details endpoint with invalid entity ID."""
        response = await client.get("/api/artist/details/999999999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_entity_details_cached_03(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
        """Test entity details endpoint with invalid entity ID."""
        response = await client.get("/api/artist/details/999999999999")
        assert response.status_code == 404

        response = await client.get("/api/artist/details/999999999999")
        assert response.status_code == 404

        response = await client.get("/api/artist/details/999999999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_entity_details_04(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
        """Test entity details endpoint with invalid entity type."""
        response = await client.get("/api/invalidtype/details/1")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_entity_details_05(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
        """Test entity details endpoint with non-numeric entity ID."""
        response = await client.get("/api/artist/details/abc")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_network_01(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
        """Test network endpoint with valid artist ID."""
        response = await client.get("/api/artist/network/2239")
        assert response.status_code == 200

        actual = response.json()
        expected = {
            "center": {
                "key": "artist-2239",
                "name": "Seefeel",
            },
            "links": [
                {
                    "key": "artist-115880-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-115880",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-1920-alias-artist-51674",
                    "role": "Alias",
                    "source": "artist-1920",
                    "target": "artist-51674",
                },
                {
                    "key": "artist-231-alias-artist-1920",
                    "role": "Alias",
                    "source": "artist-231",
                    "target": "artist-1920",
                },
                {
                    "key": "artist-231-alias-artist-51674",
                    "role": "Alias", "source": "artist-231",
                    "target": "artist-51674",
                },
                {
                    "key": "artist-3490-alias-artist-41103",
                    "role": "Alias",
                    "source": "artist-3490",
                    "target": "artist-41103",
                },
                {
                    "key": "artist-41103-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-41103",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-489350-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-489350",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-51674-member-of-artist-1656080",
                    "role": "Member Of",
                    "source": "artist-51674",
                    "target": "artist-1656080",
                },
                {
                    "key": "artist-51674-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-51674",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-66803-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-66803",
                    "target": "artist-2239",
                },
            ],
            "nodes": [
                {
                    "distance": 2,
                    "id": 231,
                    "key": "artist-231",
                    "links": [
                        "artist-231-alias-artist-1920",
                        "artist-231-alias-artist-51674",
                    ],
                    "missing": 0,
                    "name": "Woodenspoon",
                    "size": 0,
                    "type": "artist",
                    "cluster": 1,
                },
                {
                    "distance": 2,
                    "id": 1920,
                    "key": "artist-1920",
                    "links": [
                        "artist-1920-alias-artist-51674",
                        "artist-231-alias-artist-1920"
                    ],
                    "missing": 0,
                    "name": "Disjecta",
                    "size": 0,
                    "type": "artist",
                    "cluster": 1,
                },
                {
                    "distance": 0,
                    "id": 2239,
                    "key": "artist-2239",
                    "links": [
                        "artist-115880-member-of-artist-2239",
                        "artist-41103-member-of-artist-2239",
                        "artist-489350-member-of-artist-2239",
                        "artist-51674-member-of-artist-2239",
                        "artist-66803-member-of-artist-2239"
                    ],
                    "missing": 0,
                    "name": "Seefeel",
                    "size": 5,
                    "type": "artist",
                },
                {
                    "distance": 2,
                    "id": 3490,
                    "key": "artist-3490",
                    "links": [
                        "artist-3490-alias-artist-41103",
                    ],
                    "missing": 0,
                    "name": "Locust",
                    "size": 0,
                    "type": "artist",
                    "cluster": 2,
                },
                {
                    "distance": 1,
                    "id": 41103,
                    "key": "artist-41103",
                    "links": [
                        "artist-3490-alias-artist-41103",
                        "artist-41103-member-of-artist-2239",
                    ],
                    "missing": 0,
                    "name": "Mark Van Hoen",
                    "size": 0,
                    "type": "artist",
                    "cluster": 2,
                },
                {
                    "distance": 1,
                    "id": 51674,
                    "key": "artist-51674",
                    "links": [
                        "artist-1920-alias-artist-51674",
                        "artist-231-alias-artist-51674",
                        "artist-51674-member-of-artist-1656080",
                        "artist-51674-member-of-artist-2239",
                    ],
                    "missing": 0,
                    "name": "Mark Clifford",
                    "size": 0,
                    "type": "artist",
                    "cluster": 1,
                },
                {
                    "distance": 1,
                    "id": 66803,
                    "key": "artist-66803",
                    "links": [
                        "artist-66803-member-of-artist-2239",
                    ],
                    "missing": 0,
                    "name": "Daren Seymour",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 1,
                    "id": 115880,
                    "key": "artist-115880",
                    "links": [
                        "artist-115880-member-of-artist-2239",
                    ],
                    "missing": 0,
                    "name": "Sarah Peacock",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 1,
                    "id": 489350,
                    "key": "artist-489350",
                    "links": [
                        "artist-489350-member-of-artist-2239",
                    ],
                    "missing": 0,
                    "name": "Justin Fletcher",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 2,
                    "id": 1656080,
                    "key": "artist-1656080",
                    "links": [
                        "artist-51674-member-of-artist-1656080",
                    ],
                    "missing": 0,
                    "name": "Cliffordandcalix",
                    "size": 1,
                    "type": "artist",
                },
            ],
        }

        assert actual == expected

    @pytest.mark.asyncio
    async def test_network_02(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
        """Test network endpoint with invalid artist ID."""
        response = await client.get("/api/artist/network/999999999999")
        assert response.status_code == 404

        actual = response.json()
        expected = {
            "success": False,
            "status": 404,
            "message": "No Data",
        }
        assert actual == expected

    @pytest.mark.asyncio
    async def test_network_03(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
        """Test network endpoint with valid label ID."""
        response = await client.get("/api/label/network/1")
        assert response.status_code == 200

        actual = response.json()
        expected = {
            "center": {
                "key": "label-1",
                "name": "Planet E",
            },
            "links": [],
            "nodes": [
                {
                    "distance": 0,
                    "id": 1,
                    "key": "label-1",
                    "links": [],
                    "missing": 0,
                    "name": "Planet E",
                    "size": 0,
                    "type": "label",
                },
            ],
        }

        assert actual == expected

    @pytest.mark.asyncio
    async def test_relations_01(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
        """Test relations endpoint."""
        response = await client.get("/api/artist/relations/32613")
        assert response.status_code == 200

        actual = response.json()

        expected = [
            {
                "releases": {
                    "102382": 1995,
                    "134822": 1996,
                    "1530077": 2002,
                    "1741441": None,
                    "2317370": 2009,
                    "2455278": 2010,
                    "29372": 1992,
                    "29373": 1992,
                    "315067": 1992,
                    "3564784": 1992,
                    "549": 1992,
                },
                "role": "Producer",
            },
            {
                "releases": {
                    "102382": 1995,
                    "134822": 1996,
                    "1530077": 2002,
                    "1741441": None,
                    "2317370": 2009,
                    "29372": 1992,
                    "29373": 1992,
                    "315067": 1992,
                    "3564784": 1992,
                    "549": 1992,
                    "85213": 1994,
                    "89013": 1995,
                },
                "role": "Written By",
            },
            {
                "releases": {
                    "102382": 1995,
                    "134822": 1996,
                    "3097008": 1996,
                },
                "role": "Mixed By",
            },
            {
                "releases": {
                    "1530077": 2002,
                    "170322": 1994,
                    "1741441": None,
                    "2317370": 2009,
                    "29372": 1992,
                    "29373": 1992,
                    "315067": 1992,
                    "3564784": 1992,
                    "51781": 1993,
                    "548125": 1992,
                    "549": 1992,
                },
                "role": "Compiled On",
            },
            {
                "releases": {
                    "2267734": 1990,
                    "2455278": 2010,
                    "4625": 1990,
                    "61862": 1993,
                    "89013": 1995,
                },
                "role": "Remix",
            },
            {
                "releases": {
                    "2267734": 1990,
                    "4625": 1990,
                    "61862": 1993,
                },
                "role": "Turntables",
            },
        ]

        actual_str = normalize_dict_list(actual["results"])
        expected_str = normalize_dict_list(expected)
        assert actual_str == expected_str

    @pytest.mark.asyncio
    async def test_relations_not_found(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
        """Test relations endpoint."""
        response = await client.get("/api/artist/relations/999999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_random(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
        """Test random endpoint with valid label ID."""
        response = await client.get("/api/random")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_01(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
        """Test search endpoint with basic query."""
        response = await client.get("/api/search/Morris")
        assert response.status_code == 200

        actual = response.json()
        expected = {
            "results": [
                {"key": "artist-496270", "name": "Morris Gould"},
                {"key": "artist-33927", "name": "Stephen Morris"},
                {"key": "artist-3723", "name": "Chris Morris"},
                {"key": "artist-3985", "name": "Mixmaster Morris"},
                {"key": "artist-27005", "name": "Morris Nightingale"},
                {"key": "artist-444670", "name": "Craig Morris"},
                {"key": "artist-2922503", "name": "Paul Morris (17)"},
                {"key": "artist-175123", "name": "Leo \"Swift\" Morris"},
                {"key": "artist-249982", "name": "Leo Swift Morris"},
            ]
        }
        # We are not testing results sort order here, so we can just check the results
        actual_str = normalize_dict_list(actual["results"])
        expected_str = normalize_dict_list(expected["results"])
        assert actual_str == expected_str

    @pytest.mark.asyncio
    async def test_search_cached_01(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
        """Test search endpoint with basic query."""
        response = await client.get("/api/search/Morris")
        assert response.status_code == 200

        response = await client.get("/api/search/Morris")
        assert response.status_code == 200

        response = await client.get("/api/search/Morris")
        assert response.status_code == 200

        actual = response.json()
        expected = {
            "results": [
                {"key": "artist-496270", "name": "Morris Gould"},
                {"key": "artist-33927", "name": "Stephen Morris"},
                {"key": "artist-3723", "name": "Chris Morris"},
                {"key": "artist-3985", "name": "Mixmaster Morris"},
                {"key": "artist-27005", "name": "Morris Nightingale"},
                {"key": "artist-444670", "name": "Craig Morris"},
                {"key": "artist-2922503", "name": "Paul Morris (17)"},
                {"key": "artist-175123", "name": "Leo \"Swift\" Morris"},
                {"key": "artist-249982", "name": "Leo Swift Morris"},
            ]
        }
        # We are not testing results sort order here, so we can just check the results
        actual_str = normalize_dict_list(actual["results"])
        expected_str = normalize_dict_list(expected["results"])
        assert actual_str == expected_str

    @pytest.mark.asyncio
    async def test_search_02(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
        """Test search endpoint with URL encoded query."""
        response = await client.get("/api/search/Chris%20Morris")
        assert response.status_code == 200

        actual = response.json()
        expected = {
            "results": [
                {
                    "key": "artist-3723",
                    "name": "Chris Morris",
                },
            ],
        }
        assert actual == expected

    @pytest.mark.asyncio
    async def test_search_cached_02(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
        """Test search endpoint with URL encoded query."""
        response = await client.get("/api/search/Chris%20Morris")
        assert response.status_code == 200

        response = await client.get("/api/search/Chris%20Morris")
        assert response.status_code == 200

        response = await client.get("/api/search/Chris%20Morris")
        assert response.status_code == 200

        actual = response.json()
        expected = {
            "results": [
                {
                    "key": "artist-3723",
                    "name": "Chris Morris",
                },
            ],
        }
        assert actual == expected

    @pytest.mark.asyncio
    async def test_search_not_found(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
        """Test search endpoint with URL encoded query."""
        response = await client.get("/api/search/qwerty")
        assert response.status_code == 200

        actual = response.json()
        expected: dict[str, list[dict[str, str]]] = {
            "results": [
            ],
        }
        assert actual == expected

    @pytest.mark.asyncio
    async def test_roles_01(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
        client: AsyncClient,
    ) -> None:
        """Test roles endpoint."""
        response = await client.get("/api/roles")
        assert response.status_code == 200

        actual = response.json()
        assert actual is not None
        assert actual["roles"] is not None
        expected = 4119
        assert len(actual["roles"]) == expected
