import os
import pandas as pd
import pytest
import tempfile

from app import create_app

@pytest.fixture
def app():
    temp_csv = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
    temp_csv.close()

    config = {"TESTING": True, "CSV_PATH": temp_csv.name}

    app = create_app(config)

    yield app

    os.remove(temp_csv.name)


def test_post_sales(app):
    data = [{"year_week": 202001, "vegetable": "tomato", "sales": 100}]

    with app.test_client() as client:
        # Post the same data twice
        assert client.post("post_sales", json=data).status_code == 200
        assert client.post("post_sales", json=data).status_code == 200

        response = client.get("get_weekly_sales")
        assert response.status_code == 200

    assert response.json == [{"year_week": 202001, "vegetable": "tomato", "sales": 100}]


def test_get_monthly_sales(app):
    # Use weeks that sit entirely within one month (no cross-month split needed here)
    # 202002 = Jan 6-12, 202003 = Jan 13-19, 202006 = Feb 3-9, 202010 = Mar 2-8
    data = [
        {"year_week": 202002, "vegetable": "tomato", "sales": 100},
        {"year_week": 202003, "vegetable": "tomato", "sales": 100},
        {"year_week": 202006, "vegetable": "tomato", "sales": 100},
        {"year_week": 202010, "vegetable": "carrot", "sales": 50},
    ]

    with app.test_client() as client:
        assert client.post("post_sales", json=data).status_code == 200
        response = client.get("get_monthly_sales")
        assert response.status_code == 200

    assert response.json == [
        {"year_month": 202001, "vegetable": "tomato", "sales": 200},
        {"year_month": 202002, "vegetable": "tomato", "sales": 100},
        {"year_month": 202003, "vegetable": "carrot", "sales": 50},
    ]
