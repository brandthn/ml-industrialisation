import os
import pandas as pd
from datetime import date
from flask_sqlalchemy import SQLAlchemy


def split_week_into_months(year_week, sales):
    """Repartit les ventes d'une semaine ISO sur les mois concernes."""
    year = year_week // 100
    week = year_week % 100
    monday = date.fromisocalendar(year, week, 1)
    sunday = date.fromisocalendar(year, week, 7)

    first_month = monday.year * 100 + monday.month
    last_month = sunday.year * 100 + sunday.month

    if first_month == last_month:
        return [(first_month, sales)]

    if monday.month == 12:
        first_of_next = date(monday.year + 1, 1, 1)
    else:
        first_of_next = date(monday.year, monday.month + 1, 1)
    n = (first_of_next - monday).days

    return [
        (first_month, n / 7 * sales),
        (last_month, (7 - n) / 7 * sales),
    ]


def detect_outliers(df, threshold=5):
    """Tag is_outlier=True si sales > mean + threshold*std, par legume."""
    df = df.copy()
    df["is_outlier"] = False
    for veg in df["vegetable"].unique():
        mask = df["vegetable"] == veg
        subset = df.loc[mask, "sales"]
        avg = subset.mean()
        std = subset.std()
        df.loc[mask, "is_outlier"] = subset > (avg + threshold * std)
    return df


# -- CSV backend --

class CSVStore:
    def __init__(self, csv_path):
        self.csv_path = csv_path

    def save_weekly(self, records):
        df_new = pd.DataFrame(records)
        if os.path.isfile(self.csv_path) and os.path.getsize(self.csv_path) > 0:
            df = pd.read_csv(self.csv_path)
            df = pd.concat([df, df_new])
        else:
            df = df_new
        df = df.drop_duplicates(subset=["year_week", "vegetable"], keep="last")
        df.to_csv(self.csv_path, index=False)

    def load_weekly(self):
        if not os.path.isfile(self.csv_path) or os.path.getsize(self.csv_path) == 0:
            return []
        df = pd.read_csv(self.csv_path)
        return df.to_dict(orient="records")

    def clear(self):
        if os.path.isfile(self.csv_path):
            os.remove(self.csv_path)


# -- SQLite backend --

db = SQLAlchemy()


class WeeklySale(db.Model):
    __tablename__ = "weekly_sales"

    id = db.Column(db.Integer, primary_key=True)
    year_week = db.Column(db.Integer, nullable=False)
    vegetable = db.Column(db.String(100), nullable=False)
    sales = db.Column(db.Float, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("year_week", "vegetable", name="uq_week_veg"),
    )


class SQLStore:
    def __init__(self, flask_app):
        db.init_app(flask_app)
        with flask_app.app_context():
            db.create_all()

    def save_weekly(self, records):
        for rec in records:
            existing = WeeklySale.query.filter_by(
                year_week=rec["year_week"],
                vegetable=rec["vegetable"],
            ).first()
            if existing:
                existing.sales = rec["sales"]
            else:
                db.session.add(WeeklySale(**rec))
        db.session.commit()

    def load_weekly(self):
        rows = WeeklySale.query.all()
        return [
            {"year_week": r.year_week, "vegetable": r.vegetable, "sales": r.sales}
            for r in rows
        ]

    def clear(self):
        db.drop_all()
        db.create_all()


# -- Aggregation mensuelle --

def aggregate_monthly(weekly_records, remove_outliers=False):
    """Convertit les ventes weekly en monthly, avec option filtre outliers."""
    if not weekly_records:
        return []

    df = pd.DataFrame(weekly_records)

    df = detect_outliers(df)
    if remove_outliers:
        df = df[~df["is_outlier"]]

    rows = []
    for _, row in df.iterrows():
        for ym, monthly_sales in split_week_into_months(int(row["year_week"]), row["sales"]):
            rows.append({
                "year_month": ym,
                "vegetable": row["vegetable"],
                "sales": monthly_sales,
            })

    if not rows:
        return []

    result = (
        pd.DataFrame(rows)
        .groupby(["year_month", "vegetable"], sort=False)["sales"]
        .sum()
        .reset_index()
        .sort_values(["year_month", "vegetable"])
        .reset_index(drop=True)
    )
    return result.to_dict(orient="records")
