"""
utils/map_builder.py
====================
Folium map generator for UrbanPulse.
Renders colour-coded, sized circle markers with rich popups.
"""

import folium
import pandas as pd
from folium.plugins import MarkerCluster


_TIER_COLORS = {
    "Critical Hotspot": "#ff4757",
    "High Growth":      "#f5a623",
    "Moderate Growth":  "#4d9fff",
    "Low Activity":     "#6b7280",
}


def build_map(df: pd.DataFrame) -> str:
    """
    Build and return the Folium map as an HTML string.

    Circle radius scales with GVS score.
    Popup contains all 4 data-stream metrics.
    """
    center_lat = df["lat"].mean()
    center_lng = df["lng"].mean()

    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=12,
        tiles="CartoDB dark_matter",
    )

    for _, row in df.iterrows():
        color  = _TIER_COLORS.get(row["tier"], "#6b7280")
        radius = 8 + (row["gvs"] / 100) * 18

        popup_html = f"""
        <div style="
            font-family: 'Segoe UI', sans-serif;
            background:#0e1118; color:#d4dce8;
            border:1px solid #272e3d; border-radius:6px;
            padding:14px; min-width:230px; font-size:12px;
        ">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
                <strong style="font-size:14px">{row['area']}</strong>
                <span style="background:{color}22;color:{color};border:1px solid {color}55;
                       padding:3px 9px;border-radius:3px;font-size:11px;font-weight:700">{row['gvs']}</span>
            </div>
            <div style="color:#8896ae;font-size:10px;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">{row['tier']}</div>

            <table style="width:100%;border-collapse:collapse">
                <tr style="border-bottom:1px solid #272e3d">
                    <td style="padding:4px 0;color:#8896ae">Current Price</td>
                    <td style="text-align:right;font-family:monospace">₹{int(row['price_2024']):,}/sqft</td>
                </tr>
                <tr style="border-bottom:1px solid #272e3d">
                    <td style="padding:4px 0;color:#8896ae">Price Growth</td>
                    <td style="text-align:right;color:#3ddc84;font-family:monospace">+{row['price_growth_pct']}%</td>
                </tr>
                <tr style="border-bottom:1px solid #272e3d">
                    <td style="padding:4px 0;color:#8896ae">Rental Yield</td>
                    <td style="text-align:right;color:#2ec4b6;font-family:monospace">{row['rental_yield_pct']}%</td>
                </tr>
                <tr style="border-bottom:1px solid #272e3d">
                    <td style="padding:4px 0;color:#8896ae">RTM Premium</td>
                    <td style="text-align:right;color:#f5a623;font-family:monospace">{row['rtm_uc_pct']}%</td>
                </tr>
                <tr style="border-bottom:1px solid #272e3d">
                    <td style="padding:4px 0;color:#8896ae">Occupancy</td>
                    <td style="text-align:right;font-family:monospace">{row['occupancy_rate']}%</td>
                </tr>
                <tr style="border-bottom:1px solid #272e3d">
                    <td style="padding:4px 0;color:#8896ae">Active Listings</td>
                    <td style="text-align:right;font-family:monospace">{int(row['listings'])}</td>
                </tr>
                <tr style="border-bottom:1px solid #272e3d">
                    <td style="padding:4px 0;color:#8896ae">Infra Rating</td>
                    <td style="text-align:right;font-family:monospace">{row['infra']}/10</td>
                </tr>
                <tr>
                    <td style="padding:4px 0;color:#8896ae">24M Forecast</td>
                    <td style="text-align:right;color:#ff4757;font-family:monospace;font-weight:700">+{row['forecast_24m']}%</td>
                </tr>
            </table>
        </div>
        """

        folium.CircleMarker(
            location=[row["lat"], row["lng"]],
            radius=radius,
            color=color,
            weight=2 if row["tier"] == "Critical Hotspot" else 1.5,
            fill=True,
            fill_color=color,
            fill_opacity=0.72,
            popup=folium.Popup(popup_html, max_width=270),
            tooltip=f"{row['area']} · GVS {row['gvs']}",
        ).add_to(m)

        # Extra pulsing ring for hotspots
        if row["tier"] == "Critical Hotspot":
            folium.CircleMarker(
                location=[row["lat"], row["lng"]],
                radius=radius + 7,
                color=color,
                weight=1,
                fill=False,
                opacity=0.3,
            ).add_to(m)

    return m._repr_html_()
