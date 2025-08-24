import dash
from data_loader import load_data
from layout import serve_layout
from callbacks import register_callbacks
import dash_mantine_components as dmc

df, df_reserves = load_data()

theme={
    "primaryColor": "blue",
    "defaultRadius": "lg",
    "components": {
        "Card": {
            "defaultProps": {
                "shadow": "sm"
            }
        }
    }
}

app = dash.Dash(__name__)
app.title = "Norwegian Oil & Gas Dashboard"
app.layout = dmc.MantineProvider(
    forceColorScheme="dark",
    theme=theme,
    children=serve_layout(df)
)

dash.clientside_callback(
    """function(_, existingValue){ return window.innerHeight; }""",
    dash.Output("window-height", "data"),
    dash.Input("granularity-toggle", "value"),
    prevent_initial_call=False
)


register_callbacks(app, df, df_reserves)

if __name__ == "__main__":
    app.run(debug=True)
