from dash import html, dcc
import plotly.io as pio
import dash_mantine_components as dmc


pio.templates.default = "plotly_dark"

def serve_layout(df):
    return html.Div(
        [
            # to get the screen size.
            dcc.Store(id="window-height", storage_type="session"),
            html.Div(
                [
                    # AREA TOP LEFT - Info & Settings
                    dmc.Box(
                        dmc.Stack(
                            children=[
                                dmc.Button("Selections", id="drawer-button", size="m"),
                                dmc.Text("Space for non-numerical data. \n Comming soon..."),
                                dmc.Drawer(
                                    title="Dashboar Settings",
                                    id="drawer",
                                    padding="md",
                                    children=[
                                        # Select oil/gas field
                                        dmc.Select(
                                            id="field-filter",
                                            label="Field",
                                            placeholder="Select a field (optional)",
                                            value="All",
                                            data=[
                                                {"label": f, "value": f}
                                                for f in ["All"] + sorted(df["field"].unique())
                                            ],
                                            style={"marginBottom": "10px"},
                                            size="sm",
                                            searchable=True,
                                            # nothingFound="No field found",
                                            variant="filled",
                                        ),
                                        # Select what products to look at
                                        dmc.MultiSelect(
                                            label="Select Products",
                                            id="product-filter",
                                            data=[
                                                {"label": p, "value": p}
                                                for p in df["product"].unique()
                                            ],
                                            value=list(df["product"].unique()),
                                            clearable=False,
                                            style={"marginBottom": 10},
                                        ),
                                        dmc.RadioGroup(
                                            id="granularity-toggle",
                                            children=dmc.Group(
                                                [
                                                    dmc.Radio("Annual", value="annual"),
                                                    dmc.Radio("Monthly", value="monthly"),
                                                ],
                                                my=10,
                                            ),
                                            value="annual",
                                            label="Select granualrity",
                                            size="sm",
                                            my=10,
                                        ),
                                        dmc.RadioGroup(
                                            id="unit-oil",
                                            label="Units – Oil & liquids",
                                            value="sm3",
                                            size="xs",
                                            my=10,
                                            children=dmc.Group(
                                                [
                                                    dmc.Tooltip(
                                                        label="Standardised cubic meters",
                                                        children=dmc.Radio(
                                                            "Sm3", value="sm3"
                                                        ),
                                                    ),
                                                    dmc.Tooltip(
                                                        label="Barrels",
                                                        children=dmc.Radio(
                                                            "bbl", value="barrels"
                                                        ),
                                                    ),
                                                    dmc.Tooltip(
                                                        label="Tonnes of oil equivalent",
                                                        children=dmc.Radio(
                                                            "t.o.e.",
                                                            value="tonnes of oil equivalent",
                                                        ),
                                                    ),
                                                ],
                                                my=10,
                                            ),
                                        ),
                                        dmc.RadioGroup(
                                            id="unit-gas",
                                            label="Units – Gas",
                                            value="sm3",
                                            size="xs",
                                            my=10,
                                            children=dmc.Group(
                                                [
                                                    dmc.Tooltip(
                                                        label="Standardised cubic meters",
                                                        children=dmc.Radio(
                                                            "Sm3", value="sm3"
                                                        ),
                                                    ),
                                                    dmc.Tooltip(
                                                        label="British thermal unit",
                                                        children=dmc.Radio(
                                                            "Btu", value="Btu"
                                                        ),
                                                    ),
                                                    dmc.Tooltip(
                                                        label="Watt hours",
                                                        children=dmc.Radio(
                                                            "Wh", value="Watt hours"
                                                        ),
                                                    ),
                                                    dmc.Tooltip(
                                                        label="Cubic feet",
                                                        children=dmc.Radio(
                                                            "cf", value="cubic feet"
                                                        ),
                                                    ),
                                                ],
                                                my=10,
                                            ),
                                        ),
                                        html.Div(
                                            dmc.MonthPickerInput(
                                                id={
                                                    "type": "date-picker",
                                                    "subtype": "month",
                                                },
                                                type="range",
                                                label="Date Range (Monthly)",
                                                value=[df["date"].min(), df["date"].max()],
                                            ),
                                            id="month-picker-container",
                                        ),
                                        html.Div(
                                            dmc.YearPickerInput(
                                                id={
                                                    "type": "date-picker",
                                                    "subtype": "year",
                                                },
                                                type="range",
                                                label="Date Range (Annual)",
                                                value=[df["date"].min(), df["date"].max()],
                                            ),
                                            id="year-picker-container",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        w="20%",
                        mih="70%",
                        p="10px",
                        bd="1px solid dark.4",
                    ),
                    dmc.Box(
                        [

                            dmc.Group(
                                children=[
                                    card_for_product("pie-chart-oil", "Oil"),
                                    card_for_product("pie-chart-gas", "Gas"),
                                    card_for_product("pie-chart-ngl", "NGL"),
                                    card_for_product("pie-chart-condensate", "Condensate")
                                ],
                                grow=True
                            )
                        ],
                        w="60%",
                        p="10px",
                        bd="1px solid dark.4",
                    ),
                    # Map Container
                    dmc.Box(
                        dcc.Graph(
                            id="map-view",
                           style={
                                "display": "flex",
                                "flexBasis": "70%",
                                "flexGrow": 0,
                                "flexShrink": 0,
                                "width": "100%",
                                "height" : "100%"
                            },
                            config={
                                "displayModeBar": "hover",  # Hide the floating toolbar
                                "responsive": True,
                            },
                        ),
                        w="20%",
                        p="10px",
                        bd="1px solid dark.4",
                    ),
                ],
                style={
                    "display": "flex",
                    "flexBasis": "70%",
                    "flexGrow": 0,
                    "flexShrink": 0,
                    "width": "100%",
                }
            ),
            dmc.Box(
                [
                    dcc.Graph(id="field-mini-timeseries", 
                        style={
                        "height": "100%",
                        "margin": "0px"
                        }
                    )
                ],
                 style={
                    "flexBasis": "30%",
                    "flexGrow": 0,
                    "flexShrink": 0,
                    "width": "100%",
                }
            ),
        ]
    )


def card_for_product(pie_chart_id, product):
    
    card = dmc.Box(
        [
            dmc.Stack(
                children=[
                    dmc.Title(product),
                    dmc.Paper(
                        children=[html.Div(id=pie_chart_id)],
                    ),    
                ],
            )
        ],
        mih = "40%",
        miw = "40%",
        p="0px",
        bd="1px solid dark.4",
    )
    
    
    return card