from dash import Output, Input
import pandas as pd
import plotly.express as px
import numpy as np

import json

COLOUR_MAP = {
    "Oil" : "#03045e",
    "NGL" : "#0077b6",
    "Condensate" : "#00b4d8",
    "Gas": "#90e0ef"
    
}

with open("processed_data/unit_conversion.json", "r") as f:
    UNIT_CONVERSIONS = json.load(f)

def register_callbacks(app, df):
    @app.callback(
        [Output("time-series", "figure"),
         Output("map-view", "figure"),
         Output("field-pie-chart", "figure"),
         Output("field-mini-timeseries", "figure")],
        [Input("product-filter", "value"),
         Input("show-gross-toggle", "value"),
         Input("date-filter", "start_date"),
         Input("date-filter", "end_date"),
         Input("granularity-toggle", "value"),
         Input("time-series", "clickData"),
         Input("field-filter", "value"),
         Input("unit-oil", "value"),
         Input("unit-gas", "value")]
    )
    def update_graphs(product, show_gross, start_date, end_date, granularity, 
                      clickData, selected_field, unit_oil, unit_gas):
        # === 1. FILTERING ===
        mask = (
            (df["product"] == product) &
            (df["date"] >= pd.to_datetime(start_date)) &
            (df["date"] <= pd.to_datetime(end_date))
        )
        filtered = df[mask]
        
        # Apply field filter if selected
        if selected_field:
            filtered = filtered[filtered["field"] == selected_field]


        # === 2. TIME SERIES ===

        # Choose columns
        agg_cols = ["volume_net"]
        if "show" in show_gross:
            agg_cols.append("volume_gross")

        # Group by month or year
        if granularity == "annual":
            filtered["year"] = filtered["date"].dt.year
            ts_data = (
                filtered.groupby("year")[agg_cols]
                .sum()
                .reset_index()
                .rename(columns={"year": "date"})
            )
            ts_data["date"] = pd.to_datetime(ts_data["date"], format="%Y")
        else:
            ts_data = (
                filtered.groupby("date")[agg_cols]
                .sum()
                .reset_index()
            )
            

            
        
        unit_choice = unit_oil if product in ["Oil", "Condensate", "NGL"] else unit_gas
        factor, unit_label = get_conversion_factor(product, unit_choice, ts_data["volume_net"].max())
            
        ts_data["volume_net"] *= factor
        if "show" in show_gross:
            ts_data["volume_gross"] *= factor
        
        y_label = f"Net Production ({unit_label})" if unit_label else "Net Production"

        time_fig = px.line(
            ts_data, x="date", y="volume_net",
            labels={"volume_net": y_label, "date": "Date"},
            title=f"{product} Production ({granularity.title()})"
        )


        # Add gross if selected
        if "show" in show_gross:
            # Gross line
            time_fig.add_scatter(
                x=ts_data["date"],
                y=ts_data["volume_gross"],
                name="Gross Production",
                mode="lines"
            )

            # Waste bar: 100 * (gross - net) / gross, but only if diff > 1
            ts_data["waste_pct"] = np.where(
                np.abs((ts_data["volume_gross"] - ts_data["volume_net"]) / ts_data["volume_gross"]) <= 1 ,
                100 * (ts_data["volume_gross"] - ts_data["volume_net"]) / ts_data["volume_gross"],
                0
            )

            # Add as bar chart
            time_fig.add_bar(
                x=ts_data["date"],
                y=ts_data["waste_pct"],
                name="Waste (%)",
                yaxis="y2"
            )

            # Add second y-axis
            time_fig.update_layout(
                yaxis2=dict(title="Waste (%)", overlaying="y", side="right")
            )

        # Shared layout
        time_fig.update_layout(
            margin=dict(l=40, r=20, t=40, b=30),
            font=dict(size=12),
            legend=dict(orientation="h", y=-0.25)
        )

        # Highlight current date on time series
        if clickData and "points" in clickData:
            selected_date = pd.to_datetime(clickData["points"][0]["x"])
        else:
            selected_date = ts_data["date"].max()

        time_fig.add_shape(
            type="line",
            x0=selected_date, x1=selected_date,
            y0=0, y1=1,
            xref='x', yref='paper',
            line=dict(color="red", width=2, dash="dot")
        )

        time_fig.add_annotation(
            x=selected_date,
            y=1.02,
            xref='x',
            yref='paper',
            text="Map",
            showarrow=False,
            font=dict(size=12, color="red"),
            bgcolor="white",
            bordercolor="red",
            borderwidth=1,
            borderpad=2
        )

        # === 3. MAP ===

        # Aggregate map data based on granularity
        if granularity == "annual":
            year = selected_date.year
            map_df = (
                df[
                    (df["product"] == product) &
                    (df["date"].dt.year == year)
                ]
                .groupby("field", as_index=False)
                .agg({
                    "volume_net": "sum",
                    "avg_lat": "first",
                    "avg_lon": "first"
                })
            )
            map_df["date_str"] = f"{year}"
        else:
            map_df = df[
                (df["product"] == product) &
                (df["date"] == selected_date)
            ].copy()
            map_df["date_str"] = selected_date.strftime("%Y-%m")

        # Create styling columns
        map_df["volume_net"] *= factor
        map_df["opacity_val"] = map_df["field"].apply(
            lambda f: 0.5 if (not selected_field or f == selected_field) else 0.2
        )
        map_df["marker_color"] = map_df["field"].apply(
            lambda f: "#6e3500" if (not selected_field or f == selected_field) else "#999999"
        )

        # Plot the map
        map_fig = px.scatter_mapbox(
            map_df,
            lat="avg_lat",
            lon="avg_lon",
            size="volume_net",
            hover_name="field",
            title=f"{product} Production by Field ({map_df['date_str'].iloc[0]})",
            mapbox_style="carto-positron",
            zoom=3.5,
            center={"lat": 64.5, "lon": 15},
        )

        # Now apply custom colour and opacity
        map_fig.update_traces(
            marker=dict(
                color=map_df["marker_color"],
                opacity=map_df["opacity_val"]
            )
        )

        # Layout tweaks
        map_fig.update_layout(
            uirevision="map",
            margin=dict(l=40, r=20, t=40, b=30),
            font=dict(size=12),
            showlegend=False
        )

        pie_fig = get_field_product_mix(df, selected_field, UNIT_CONVERSIONS)
        mini_ts_fig = get_field_stacked_timeseries(df, selected_field, granularity, UNIT_CONVERSIONS)
        
        return time_fig, map_fig, pie_fig, mini_ts_fig
    
    
def get_field_product_mix(df, selected_field, unit_conversions):
    field_df = df[df["field"] == selected_field].copy()
    field_df = field_df.groupby("product")["volume_net"].sum().reset_index()

    oil_eq = []
    for _, row in field_df.iterrows():
        product = row["product"]
        vol = row["volume_net"]
        try:
            factor, _ = get_conversion_factor(product, "tonnes of oil equivalent",0)
        except KeyError:
            factor = 1  # fallback
        oil_eq.append(vol * factor)

    field_df["oil_equivalent"] = oil_eq
    pie_fig = px.pie(
        field_df,
        names="product",
        color="product",
        values="oil_equivalent",
        title=f"{selected_field}: Product Mix (t.o.e)",
        hole=0.4,
        color_discrete_map=COLOUR_MAP
    )
    
    pie_fig.update_layout(margin=dict(t=30, b=0, l=0, r=0))
    return pie_fig


def get_field_stacked_timeseries(df, selected_field, granularity, unit_conversions):
    field_df = df[df["field"] == selected_field].copy()
    field_df = field_df.copy()

    def oil_equiv(row):
        product = row["product"]
        try:
            conversions = unit_conversions[product]["tonnes of oil equivalent"]
            if isinstance(conversions, list) and len(conversions) > 0:
                factor = conversions[0]["factor"]
            else:
                factor = 1
        except (KeyError, IndexError, TypeError):
            factor = 1
        return row["volume_net"] * factor

    field_df["oil_equivalent"] = field_df.apply(oil_equiv, axis=1)

    if granularity == "annual":
        field_df["year"] = field_df["date"].dt.year
        group = field_df.groupby(["year", "product"])["oil_equivalent"].sum().reset_index()
        group = group.rename(columns={"year": "date"})
        group["date"] = pd.to_datetime(group["date"], format="%Y")
    else:
        group = field_df.groupby(["date", "product"])["oil_equivalent"].sum().reset_index()

    mini_fig = px.area(
        group,
        x="date",
        y="oil_equivalent",
        color="product",
        title=f"{selected_field}: Stacked Production (t.o.e)",
        color_discrete_map=COLOUR_MAP,
        category_orders={"product": ["Oil", "NGL", "Condensate", "Gas"]}
    )
    mini_fig.update_layout(
        margin=dict(t=30, b=30, l=30, r=10),
        legend=dict(orientation="h", y=-0.2)
    )
    return mini_fig


# Unit Conversion
def get_conversion_factor(product, unit_choice, max_value):
    if product in UNIT_CONVERSIONS:
        for entry in UNIT_CONVERSIONS[product][unit_choice]:
            if max_value*entry["factor"] > 1:
                break
            
        # if condition fails, samllest is picked
        return entry["factor"], entry["unit"] 
    else:
        # to avoid confusion
        return 0, None