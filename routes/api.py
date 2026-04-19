"""
routes/api.py
=============
REST API endpoints — all return JSON.

GET  /api/zones          → all zone records with computed metrics
GET  /api/zones/<area>   → single zone detail
GET  /api/summary        → KPI summary stats
GET  /api/top?n=5        → top-N zones by GVS
GET  /api/tier/<tier>    → zones filtered by tier name
"""

from flask import Blueprint, jsonify, request, abort
from utils.data_engine import get_processed, summary_stats

api_bp = Blueprint("api", __name__)


def _df_to_json(df):
    """Convert DataFrame to a clean JSON-serialisable list."""
    cols = [
        "area", "tier", "gvs",
        "price_2022", "price_2024", "price_growth_pct",
        "rtm_price", "uc_price", "rtm_uc_pct",
        "rent", "rental_yield_pct", "occupancy_rate",
        "listings", "infra", "declarations",
        "forecast_24m", "lat", "lng",
    ]
    return df[cols].to_dict(orient="records")


@api_bp.route("/zones")
def zones():
    """Return all zone records."""
    df = get_processed()
    return jsonify({"status": "ok", "count": len(df), "data": _df_to_json(df)})


@api_bp.route("/zones/<string:area>")
def zone_detail(area):
    """Return a single zone by name (case-insensitive)."""
    df = get_processed()
    match = df[df["area"].str.lower() == area.lower()]
    if match.empty:
        abort(404, description=f"Zone '{area}' not found")
    return jsonify({"status": "ok", "data": _df_to_json(match)[0]})


@api_bp.route("/summary")
def summary():
    """Return top-level KPI summary."""
    df = get_processed()
    return jsonify({"status": "ok", "data": summary_stats(df)})


@api_bp.route("/top")
def top_zones():
    """Return top-N zones by GVS (default 5)."""
    n = min(int(request.args.get("n", 5)), 50)
    df = get_processed().nlargest(n, "gvs")
    return jsonify({"status": "ok", "count": len(df), "data": _df_to_json(df)})


@api_bp.route("/tier/<string:tier_name>")
def by_tier(tier_name):
    """Return zones matching a tier (partial, case-insensitive)."""
    df = get_processed()
    match = df[df["tier"].str.lower().str.contains(tier_name.lower())]
    if match.empty:
        return jsonify({"status": "ok", "count": 0, "data": []})
    return jsonify({"status": "ok", "count": len(match), "data": _df_to_json(match)})
