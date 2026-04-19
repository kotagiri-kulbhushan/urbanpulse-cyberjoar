"""
utils/data_engine.py
====================
Core data processing layer for UrbanPulse.

Implements the Growth Velocity Score (GVS) formula across 4 data streams:
  Stream 1 — Pricing Velocity     (price_growth, RTM vs UC premium)
  Stream 2 — Rental Absorption    (yield, occupancy, population shift)
  Stream 3 — Infrastructure Score (municipal declarations, infra rating)
  Stream 4 — Listing Density      (active listings, saturation index)

GVS = (Pricing × W1) + (Rental × W2) + (Infra × W3) + (Listings × W4)
Default weights: W1=0.35, W2=0.25, W3=0.25, W4=0.15
"""

import pandas as pd
import numpy as np
import os

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "data.csv")

# ── Default GVS weights
DEFAULT_WEIGHTS = {
    "pricing":  0.35,
    "rental":   0.25,
    "infra":    0.25,
    "listings": 0.15,
}

def load_raw() -> pd.DataFrame:
    """Load raw CSV and return as DataFrame."""
    return pd.read_csv(DATA_PATH)


def compute_gvs(df: pd.DataFrame, weights: dict = None) -> pd.DataFrame:
    """
    Process raw DataFrame and compute all derived metrics including GVS.

    Parameters
    ----------
    df      : Raw DataFrame from CSV
    weights : Dict with keys pricing, rental, infra, listings (must sum ~1.0)

    Returns
    -------
    Enriched DataFrame with all computed columns.
    """
    w = weights or DEFAULT_WEIGHTS
    df = df.copy()

    # ── STREAM 1: Pricing Velocity ─────────────────────────
    df["price_growth"]      = (df["price_2024"] - df["price_2022"]) / df["price_2022"]
    df["rtm_uc_premium"]    = (df["rtm_price"]  - df["uc_price"])   / df["uc_price"]
    # Normalise 0→1
    pg_min, pg_max = df["price_growth"].min(), df["price_growth"].max()
    df["pricing_score"] = (df["price_growth"] - pg_min) / (pg_max - pg_min + 1e-9)
    # Bonus for high RTM premium (supply lag signal)
    df["pricing_score"] = df["pricing_score"] + 0.1 * df["rtm_uc_premium"]
    df["pricing_score"] = df["pricing_score"].clip(0, 1)

    # ── STREAM 2: Rental Absorption ────────────────────────
    # Assume standard 1000 sqft unit; price_2024 is ₹/sqft
    df["rental_yield"]      = (df["rent"] * 12) / (df["price_2024"] * 1000)
    # Pop shift already normalised per-unit in CSV (per 1000 residents)
    ry_min, ry_max = df["rental_yield"].min(), df["rental_yield"].max()
    oc_min, oc_max = df["occupancy_rate"].min(), df["occupancy_rate"].max()
    ps_min, ps_max = df["pop_shift"].min(), df["pop_shift"].max()
    df["rental_score"] = (
        0.50 * (df["rental_yield"] - ry_min)   / (ry_max - ry_min + 1e-9) +
        0.30 * (df["occupancy_rate"] - oc_min)  / (oc_max - oc_min + 1e-9) +
        0.20 * (df["pop_shift"] - ps_min)       / (ps_max - ps_min + 1e-9)
    )

    # ── STREAM 3: Infrastructure (Municipal Declarations) ──
    # infra: raw 1–10 rating; declarations: count of active gov notifications
    df["infra_score"] = (
        0.60 * df["infra"] / 10.0 +
        0.40 * (df["declarations"] / df["declarations"].max())
    )

    # ── STREAM 4: Listing Density ──────────────────────────
    ls_min, ls_max = df["listings"].min(), df["listings"].max()
    df["listing_score"] = (df["listings"] - ls_min) / (ls_max - ls_min + 1e-9)

    # ── COMPOSITE GVS (0→100) ─────────────────────────────
    df["gvs_raw"] = (
        w["pricing"]  * df["pricing_score"] +
        w["rental"]   * df["rental_score"]  +
        w["infra"]    * df["infra_score"]   +
        w["listings"] * df["listing_score"]
    )
    gvs_min, gvs_max = df["gvs_raw"].min(), df["gvs_raw"].max()
    df["gvs"] = ((df["gvs_raw"] - gvs_min) / (gvs_max - gvs_min + 1e-9) * 100).round(1)

    # ── Tier classification ────────────────────────────────
    df["tier"] = df["gvs"].apply(_classify_tier)

    # ── Forecast (24-month projected appreciation %) ───────
    df["forecast_24m"] = (
        df["price_growth"] * 100 * 1.4 +
        df["infra_score"]  * 8
    ).round(1)

    # ── Round display columns ──────────────────────────────
    df["price_growth_pct"] = (df["price_growth"] * 100).round(1)
    df["rental_yield_pct"] = (df["rental_yield"] * 100).round(2)
    df["rtm_uc_pct"]       = (df["rtm_uc_premium"] * 100).round(1)

    return df


def _classify_tier(gvs: float) -> str:
    if gvs >= 80:
        return "Critical Hotspot"
    elif gvs >= 60:
        return "High Growth"
    elif gvs >= 40:
        return "Moderate Growth"
    return "Low Activity"


def get_processed() -> pd.DataFrame:
    """Convenience: load + process in one call."""
    return compute_gvs(load_raw())


def summary_stats(df: pd.DataFrame) -> dict:
    """Return top-level KPIs for the dashboard header."""
    return {
        "total_zones":     len(df),
        "hotspot_count":   int((df["gvs"] >= 80).sum()),
        "high_growth":     int(((df["gvs"] >= 60) & (df["gvs"] < 80)).sum()),
        "avg_gvs":         round(df["gvs"].mean(), 1),
        "top_zone":        df.loc[df["gvs"].idxmax(), "area"],
        "top_gvs":         df["gvs"].max(),
        "avg_yield":       round(df["rental_yield_pct"].mean(), 2),
        "total_listings":  int(df["listings"].sum()),
        "avg_appreciation":round(df["price_growth_pct"].mean(), 1),
        "avg_forecast":    round(df["forecast_24m"].mean(), 1),
    }
