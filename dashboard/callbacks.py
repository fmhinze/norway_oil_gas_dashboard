from dash import Output, Input, MATCH, callback_context
import pandas as pd
import plotly.express as px
import numpy as np
import dash_mantine_components as dmc
import json

from utility import human_format, custom_round

# ========== CONSTANTS ==========
COLOUR_MAP = {
    "Oil": "#03045e",
    "NGL": "#0077b6",
    "Condensate": "#00b4d8",
    "Gas": "#90e0ef"
}

with open("processed_data/unit_conversion.json", "r") as f:
    UNIT_CONVERSIONS = json.load(f)

# ========== UTILITY FUNCTIONS ==========

def get_conversion_factor(product, unit_choice, max_value):
    if product in UNIT_CONVERSIONS:
        for entry in UNIT_CONVERSIONS[product][unit_choice]:
            if max_value * entry["factor"] > 1:
                break
        return entry["factor"], entry["unit"]
    return 0, None

def oil_equiv(row, unit_conversions):
    product = row["product"]
    try:
        conversions = unit_conversions[product]["tonnes of oil equivalent"]
        return row["volume_net"] * conversions[-1]["factor"]
    except Exception:
        return row["volume_net"]

# ========== CHART COMPONENTS ==========

def make_pie_chart(df):
    """if not selected_field:
        return dmc.DonutChart(data=[])

    #field_df = df[df["field"] == selected_field].copy()"""
    df = df.groupby("product")["volume_net_converted"].sum().reset_index().copy()

    pie_data, total_oil_eq = [], 0
    for _, row in df.iterrows():
        vol = row["volume_net_converted"]
        if vol == 0:
            continue
        factor, _ = get_conversion_factor(row["product"], "tonnes of oil equivalent", 0)
        oil_eq = vol * factor
        pie_data.append({
            "name": row["product"],
            "value": oil_eq,
            "color": COLOUR_MAP[row["product"]]
        })
        total_oil_eq += oil_eq
        
    factor, unit = human_format(total_oil_eq/10, return_list=True)
    for item in pie_data:
        item["value"] = custom_round(item["value"]/factor, 2)
    
    total_oil_eq = custom_round(total_oil_eq/factor, 2)

    return dmc.DonutChart(
        data=pie_data,
        thickness=25,
        withTooltip=True,
        withLabelsLine=True,
        chartLabel=f"{total_oil_eq} {unit} t.o.e."
    )

def make_stacked_area_chart(df, granularity, unit_conversions, window_height):
    chart_height = int(0.3 * window_height) - 20 if window_height else 200

    df = df.copy()
    df["oil_equivalent"] = df.apply(lambda r: oil_equiv(r, unit_conversions), axis=1)

    if granularity == "annual":
        df["date"] = df["date"].dt.year.astype(str)
    else:
        df["date"] = df["date"].dt.strftime("%Y-%m")

    grouped = df.groupby(["date", "product"])["oil_equivalent"].sum().reset_index()
    totals = grouped.groupby("product")["oil_equivalent"].sum()
    products = [p for p in ["Oil", "NGL", "Condensate", "Gas"] if p in totals and totals[p] > 0]
    
    factor, unit = human_format(grouped.groupby("date")["oil_equivalent"].sum().max()/10,return_list=True)

    data = grouped[grouped["product"].isin(products)]
    data["oil_equivalent"] /= factor
    data["oil_equivalent"] = data["oil_equivalent"].apply((lambda x: custom_round(x,2) ))
    pivoted = data.pivot(index="date", columns="product", values="oil_equivalent").fillna(0).reset_index()
    records = pivoted.to_dict(orient="records")

    series = [{"name": p, "color": COLOUR_MAP[p]} for p in products]

    return dmc.AreaChart(
        dataKey="date",
        data=records,
        series=series,
        type="stacked",
        h=chart_height,
        curveType="Linear",
        tickLine="xy",
        gridAxis="x",
        withGradient=False,
        withXAxis=True,
        withYAxis=True,
        withDots=False,
        withLegend=True,
        yAxisLabel=f"{unit} Tonnes of Oil Equivalent"
    )
    
# ========== MAP ================

def make_map_figure(df, selected_field, product, granularity, selected_date, unit_oil, unit_gas):
    if granularity == "annual":
        map_df = df[
            (df["product"] == product) &
            (df["date"].dt.year == selected_date.year)
        ]
        map_df["date_str"] = f"{selected_date.year}"
    else:
        map_df = df[
            (df["product"] == product) &
            (df["date"] == selected_date)
        ]
        map_df["date_str"] = selected_date.strftime("%Y-%m")

    # Get conversion factor based on product type
    factor, _ = get_conversion_factor(product, unit_oil if product in ["Oil", "Condensate", "NGL"] else unit_gas, 1)

    # Style markers
    map_df["volume_net"] *= factor
    map_df["opacity_val"] = map_df["field"].apply(lambda f: 1 if f == selected_field else 0.1)
    map_df["marker_color"] = map_df["field"].apply(lambda f: COLOUR_MAP.get(product, "#cccccc") if f != selected_field else "#ff0000")

    # Build the map figure
    fig = px.scatter_mapbox(
        map_df,
        lat="avg_lat",
        lon="avg_lon",
        size="volume_net",
        hover_name="field",
        title=f"{product} Production by Field ({map_df['date_str'].iloc[0]})",
        mapbox_style="carto-positron",
        zoom=3.3,
        center={"lat": 66, "lon": 11},
    )
    fig.update_traces(marker=dict(
        color=map_df["marker_color"],
        opacity=map_df["opacity_val"]
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        font=dict(size=12),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    return fig


# ========== CALLBACKS ==========

def register_callbacks(app, df):
    @app.callback(
        Output("month-picker-container", "style"),
        Output("year-picker-container", "style"),
        Input("granularity-toggle", "value")
    )
    def toggle_date_inputs(granularity):
        return ({}, {"display": "none"}) if granularity == "monthly" else ({"display": "none"}, {})

    @app.callback(
        Output("drawer", "opened"),
        Input("drawer-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def drawer_demo(n_clicks):
        return True

    @app.callback(
        [Output("map-view", "figure"),
         Output("field-pie-chart", "children"),
         Output("field-mini-timeseries", "children")],
        [Input("product-filter", "value"),
         Input("granularity-toggle", "value"),
         Input("field-filter", "value"),
         Input("unit-oil", "value"),
         Input("unit-gas", "value"),
         Input({"type": "date-picker", "subtype": "month"}, "value"),
         Input({"type": "date-picker", "subtype": "year"}, "value"),
         Input("window-height", "data")]
    )
    def update_graphs(products, granularity, selected_field, unit_oil, unit_gas, month_range, year_range, window_height):
        
        date_range = year_range if granularity == "annual" else month_range
        if date_range is None or len(date_range) != 2:
            date_range = [df["date"].min(), df["date"].max()]
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])

        filtered = df[
            (df["product"].isin(products)) &
            (df["date"] >= start_date) &
            (df["date"] <= end_date)
        ]
        
        if selected_field == "All":
            selected_field = None,
        else:
            filtered = filtered[filtered["field"] == selected_field]
        
        #Apply units
        # Get conversion factor based on product type
        filtered["volume_net_converted"] = filtered["volume_net"]
        for product in products:
            factor, _ = get_conversion_factor(product, unit_gas if product == "Gas" else unit_oil, 1)

            # Style markers
            filtered[filtered["product"] == product]["volume_net_converted"] *= factor
        
        
        

        # === Map ===
        selected_date = end_date
        map_fig = make_map_figure(df, selected_field, product, granularity, selected_date, unit_oil, unit_gas)

        # === Donut + Timeseries ===
        pie_fig = make_pie_chart(filtered)
        mini_ts_fig = make_stacked_area_chart(filtered, granularity, UNIT_CONVERSIONS, window_height)

        return map_fig, pie_fig, mini_ts_fig
