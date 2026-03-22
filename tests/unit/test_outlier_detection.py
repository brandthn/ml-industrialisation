"""Unit tests for outlier detection (per vegetable, mean + 5*std)."""
import pandas as pd
from services.data import detect_outliers


def test_no_outlier_normal_data():
    # all values are close, none should be flagged
    df = pd.DataFrame({
        "vegetable": ["tomato"] * 5,
        "sales": [100, 102, 98, 101, 99],
    })
    result = detect_outliers(df)
    assert result["is_outlier"].sum() == 0


def test_obvious_outlier():
    # 28 normal values around 100, then one extreme value
    sales = [100] * 28 + [10000]
    df = pd.DataFrame({
        "vegetable": ["tomato"] * 29,
        "sales": sales,
    })
    result = detect_outliers(df)
    # only the last row should be flagged
    assert result["is_outlier"].sum() == 1
    assert result.iloc[-1]["is_outlier"] == True


def test_outlier_per_vegetable():
    # carrots have high values normally, tomato has low values
    # a value that is normal for carrot should not be flagged
    df = pd.DataFrame({
        "vegetable": ["carrot"] * 10 + ["tomato"] * 10,
        "sales": [5000] * 10 + [50] * 10,
    })
    result = detect_outliers(df)
    assert result["is_outlier"].sum() == 0


def test_outlier_only_for_its_vegetable():
    # tomato normally sells ~100, one sells 10000 -> outlier
    # carrot normally sells ~5000, not affected
    df = pd.DataFrame({
        "vegetable": ["tomato"] * 30 + ["carrot"] * 10 + ["tomato"],
        "sales": [100] * 30 + [5000] * 10 + [10000],
    })
    result = detect_outliers(df)
    assert result["is_outlier"].sum() == 1
    assert result[result["is_outlier"]].iloc[0]["vegetable"] == "tomato"
