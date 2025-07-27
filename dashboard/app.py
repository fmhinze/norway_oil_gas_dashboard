import dash
from data_loader import load_data
from layout import serve_layout
from callbacks import register_callbacks

df = load_data()

app = dash.Dash(__name__)
app.title = "Norwegian Oil & Gas Dashboard"
app.layout = serve_layout(df)

register_callbacks(app, df)

if __name__ == "__main__":
    app.run_server(debug=False)
