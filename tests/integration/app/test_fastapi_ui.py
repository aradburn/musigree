from tests.integration.app_test_case import AppTestCase


class TestFastAPIUI(AppTestCase):

    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(200, response.status_code)

    def test_artist_200(self):
        response = self.client.get("/artist/2239")
        self.assertEqual(200, response.status_code)

    def test_artist_400(self):
        response = self.client.get("/artist/bad")
        self.assertEqual(400, response.status_code)

    def test_artist_404(self):
        response = self.client.get("/artist/0")
        self.assertEqual(404, response.status_code)

    def test_label_200(self):
        response = self.client.get("/label/1")
        self.assertEqual(200, response.status_code)

    def test_label_400(self):
        response = self.client.get("/label/bad")
        self.assertEqual(400, response.status_code)

    def test_label_404(self):
        response = self.client.get("/label/2")
        self.assertEqual(404, response.status_code)

    def test_error(self):
        response = self.client.get("/malformed")
        self.assertEqual(404, response.status_code)
