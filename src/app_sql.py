"""
Flask app with SQLite-based storage.
"""
from flask import Flask, request, jsonify
from services.data import SQLStore, aggregate_monthly, split_week_into_months, db


def create_app(config=None):
    config = config or {}
    app = Flask(__name__)

    # default to a local sqlite file
    if "SQLALCHEMY_DATABASE_URI" not in config:
        config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sales.db"

    app.config.update(config)

    store = SQLStore(app)

    @app.route("/init_database", methods=["POST"])
    def init_database():
        """Create or reset the database (step 8)."""
        store.clear()
        return jsonify({"status": "database initialized"}), 200

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
