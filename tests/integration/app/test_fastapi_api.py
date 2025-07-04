

class TestFastAPIAPI(AppTestCase):

    def test_network_01(self):
        response = self.client.get("/api/artist/network/2239")
        self.assertEqual(200, response.status_code)

    def test_network_02(self):
        response = self.client.get("/api/artist/network/999999999999")
        self.assertEqual(404, response.status_code)

    def test_network_03(self):
        response = self.client.get("/api/label/network/1")
        self.assertEqual(200, response.status_code)

    def test_search_01(self):
        response = self.client.get("/api/search/Morris")
        print(f"response: {response}")
        self.assertEqual(200, response.status_code)

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
        self.maxDiff = None
        self.assertCountEqual(expected["results"], actual["results"])

    def test_search_02(self):
        response = self.client.get("/api/search/Chris%20Morris")
        self.assertEqual(200, response.status_code)

        actual = response.json()
        expected = {"results": [{"key": "artist-3723", "name": "Chris Morris"}]}
        self.assertEqual(expected, actual)

    def test_relations_01(self):
        response = self.client.get("/api/artist/relations/32613")
        self.assertEqual(200, response.status_code)

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
        self.assertEqual(expected, actual)

    def test_roles_01(self):
        response = self.client.get("/api/roles")
        self.assertEqual(200, response.status_code)

        actual = response.json()
        self.assertIsNotNone(actual)
        self.assertIsNotNone(actual["roles"])
        expected = 4119
        self.assertEqual(expected, len(actual["roles"]))

    def test_entity_details_01(self):
        """Test getting entity details for an artist."""
        response = self.client.get("/api/artist/details/2239")
        self.assertEqual(200, response.status_code)

        actual = response.json()
        self.assertIsNotNone(actual)
        
        # Verify required fields are present
        self.assertIn("id", actual)
        self.assertIn("type", actual)
        self.assertIn("name", actual)
        self.assertIn("metadata", actual)
        self.assertIn("entities", actual)
        self.assertIn("relation_counts", actual)
        
        # Verify correct types
        self.assertEqual(actual["id"], 2239)
        self.assertEqual(actual["type"], "artist")
        self.assertIsInstance(actual["name"], str)
        self.assertIsInstance(actual["metadata"], dict)
        self.assertIsInstance(actual["entities"], dict)
        self.assertIsInstance(actual["relation_counts"], dict)

    def test_entity_details_02(self):
        """Test getting entity details for a label."""
        response = self.client.get("/api/label/details/1")
        self.assertEqual(200, response.status_code)

        actual = response.json()
        self.assertIsNotNone(actual)
        
        # Verify required fields are present
        self.assertIn("id", actual)
        self.assertIn("type", actual)
        self.assertIn("name", actual)
        
        # Verify correct types
        self.assertEqual(actual["id"], 1)
        self.assertEqual(actual["type"], "label")

    def test_entity_details_03(self):
        """Test entity details endpoint with invalid entity ID."""
        response = self.client.get("/api/artist/details/999999999999")
        self.assertEqual(404, response.status_code)

    def test_entity_details_04(self):
        """Test entity details endpoint with invalid entity type."""
        response = self.client.get("/api/invalidtype/details/1")
        self.assertEqual(400, response.status_code)

    def test_entity_details_05(self):
        """Test entity details endpoint with non-numeric entity ID."""
        response = self.client.get("/api/artist/details/abc")
        self.assertEqual(400, response.status_code)
