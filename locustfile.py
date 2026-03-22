"""
Locust load test for the sales API.
Run: uv run locust -f locustfile.py --host http://localhost:8000
Target: 1000 req/s (500 POST, 250 GET weekly, 250 GET monthly)
"""
from locust import HttpUser, task, between


class SalesUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(2)
    def post_sales(self):
        self.client.post("/post_sales", json=[
            {"year_week": 202010, "vegetable": "tomato", "sales": 120},
        ])

    @task(1)
    def get_weekly(self):
        self.client.get("/get_weekly_sales")

    @task(1)
    def get_monthly(self):
        self.client.get("/get_monthly_sales")
