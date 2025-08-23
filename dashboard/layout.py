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
                        dmc.Center(
                            children=[
                                dmc.Button("Selections", id="drawer-button", size="m")
                            ],
                        ),
                        w="20%",
                        mah="70%",
                        mih="70%",
                        p="10px",
                        bd="1px solid dark.4",
                    ),
                    dmc.Box(
                        [
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
                                        value=None,
                                        data=[
                                            {"label": f, "value": f}
                                            for f in sorted(df["field"].unique())
                                        ],
                                        style={"marginBottom": "10px"},
                                        size="sm",
                                        searchable=True,
                                        # nothingFound="No field found",
                                        variant="filled",
                                    ),
                                    # Select what products to look at
                                    dmc.Select(
                                        label="Product",
                                        id="product-filter",
                                        data=[
                                            {"label": p, "value": p}
                                            for p in df["product"].unique()
                                        ],
                                        value="Oil",
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
                            dmc.Paper(
                                children=[html.Div(id="field-pie-chart")],
                                style={
                                    "height": "40%",
                                    "marginBottom": "10px",
                                    "padding": 10,
                                },
                            ),
                        ],
                        mih="70%",
                        mah="70%",
                        w="60%",
                        p="10px",
                        bd="1px solid dark.4",
                    ),
                    # Map Container
                    dmc.Box(
                        dcc.Graph(
                            id="map-view",
                            style={
                                "height": "70vh",
                                "margin": "0px",
                                "backgroundColor": "#1e1e1e00",  # dark background
                                "border": "1px solid #444",
                                "borderRadius": "5px",
                                "padding": "0px",
                            },
                            config={
                                "displayModeBar": "hover",  # Hide the floating toolbar
                                "responsive": True,
                            },
                        ),
                        w="20%",
                        h="70%",
                        p="10px",
                        bd="1px solid dark.4",
                    ),
                ],
                style={"display": "flex", "height": "70%", "width": "100%"},
            ),
            html.Div(
                [
                    dmc.Box(
                        [html.Div(id="field-mini-timeseries")],
                        w="100%",
                        h="30%",
                        p="10px",
                        bd="1px solid dark.4",
                    )
                ],
                style={
                    "display": "flex",
                    "height": "30%",
                    "width": "100%",
                },
            ),
        ]
    )
