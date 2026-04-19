"""
routes/dashboard.py
===================
Main dashboard page route.
Assembles processed data, charts, and map → renders index.html.
"""

from flask import Blueprint, render_template, request
from utils.data_engine import get_processed, summary_stats, DEFAULT_WEIGHTS, compute_gvs, load_raw
from utils.charts import gvs_bar, price_trend, rtm_uc_chart, rental_yield_chart, forecast_chart, scatter_matrix
from utils.map_builder import build_map

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def home():
    # ── Weight overrides from query params (e.g. ?pricing=0.40&rental=0.30)
    try:
        weights = {
            "pricing":  float(request.args.get("pricing",  DEFAULT_WEIGHTS["pricing"])),
            "rental":   float(request.args.get("rental",   DEFAULT_WEIGHTS["rental"])),
            "infra":    float(request.args.get("infra",    DEFAULT_WEIGHTS["infra"])),
            "listings": float(request.args.get("listings", DEFAULT_WEIGHTS["listings"])),
        }
    except (ValueError, TypeError):
        weights = DEFAULT_WEIGHTS

    df = compute_gvs(load_raw(), weights=weights)

    context = {
        # ── KPI header
        "stats": summary_stats(df),

        # ── Map
        "map_html": build_map(df),

        # ── Charts
        "chart_gvs":       gvs_bar(df),
        "chart_price":     price_trend(df),
        "chart_rtm_uc":    rtm_uc_chart(df),
        "chart_yield":     rental_yield_chart(df),
        "chart_forecast":  forecast_chart(df),
        "chart_scatter":   scatter_matrix(df),

        # ── Data table
        "zones": df[[
            "area", "tier", "gvs",
            "price_2022", "price_2024", "price_growth_pct",
            "rtm_price", "uc_price", "rtm_uc_pct",
            "rent", "rental_yield_pct", "occupancy_rate",
            "listings", "infra", "declarations", "forecast_24m"
        ]].to_dict(orient="records"),

        # ── Active weights (for slider display)
        "weights": weights,
    }
    return render_template("index.html", **context)
