"""
Flask app with CSV-based storage.
"""
from flask import Flask, request, jsonify
from services.data import CSVStore, aggregate_monthly, split_week_into_months

PATH_CSV = "data/raw/db.csv"


def create_app(config=None):
    config = config or {}
    app = Flask(__name__)

    if "CSV_PATH" not in config:
        config["CSV_PATH"] = PATH_CSV

    app.config.update(config)

    store = CSVStore(app.config["CSV_PATH"])

    @app.route("/post_sales", methods=["POST"])
    def post_sales():
        data = request.json
        store.save_weekly(data)
        return jsonify({"status": "success"}), 200

    @app.route("/get_weekly_sales", methods=["GET"])
    def get_weekly_sales():
        records = store.load_weekly()
        return jsonify(records), 200

    @app.route("/get_monthly_sales", methods=["GET"])
    def get_monthly_sales():
        remove = request.args.get("remove_outliers", "false").lower() == "true"
        records = store.load_weekly()
        monthly = aggregate_monthly(records, remove_outliers=remove)
        return jsonify(monthly), 200

    return app


# keep backward compat for unit tests
week_to_months = split_week_into_months


if __name__ == "__main__":
    app = create_app()
    app.run(port=8000)
