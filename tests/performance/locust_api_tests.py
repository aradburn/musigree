from locust import task, FastHttpUser


class MusigreePerformaceTest(FastHttpUser):
    @task
    def home_page(self) -> None:
        self.client.get("/")
