from dash import html, dcc
import pandas as pd

def serve_layout(df):
    return html.Div([
        

        html.Div([  # Main horizontal container: sidebar + main content
            html.Div([  # Sidebar
                html.H2("Norwegian Oil & Gas", style={"margin": "10px 0"}),
                html.Label("Field"),
                dcc.Dropdown(
                    options=[{"label": f, "value": f} for f in sorted(df["field"].unique())],
                    id="field-filter",
                    placeholder="Select a field (optional)",
                    value=None,
                    style={"marginBottom": "10px"}
                ),
                html.Label("Product"),
                dcc.Dropdown(
                    options=[{"label": p, "value": p} for p in df["product"].unique()],
                    value="Oil",
                    id="product-filter",
                    style={"marginBottom": "10px"}
                ),
                html.Label("Gross Comparison"),
                dcc.Checklist(
                    options=[{"label": " Show Gross & Waste", "value": "show"}],
                    value=[],  # default is off
                    id="show-gross-toggle",
                    style={"marginBottom": "10px"}
                ),
                html.Label("Display"),
                dcc.RadioItems(
                    options=[
                        {"label": "Monthly", "value": "monthly"},
                        {"label": "Annual", "value": "annual"},
                    ],
                    value="monthly",
                    id="granularity-toggle",
                    style={"marginBottom": "10px"}
                ),
                html.Label("Date Range"),
                dcc.DatePickerRange(
                    id="date-filter",
                    start_date=df["date"].min(),
                    end_date=df["date"].max(),
                    display_format="YYYY-MM",
                    style={"marginBottom": "10px"}
                ),
            ], style={
                "width": "20%",
                "padding": "0px",
                "height": "70vh",
                "overflowY": "auto",
                "boxSizing": "border-box",
                "borderRight": "1px solid #ccc"
            }),

            html.Div([  # Map + placeholder panel
                html.Div([
                    dcc.Graph(id="map-view", style={
                        "height": "70vh",
                        "margin": "0px"
                    }),
                ], style={
                    "width": "100%",
                    "boxSizing": "border-box"
                }),

                html.Div([
                    html.Div("← Future visualisations here", style={
                        "padding": "10px"
                    })
                ], style={
                    "display": "none"  # placeholder for future content
                })

            ], style={
                "width": "80%",
                "padding": "0px",
                "boxSizing": "border-box"
            })

        ], style={
            "display": "flex",
            "height": "70vh",
            "width": "100%"
        }),

        html.Div([
            dcc.Graph(id="time-series", style={
                "height": "30vh",
                "margin": "0px"
            })
        ], style={
            "width": "100%"
        })

    ], style={
        "height": "100vh",
        "boxSizing": "border-box",
        "padding": "0 10px"
    })
