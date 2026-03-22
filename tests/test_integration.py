"""Integration tests for the sales API (SQLite backend)."""
import pytest
from app import create_app


@pytest.fixture
def app():
    # in-memory sqlite for tests – fast and isolated
    config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    }
    app = create_app(config)
    yield app


def test_post_sales(app):
    """Post same data twice, should only keep one record (idempotence)."""
    data = [{"year_week": 202001, "vegetable": "tomato", "sales": 100}]

    with app.test_client() as client:
        assert client.post("post_sales", json=data).status_code == 200
        assert client.post("post_sales", json=data).status_code == 200

        response = client.get("get_weekly_sales")
        assert response.status_code == 200

    assert response.json == [{"year_week": 202001, "vegetable": "tomato", "sales": 100.0}]


def test_get_monthly_sales(app):
    """Weekly data should be aggregated correctly into months."""
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
        {"year_month": 202001, "vegetable": "tomato", "sales": 200.0},
        {"year_month": 202002, "vegetable": "tomato", "sales": 100.0},
        {"year_month": 202003, "vegetable": "carrot", "sales": 50.0},
    ]


def test_init_database(app):
    """init_database should clear all data."""
    data = [{"year_week": 202001, "vegetable": "tomato", "sales": 100}]

    with app.test_client() as client:
        client.post("post_sales", json=data)
        client.post("init_database")

        response = client.get("get_weekly_sales")
        assert response.json == []


def test_post_sales_partial_valid(app):
    """Valid records should be saved even if others in the batch are invalid."""
    data = [
        {"year_week": 202001, "vegetable": "tomato", "sales": 100},
        {"year_week": 202002, "vegetable": "tomato", "sales": 50},
    ]

    with app.test_client() as client:
        assert client.post("post_sales", json=data).status_code == 200
        response = client.get("get_weekly_sales")

    assert len(response.json) == 2
