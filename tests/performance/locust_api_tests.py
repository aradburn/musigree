from locust import FastHttpUser, task


class MusigreePerformaceTest(FastHttpUser):
    @task
    def home_page(self) -> None:
        self.client.get("/")
