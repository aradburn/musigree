from locust import task, FastHttpUser


class MusigreePerformaceTest(FastHttpUser):
    @task
    def home_page(self):
        self.client.get("/")
