"""
routes/upload.py
================
File upload endpoint.
Accepts CSV or JSON, validates columns, saves to data/, redirects home.
"""

import os
import json
import pandas as pd
from flask import Blueprint, request, redirect, url_for, flash, jsonify, current_app

upload_bp = Blueprint("upload", __name__)

REQUIRED_COLS = {
    "area", "price_2022", "price_2024", "rent",
    "listings", "infra", "lat", "lng"
}
OPTIONAL_COLS = {
    "municipal_score", "occupancy_rate", "pop_shift",
    "rtm_price", "uc_price", "cagr_3y", "declarations"
}

DEFAULTS = {
    "municipal_score": 70,
    "occupancy_rate":  82,
    "pop_shift":       3000,
    "rtm_price":       0,      # will be derived from price_2024 + 20%
    "uc_price":        0,      # will be derived from price_2024 - 10%
    "cagr_3y":         10.0,
    "declarations":    1,
}


def _fill_optional(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing optional columns with sensible defaults."""
    for col, val in DEFAULTS.items():
        if col not in df.columns:
            df[col] = val
    # Derive RTM/UC if not supplied
    if df["rtm_price"].eq(0).all():
        df["rtm_price"] = (df["price_2024"] * 1.22).round(0)
    if df["uc_price"].eq(0).all():
        df["uc_price"]  = (df["price_2024"] * 0.88).round(0)
    return df


@upload_bp.route("/csv", methods=["POST"])
def upload_csv():
    """Upload a CSV file to replace / append data."""
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file provided"}), 400

    f = request.files["file"]
    if not f.filename.endswith(".csv"):
        return jsonify({"status": "error", "message": "Only CSV files accepted"}), 400

    try:
        df = pd.read_csv(f)
    except Exception as e:
        return jsonify({"status": "error", "message": f"CSV parse error: {e}"}), 400

    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        return jsonify({
            "status": "error",
            "message": f"Missing required columns: {sorted(missing)}"
        }), 400

    df = _fill_optional(df)
    dest = os.path.join(current_app.config["UPLOAD_FOLDER"], "data.csv")
    df.to_csv(dest, index=False)

    return jsonify({
        "status": "ok",
        "message": f"Uploaded {len(df)} zones. Dashboard updated.",
        "zones": len(df),
        "columns": list(df.columns),
    })


@upload_bp.route("/json", methods=["POST"])
def upload_json():
    """Upload a JSON array of zone records."""
    try:
        payload = request.get_json(force=True)
        if not isinstance(payload, list):
            payload = [payload]
        df = pd.DataFrame(payload)
    except Exception as e:
        return jsonify({"status": "error", "message": f"JSON parse error: {e}"}), 400

    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        return jsonify({
            "status": "error",
            "message": f"Missing required columns: {sorted(missing)}"
        }), 400

    df = _fill_optional(df)
    dest = os.path.join(current_app.config["UPLOAD_FOLDER"], "data.csv")
    df.to_csv(dest, index=False)

    return jsonify({
        "status": "ok",
        "message": f"Uploaded {len(df)} zones from JSON.",
        "zones": len(df),
    })
