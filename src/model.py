import pandas as pd


class PrevMonthSale:
    def predict(self, df):
        return df.groupby("item_id")["sales"].shift(1)


class SameMonthLastYearSales:
    def predict(self, df):
        return df.groupby("item_id")["sales"].shift(12)


MODEL_REGISTRY = {
    "PrevMonthSale": PrevMonthSale,
    "SameMonthLastYearSales": SameMonthLastYearSales,
}


def make_predictions(config):
    df_sales = pd.read_csv(config["data"]["sales"])

    model = MODEL_REGISTRY[config["model"]]()
    df_sales["prediction"] = model.predict(df_sales)

    df_sales = df_sales[df_sales["dates"] >= config["start_test"]].reset_index(drop=True)

    return df_sales[["dates", "item_id", "prediction"]]
