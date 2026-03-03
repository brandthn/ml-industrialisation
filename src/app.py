from flask import Flask, request, jsonify
import pandas as pd
from datetime import date
import os

PATH_CSV = "data/raw/db.csv"


def week_to_months(year_week, sales):
    year = year_week // 100
    week = year_week % 100
    monday = date.fromisocalendar(year, week, 1)
    sunday = date.fromisocalendar(year, week, 7)

    first_month = monday.year * 100 + monday.month
    last_month = sunday.year * 100 + sunday.month

    if first_month == last_month:
        return [(first_month, sales)]

    # Days in the first month: from monday up to (not including) the 1st of next month
    if monday.month == 12:
        first_of_next = date(monday.year + 1, 1, 1)
    else:
        first_of_next = date(monday.year, monday.month + 1, 1)
    n = (first_of_next - monday).days

    return [
        (first_month, n / 7 * sales),
        (last_month, (7 - n) / 7 * sales),
    ]


def create_app(config=None):
    config = config or {}
    app = Flask(__name__)

    if "CSV_PATH" not in config:
        config["CSV_PATH"] = PATH_CSV

    app.config.update(config)

    @app.route('/post_sales', methods=['POST'])
    def post_sales():
        data = request.json
        df_new = pd.DataFrame(data)

        if os.path.isfile(app.config['CSV_PATH']) and os.path.getsize(app.config['CSV_PATH']) > 0:
            df = pd.read_csv(app.config['CSV_PATH'])
            df = pd.concat([df, df_new])
        else:
            df = df_new

        df = df.drop_duplicates(subset=['year_week', 'vegetable'], keep='last')
        df.to_csv(app.config['CSV_PATH'], index=False)

        return jsonify({"status": "success"}), 200

    @app.route('/get_weekly_sales', methods=['GET'])
    def get_weekly_sales():
        csv_path = app.config['CSV_PATH']
        if not os.path.isfile(csv_path) or os.path.getsize(csv_path) == 0:
            return jsonify([]), 200
        df = pd.read_csv(csv_path)
        return jsonify(df.to_dict(orient='records')), 200

    @app.route('/get_monthly_sales', methods=['GET'])
    def get_monthly_sales():
        csv_path = app.config['CSV_PATH']
        if not os.path.isfile(csv_path) or os.path.getsize(csv_path) == 0:
            return jsonify([]), 200

        df = pd.read_csv(csv_path)

        rows = []
        for _, row in df.iterrows():
            for year_month, monthly_sales in week_to_months(int(row['year_week']), row['sales']):
                rows.append({
                    'year_month': year_month,
                    'vegetable': row['vegetable'],
                    'sales': monthly_sales,
                })

        if not rows:
            return jsonify([]), 200

        monthly_df = pd.DataFrame(rows)
        result = (
            monthly_df
            .groupby(['year_month', 'vegetable'], sort=False)['sales']
            .sum()
            .reset_index()
            .sort_values(['year_month', 'vegetable'])
            .reset_index(drop=True)
        )

        return jsonify(result.to_dict(orient='records')), 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(port=8000)
