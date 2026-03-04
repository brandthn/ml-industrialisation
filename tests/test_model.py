import pandas as pd
from sklearn.metrics import r2_score
import pytest

import model


def test_model_prev_month():
    config = {
        "data": {
            "sales": "data/raw/sales.csv",
        },
        "start_test": "2023-07-01",
        "model": "PrevMonthSale",
    }

    prediction = model.make_predictions(config)

    df_expected = pd.read_csv("data/raw/prediction_prev_month.csv")

    pd.testing.assert_frame_equal(df_expected, prediction)


def test_model_same_month_last_year():
    config = {
        "data": {
            "sales": "data/raw/sales.csv",
        },
        "start_test": "2023-07-01",
        "model": "SameMonthLastYearSales",
    }

    df_pred = model.make_predictions(config)

    df_expected = pd.read_csv("data/raw/prediction_same_month_last_year.csv")

    pd.testing.assert_frame_equal(df_expected, df_pred)
    

def test_ridge_model():
    """make_predictions is able to fit a ridge model

    features are:
    - "last_month": sales at M-1
    - "same_month_last_year": sales at M-12
    """
    config = {
        "data": {
            "sales": "data/raw/sales.csv",
        },
        "start_test": "2023-07-01",
        "model": "Ridge",
        "features": ["last_month", "same_month_last_year"],
    }

    df_pred = model.make_predictions(config)

    df_true = pd.read_csv("data/raw/sales_to_predict.csv")

    r2 = r2_score(df_true["sales"], df_pred["prediction"])

    assert r2 == pytest.approx(0.8154,rel=1e-3)


def test_compute_mean_sales_on_period():
    df = pd.DataFrame({
        "dates": ["2020-01-01", "2020-02-01", "2020-03-01", "2020-04-01",
                  "2020-01-01", "2020-02-01", "2020-03-01", "2020-04-01"],
        "item_id": [1, 1, 1, 1, 2, 2, 2, 2],
        "sales": [1, 2, 3, 4, 10, 20, 30, 40],
    })
    period = 2
    df = df.sort_values(["item_id", "dates"]).reset_index(drop=True)
    df["sales_on_period"] = df.groupby("item_id")["sales"].transform(
        lambda x: x.shift(1).rolling(window=period).mean()
    )

    expected = pd.Series([float("nan"), float("nan"), 1.5, 2.5,
                          float("nan"), float("nan"), 15.0, 25.0], name="sales_on_period")
    pd.testing.assert_series_equal(df["sales_on_period"], expected)


def test_ridge_model_adding_yearly_mean_sales():
    """Adding a new feature to our sales features.
    make_predictions can now compute the features "average sales over a period"

    Adding feature "last_year_average" which is the average sales on past 12 months

    TIP: Add a unit-test "test_compute_mean_sales_on_period"
    with a dataframe dates, item_id, sales [not necessariliy ordered]
    -> expected sales on period
    TIP2: choose "sales" value so "sales_on_period" is easy to compute.
    TIP3: Also, in test_compute_mean_sales_on_period", you don't have to take a 12-months period.
    You can choose
    period_nb_months=2
    df:
    dates      | item_id  | sales
    2020-01-01 | 1        | 1
    2020-02-01 | 1        | 2
    2020-03-01 | 1        | 3
    2020-04-01 | 1        | 4
    2020-01-01 | 2        | 10
    2020-02-01 | 2        | 20
    2020-03-01 | 2        | 30
    2020-04-01 | 2        | 40

    So that
    df_expected
    dates      | item_id  | sales | sales_on_period
    2020-01-01 | 1        | 1     | NaN
    2020-02-01 | 1        | 2     | NaN
    2020-03-01 | 1        | 3     | 1.5
    2020-04-01 | 1        | 4     | 2.5
    2020-01-01 | 2        | 10    | NaN
    2020-02-01 | 2        | 20    | NaN
    2020-03-01 | 2        | 30    | 15
    2020-04-01 | 2        | 40    | 25
    """
    config = {
        "data": {
            "sales": "data/raw/sales.csv",
        },
        "start_test": "2023-07-01",
        "model": "Ridge",
        "features": ["last_month", "same_month_last_year", "last_year_average"],
    }

    df_pred = model.make_predictions(config)

    df_true = pd.read_csv("data/raw/sales_to_predict.csv")

    r2 = r2_score(df_true["sales"], df_pred["prediction"])

    assert r2 == pytest.approx(0.8412497822819137,rel=1e-3)


def test_ridge_model__adding_growth_factor():
    """
    We now add a growth factor as a feature.
    Growth factor is how much the item grew from year Y-1 to year.
    We measure it as sales of past quarter (last 3 months)
    over sales same quarter last year
    """
    config = {
        "data": {
            "sales": "data/raw/sales.csv",
        },
        "start_test": "2023-07-01",
        "model": "Ridge",
        "features": ["last_month", "same_month_last_year", "last_year_average", "growth"],
    }

    df_pred = model.make_predictions(config)

    df_true = pd.read_csv("data/raw/sales_to_predict.csv")

    r2 = r2_score(df_true["sales"], df_pred["prediction"])

    # R2 score dimishied. Why do you think that is ?
    assert r2 == pytest.approx(0.8408,rel=1e-3)


def tst_marketing_model():
    config = {
        "data": {
            "sales": "data/raw/sales.csv",
            "marketing": "data/raw/marketing.csv",
        },
        "start_test": "2023-07-01",
        "model": "Ridge",
        "features": ["last_month", "same_month_last_year", "last_year_average", "marketing"],
    }

    df_pred = model.make_predictions(config)

    df_true = pd.read_csv("data/raw/sales_to_predict.csv")

    r2 = r2_score(df_true["sales"], df_pred["prediction"])
    assert r2 == pytest.approx(0.8786,rel=1e-3)


def tst_price_model():
    config = {
        "data": {
            "sales": "data/raw/sales.csv",
            "marketing": "data/raw/marketing.csv",
            "price": "data/raw/price.csv",
        },
        "start_test": "2023-07-01",
        "model": "Ridge",
        "features": ["last_month", "same_month_last_year", "last_year_average", "marketing", "price"],
    }

    df_pred = model.make_predictions(config)

    df_true = pd.read_csv("data/raw/sales_to_predict.csv")

    r2 = r2_score(df_true["sales"], df_pred["prediction"])

    assert r2 == pytest.approx(0.8791,rel=1e-3)


def tst_stock_model():
    config = {
        "data": {
            "sales": "data/raw/sales.csv",
            "marketing": "data/raw/marketing.csv",
            "price": "data/raw/price.csv",
            "stock": "data/raw/stock.csv",
        },
        "start_test": "2023-07-01",
        "model": "Ridge",
        "features": ["last_month", "same_month_last_year", "last_year_average", "marketing", "price", "stock"],
    }

    df_pred = model.make_predictions(config)

    df_true = pd.read_csv("data/raw/sales_to_predict.csv")

    r2 = r2_score(df_true["sales"], df_pred["prediction"])

    assert r2 == pytest.approx(0.8446,rel=1e-3)


def tst_model_with_objectives():
    config = {
        "data": {
            "sales": "data/raw/sales.csv",
            "marketing": "data/raw/marketing.csv",
            "price": "data/raw/price.csv",
            "stock": "data/raw/stock.csv",
            "objectives": "data/raw/objectives.csv",
        },
        "start_test": "2023-07-01",
        "model": "Ridge",
        "features": ["last_month", "same_month_last_year", "last_year_average", "marketing", "price", "stock", "objectives"],
    }

    df_pred = model.make_predictions(config)

    df_true = pd.read_csv("data/raw/sales_to_predict.csv")

    r2 = r2_score(df_true["sales"], df_pred["prediction"])

    assert r2 == pytest.approx(0.8446,rel=1e-3)

def tst_custom_model():
    config = {
        "data": {
            "sales": "data/raw/sales.csv",
            "marketing": "data/raw/marketing.csv",
            "price": "data/raw/price.csv",
            "stock": "data/raw/stock.csv",
            "objectives": "data/raw/objectives.csv",
        },
        "start_test": "2023-07-01",
        "model": "CustomModel",
        "features": ["last_month", "same_month_last_year", "last_year_average", "marketing", "price", "stock", "objectives"],
    }

    df_pred = model.make_predictions(config)

    df_true = pd.read_csv("data/raw/sales_to_predict.csv")

    r2 = r2_score(df_true["sales"], df_pred["prediction"])

    assert r2 == pytest.approx(0.8446,rel=1e-3)

