"""
utils/charts.py
===============
Plotly chart builders for the UrbanPulse dashboard.
All functions return HTML fragment strings (full_html=False).
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# ── Shared Plotly layout theme
_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="'Barlow', sans-serif", color="#c8d4e8", size=11),
    margin=dict(l=36, r=16, t=36, b=36),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#272e3d"),
    xaxis=dict(gridcolor="#1d2330", linecolor="#272e3d", tickcolor="#4e5a70"),
    yaxis=dict(gridcolor="#1d2330", linecolor="#272e3d", tickcolor="#4e5a70"),
)

_COLOR_MAP = {
    "Critical Hotspot": "#ff4757",
    "High Growth":      "#f5a623",
    "Moderate Growth":  "#4d9fff",
    "Low Activity":     "#4e5a70",
}

def _fig_to_html(fig) -> str:
    fig.update_layout(**_THEME)
    return fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        config={"displayModeBar": False, "responsive": True}
    )


def gvs_bar(df: pd.DataFrame) -> str:
    """Horizontal bar chart of GVS scores, color-coded by tier."""
    df_sorted = df.sort_values("gvs", ascending=True)
    colors = [_COLOR_MAP.get(t, "#4e5a70") for t in df_sorted["tier"]]

    fig = go.Figure(go.Bar(
        x=df_sorted["gvs"],
        y=df_sorted["area"],
        orientation="h",
        marker_color=colors,
        text=df_sorted["gvs"].astype(str),
        textposition="outside",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "GVS: %{x}<br>"
            "<extra></extra>"
        )
    ))
    fig.update_layout(
        title=dict(text="Growth Velocity Score by Zone", font=dict(size=13, color="#c8d4e8")),
        xaxis_range=[0, 110],
        height=420,
    )
    return _fig_to_html(fig)


def price_trend(df: pd.DataFrame) -> str:
    """Grouped bar: price_2022 vs price_2024 per area."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Price 2022", x=df["area"], y=df["price_2022"],
        marker_color="#4d9fff", opacity=0.8
    ))
    fig.add_trace(go.Bar(
        name="Price 2024", x=df["area"], y=df["price_2024"],
        marker_color="#f5a623", opacity=0.9
    ))
    fig.update_layout(
        title=dict(text="Price Comparison: 2022 vs 2024 (₹/sqft)", font=dict(size=13, color="#c8d4e8")),
        barmode="group", height=340,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis_tickangle=-30,
    )
    return _fig_to_html(fig)


def rtm_uc_chart(df: pd.DataFrame) -> str:
    """RTM price vs UC price scatter with RTM premium annotation."""
    fig = go.Figure()
    for _, row in df.iterrows():
        color = _COLOR_MAP.get(row["tier"], "#4e5a70")
        fig.add_trace(go.Scatter(
            x=[row["uc_price"]], y=[row["rtm_price"]],
            mode="markers+text",
            text=[row["area"]],
            textposition="top center",
            textfont=dict(size=9, color="#8896ae"),
            marker=dict(size=14, color=color, opacity=0.85,
                        line=dict(color="white", width=1)),
            name=row["area"],
            hovertemplate=(
                f"<b>{row['area']}</b><br>"
                f"UC: ₹{row['uc_price']:,}<br>"
                f"RTM: ₹{row['rtm_price']:,}<br>"
                f"Premium: {row['rtm_uc_pct']}%<extra></extra>"
            )
        ))
    # Diagonal parity line
    mn = df[["uc_price","rtm_price"]].min().min()
    mx = df[["uc_price","rtm_price"]].max().max()
    fig.add_trace(go.Scatter(
        x=[mn, mx], y=[mn, mx], mode="lines",
        line=dict(color="#4e5a70", dash="dash", width=1),
        showlegend=False, hoverinfo="skip"
    ))
    fig.update_layout(
        title=dict(text="RTM vs Under Construction Price (₹/sqft)", font=dict(size=13, color="#c8d4e8")),
        xaxis_title="UC Price", yaxis_title="RTM Price",
        height=360, showlegend=False,
    )
    return _fig_to_html(fig)


def rental_yield_chart(df: pd.DataFrame) -> str:
    """Bar chart of rental yield % per zone."""
    df_sorted = df.sort_values("rental_yield_pct", ascending=False)
    colors = [_COLOR_MAP.get(t, "#4e5a70") for t in df_sorted["tier"]]
    fig = go.Figure(go.Bar(
        x=df_sorted["area"], y=df_sorted["rental_yield_pct"],
        marker_color=colors, opacity=0.88,
        text=df_sorted["rental_yield_pct"].apply(lambda v: f"{v:.2f}%"),
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Yield: %{y:.2f}%<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text="Gross Rental Yield % by Zone", font=dict(size=13, color="#c8d4e8")),
        height=300, xaxis_tickangle=-30,
        yaxis_title="Yield (%)",
    )
    return _fig_to_html(fig)


def forecast_chart(df: pd.DataFrame) -> str:
    """Horizontal bar of 24-month forecast appreciation."""
    df_sorted = df.sort_values("forecast_24m", ascending=True)
    colors = [_COLOR_MAP.get(t, "#4e5a70") for t in df_sorted["tier"]]
    fig = go.Figure(go.Bar(
        x=df_sorted["forecast_24m"],
        y=df_sorted["area"],
        orientation="h",
        marker_color=colors,
        text=df_sorted["forecast_24m"].apply(lambda v: f"+{v}%"),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>24M Forecast: +%{x}%<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text="24-Month Appreciation Forecast (%)", font=dict(size=13, color="#c8d4e8")),
        height=420, xaxis_title="Projected Appreciation (%)"
    )
    return _fig_to_html(fig)


def scatter_matrix(df: pd.DataFrame) -> str:
    """GVS vs infra vs price_growth scatter."""
    fig = px.scatter(
        df, x="price_growth_pct", y="gvs",
        size="listings", color="tier",
        color_discrete_map=_COLOR_MAP,
        hover_name="area",
        hover_data={"rental_yield_pct": True, "forecast_24m": True,
                    "infra": True, "price_growth_pct": True},
        labels={"price_growth_pct": "Price Growth (%)", "gvs": "GVS Score"},
        title="GVS vs Price Growth (bubble = listing count)",
        height=340,
    )
    fig.update_traces(marker=dict(opacity=0.85, line=dict(width=1, color="white")))
    fig.update_layout(**_THEME)
    return fig.to_html(
        full_html=False, include_plotlyjs=False,
        config={"displayModeBar": False, "responsive": True}
    )
