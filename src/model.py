import pandas as pd
from sklearn.linear_model import Ridge as SklearnRidge


def build_features(df):
    df = df.sort_values(["item_id", "dates"]).reset_index(drop=True)
    df["last_month"] = df.groupby("item_id")["sales"].shift(1)
    df["same_month_last_year"] = df.groupby("item_id")["sales"].shift(12)
    df["last_year_average"] = df.groupby("item_id")["sales"].transform(lambda x: x.shift(1).rolling(window=12).mean())
    df["growth"] = df.groupby("item_id")["sales"].transform(
        lambda x: x.shift(1).rolling(3).sum() / x.shift(13).rolling(3).sum()
    )
    return df


def train_model(model, df_train):
    model.fit(df_train)
    return model


class PrevMonthSale:
    def fit(self, df):
        pass

    def predict(self, df):
        return df.groupby("item_id")["sales"].shift(1)


class SameMonthLastYearSales:
    def fit(self, df):
        pass

    def predict(self, df):
        return df.groupby("item_id")["sales"].shift(12)


class RidgeModel:
    def __init__(self, features):
        self.features = features
        self.model = SklearnRidge()

    def fit(self, df):
        X = df[self.features].dropna()
        y = df.loc[X.index, "sales"]
        self.model.fit(X, y)

    def predict(self, df):
        X = df[self.features].dropna()
        predictions = pd.Series(index=df.index, dtype=float)
        predictions[X.index] = self.model.predict(X)
        return predictions


MODEL_REGISTRY = {
    "PrevMonthSale": lambda config: PrevMonthSale(),
    "SameMonthLastYearSales": lambda config: SameMonthLastYearSales(),
    "Ridge": lambda config: RidgeModel(features=config["features"]),
}


def make_predictions(config):
    df_sales = pd.read_csv(config["data"]["sales"])

    test_order = (
        df_sales[df_sales["dates"] >= config["start_test"]][["dates", "item_id"]]
        .reset_index(drop=True)
    )

    df_sales = build_features(df_sales)

    train = df_sales[df_sales["dates"] < config["start_test"]]

    model = MODEL_REGISTRY[config["model"]](config)
    train_model(model, train)
    df_sales["prediction"] = model.predict(df_sales)

    result = test_order.merge(
        df_sales[["dates", "item_id", "prediction"]],
        on=["dates", "item_id"]
    )

    return result
