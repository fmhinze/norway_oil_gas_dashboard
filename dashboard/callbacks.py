from dash import Output, Input, MATCH, callback_context
import pandas as pd
import plotly.express as px
import numpy as np
import dash_mantine_components as dmc
import json
from utility import human_format, custom_round

# ========== CONSTANTS ==========
COLOUR_MAP = {
    "Oil": "#228be6", #blue.6
    "NGL": "#74c0fc", #blue.3
    "Condensate": "#38d9a9",#teal.4
    "Gas": "#96f2d7", #teal.2
}

USE_UNIT = {"Oil": "Oil", "Gas": "Gas", "NGL": "Oil", "Condensate": "Oil"}

with open("processed_data/unit_conversion.json", "r") as f:
    UNIT_CONVERSIONS = json.load(f)

RESERVE_ORG_PREFIX = "fldRecoverable"
RESERVE_REMAIN_PREFIX = "fldRemaining"

# ========== UTILITY FUNCTIONS ==========


def get_conversion_factor(product, unit_choice, max_value):
    if product in USE_UNIT:
        for entry in UNIT_CONVERSIONS[USE_UNIT[product]][unit_choice]:
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


def make_pie_chart(
    filtered, df, df_reserves, product, selected_field, product_unit, window_height
):
    filtered_total_extracted = filtered[filtered["product"] == product][
        "volume_net"
    ].sum()

    if selected_field is not None:
        df = df[df["field"] == selected_field].copy()

    total_extracted = df[df["product"] == product]["volume_net"].sum()

    if selected_field is None:
        remain_res = df_reserves[RESERVE_REMAIN_PREFIX + product].sum()
    else:
        remain_res = df_reserves.loc[
            df_reserves["fldName"] == selected_field, RESERVE_REMAIN_PREFIX + product
        ].sum()

    factor, unit = get_conversion_factor(
        product, product_unit, remain_res + total_extracted
    )
    magnitude, multiplier = human_format(
        (remain_res + total_extracted) * factor, return_list=True
    )

    pie_data = []
    if filtered_total_extracted != total_extracted:
        pie_data.append(
            {
                "name": "Extracted prior/after",
                "value": custom_round(
                    (total_extracted - filtered_total_extracted) * factor / magnitude, 2
                ),
                "color": "gray.8",
            }
        )

    pie_data.append(
        {
            "name": f"Extracted ({multiplier}{unit})",
            "value": custom_round((filtered_total_extracted) * factor / magnitude, 2),
            "color": COLOUR_MAP[product],
        }
    )

    pie_data.append(
        {
            "name": f"Remaining ({multiplier}{unit})",
            "value": custom_round((remain_res) * factor / magnitude, 2),
            "color": "gray.6",
        }
    )

    total = custom_round((remain_res + total_extracted) * factor / magnitude, 2)

    chart_hieght = window_height * 0.15

    return dmc.PieChart(
        data=pie_data,
        size=chart_hieght,
        withLabels=True,
        withLabelsLine=True,
        labelsPosition="outside",
        labelsType="value",
        strokeWidth=1,
        withTooltip=True,
        paddingAngle=0,
        style={"width": chart_hieght * 1.9, "height": chart_hieght * 1.9},
        # chartLabel = f"{total} {unit} {product_unit}"
    )


def make_stacked_area_chart(
    df,
    granularity,
    products,
    unit_gas,
    unit_oil,
    clickData,
):
    # 1. Group by month or year
    if granularity == "annual":
        df["year"] = df["date"].dt.year
        ts_data = (
            df.groupby(["year", "product"])[["volume_net_converted", "volume_net"]]
            .sum()
            .reset_index()
            .rename(columns={"year": "date"})
        )
        ts_data["date"] = pd.to_datetime(ts_data["date"], format="%Y")
    else:
        ts_data = (
            df.groupby(["date", "product"])[["volume_net_converted", "volume_net"]]
            .sum()
            .reset_index()
        )

    # 2. If gas and other products, force oil equivalent as unit.
    if "Gas" in products and len(products) > 1:
        unit = "tonnes of oil equivalent"
    elif "Gas" not in products:
        unit = unit_oil
    else:
        unit = unit_gas

    # 3. Convert data to correct unit
    for product in products:
        factor, unit_label = get_conversion_factor(
            product, unit, ts_data["volume_net"].max()
        )
        ts_data.loc[ts_data["product"] == product, "volume_net_converted"] = (
            ts_data.loc[ts_data["product"] == product, "volume_net"] * factor
        )
    
    # 4. auxiliary data  
    grouped = (
        ts_data.groupby(
            ["date", "product"]
        )["volume_net_converted"].sum().reset_index()
    )
    
    # 4.1 remove products that are null
    totals_p = grouped.groupby("product")["volume_net_converted"].sum()
    products = [p for p in products if p in totals_p and totals_p[p] > 0]
    ts_data = ts_data[ts_data["product"].isin(products)]
    
    # 4.2 scale values for readability
    # TODO: Remove once sure it is reduandant
    totals_d_max = grouped.groupby("date")["volume_net_converted"].sum().max()
    factor, scale = human_format(totals_d_max / 10, return_list=True)
    ts_data["volume_net_converted"] = ts_data["volume_net_converted"].apply(
        lambda x: custom_round(x / factor, 2)
    )
    if scale != "":
        scale = "USING REDUNDANT FORMATER!"

    # 5. Create stacked area chart
    # 5.1 Create y-label
    y_label = (
        f"Net Production [{scale}{unit_label}]" 
        if unit_label 
        else "Net Production"
    )

    # 5.2 Create chart
    time_fig = px.area(
        ts_data,
        x="date",
        y="volume_net_converted",
        color="product",
        color_discrete_map=COLOUR_MAP,
        category_orders={"product": products},
        custom_data=["volume_net_converted"]
    )

    # 5.3 Make hover tooltip
    time_fig.update_traces(
        hovertemplate=f"%{{fullData.name}}: %{{customdata[0]}} {scale}{unit_label}"
    )

    # Make the unified hover *title* show only the year when annual
    if granularity == "annual":
        time_fig.update_xaxes(hoverformat="%Y", tickformat="%Y")  # header: 2019; ticks: 2019
    else:
        time_fig.update_xaxes(hoverformat="%Y %B", tickformat="%Y-%m")  # e.g. 2019 January

    # 5.4 Control layout
    time_fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        font=dict(size=14),
        legend=dict(orientation="h", y=1.1),
        hovermode="x unified",
        xaxis=dict(
            title_text="Date",
            title_font=dict(size=16, color="white"),  # axis title
            tickfont=dict(size=14,  color="white"), # tick labels
        ),
        yaxis=dict(
            title_text=y_label,
            title_font=dict(size=16, color="white"),
            tickfont=dict(size=14, color="white"),
        )
    )


    # 6. Higlight current selected date, controlling what data is on map.
    if clickData and "points" in clickData:
        selected_date = pd.to_datetime(clickData["points"][0]["x"])
    else:
        selected_date = ts_data["date"].max()

    time_fig.add_shape(
        type="line",
        x0=selected_date,
        x1=selected_date,
        y0=0,
        y1=1,
        xref="x",
        yref="paper",
        line=dict(color="red", width=2, dash="dot"),
    )

    time_fig.add_annotation(
        x=selected_date,
        y=1,
        xref="x",
        yref="paper",
        text="Map",
        showarrow=False,
        font=dict(size=12, color="red"),
        bgcolor="white",
        bordercolor="red",
        borderwidth=1,
        borderpad=2,
    )

    return time_fig, selected_date


# ========== MAP ================


def make_map_figure(
    df, selected_field, products, granularity, selected_date, unit_oil, unit_gas
):
    if granularity == "annual":
        map_df = df[(df["date"].dt.year == selected_date.year)]
        map_df["date_str"] = f"{selected_date.year}"
    else:
        map_df = df[(df["date"] == selected_date)]
        map_df["date_str"] = selected_date.strftime("%Y-%m")

    map_df["volume_net_converted"] = map_df["volume_net"].copy()
    for product in products:
        factor, _ = get_conversion_factor(product, "tonnes of oil equivalent", 0)
        map_df[map_df["product"] == product]["volume_net_converted"] = (
            map_df[map_df["product"] == product]["volume_net"] * factor
        )

    date_lable = map_df["date_str"].iloc[0]
    map_df = (
        map_df.groupby(["field", "avg_lat", "avg_lon", "date_str"])[
            ["volume_net", "volume_net_converted"]
        ]
        .sum()
        .reset_index()
    )

    # Style markers
    if selected_field == None:
        map_df["opacity_val"] = 0.2
        map_df["marker_color"] = "#0800ff"
    else:
        map_df["opacity_val"] = map_df["field"].apply(
            lambda f: 1 if f == selected_field else 0.01
        )
        map_df["marker_color"] = map_df["field"].apply(
            lambda f: "#0800ff" if f != selected_field else "#ff0000"
        )

    # Build the map figure
    fig = px.scatter_mapbox(
        map_df,
        lat="avg_lat",
        lon="avg_lon",
        size="volume_net_converted",
        hover_name="field",
        title=f"Production by Field ({date_lable})",
        mapbox_style="carto-positron",
        zoom=3.3,
        center={"lat": 66, "lon": 11},
        custom_data=["field", "volume_net_converted"],
    )
    fig.update_traces(
        hovertemplate=f" <b> %{{customdata[0]}} </b>  <br> Volume:  %{{customdata[1]}} t.o.e."
    )
    fig.update_traces(
        marker=dict(color=map_df["marker_color"], opacity=map_df["opacity_val"])
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        font=dict(size=12),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ========== CALLBACKS ==========


def register_callbacks(app, df, df_reserves):

    @app.callback(
        Output("month-picker-container", "style"),
        Output("year-picker-container", "style"),
        Input("granularity-toggle", "value"),
    )
    def toggle_date_inputs(granularity):
        return (
            ({}, {"display": "none"})
            if granularity == "monthly"
            else ({"display": "none"}, {})
        )

    # Drawer
    @app.callback(
        Output("drawer", "opened"),
        Input("drawer-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def drawer_demo(n_clicks):
        return True

    # Main Callback
    @app.callback(
        [
            Output("map-view", "figure"),
            Output("field-mini-timeseries", "figure"),
            Output("pie-chart-oil", "children"),
            Output("pie-chart-gas", "children"),
            Output("pie-chart-ngl", "children"),
            Output("pie-chart-condensate", "children"),
        ],
        [
            Input("product-filter", "value"),
            Input("granularity-toggle", "value"),
            Input("field-filter", "value"),
            Input("unit-oil", "value"),
            Input("unit-gas", "value"),
            Input({"type": "date-picker", "subtype": "month"}, "value"),
            Input({"type": "date-picker", "subtype": "year"}, "value"),
            Input("window-height", "data"),
            Input("field-mini-timeseries", "clickData"),
        ],
    )
    def update_graphs(
        products,
        granularity,
        selected_field,
        unit_oil,
        unit_gas,
        month_range,
        year_range,
        window_height,
        clickData,
    ):

        # Order products
        tmp_products = []
        for product in ["Oil", "NGL", "Condensate", "Gas"]:
            if product in products:
                tmp_products.append(product)

        products = tmp_products
        del tmp_products

        date_range = year_range if granularity == "annual" else month_range
        if date_range is None or len(date_range) != 2:
            date_range = [df["date"].min(), df["date"].max()]
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(
            date_range[1]
        )

        if granularity == "annual":
            filtered = df[
                (df["product"].isin(products))
                & (df["date"].apply(lambda x: x.year) >= start_date.year)
                & (df["date"].apply(lambda x: x.year) <= end_date.year)
            ]
        else:
            filtered = df[
                (df["product"].isin(products))
                & (df["date"] >= start_date)
                & (df["date"] <= end_date)
            ]

        if selected_field == "All":
            selected_field = None
        else:
            filtered = filtered[filtered["field"] == selected_field]

        # Apply units
        # Get conversion factor based on product type
        filtered["volume_net_converted"] = filtered["volume_net"]
        for product in products:
            factor, _ = get_conversion_factor(
                product, unit_gas if product == "Gas" else unit_oil, 0
            )

            # Style markers
            filtered[filtered["product"] == product]["volume_net_converted"] *= factor

        # === Donut + Timeseries ===
        pie_fig_oil = make_pie_chart(
            filtered, df, df_reserves, "Oil", selected_field, unit_oil, window_height
        )
        pie_fig_gas = make_pie_chart(
            filtered, df, df_reserves, "Gas", selected_field, unit_gas, window_height
        )
        pie_fig_condensate = make_pie_chart(
            filtered,
            df,
            df_reserves,
            "Condensate",
            selected_field,
            unit_oil,
            window_height,
        )
        pie_fig_ngl = make_pie_chart(
            filtered, df, df_reserves, "NGL", selected_field, unit_oil, window_height
        )

        mini_ts_fig, selected_date = make_stacked_area_chart(
            filtered,
            granularity,
            products,
            unit_gas,
            unit_oil,
            clickData,
        )

        # === Map ===
        if selected_date is None:
            selected_date = end_date
        map_fig = make_map_figure(
            df, selected_field, products, granularity, selected_date, unit_oil, unit_gas
        )

        return (
            map_fig,
            mini_ts_fig,
            pie_fig_oil,
            pie_fig_gas,
            pie_fig_ngl,
            pie_fig_condensate,
        )
