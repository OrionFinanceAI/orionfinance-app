"""
Orion Finance DeFi Protocol.

This is a Dash web application that simulates and visualizes privacy-preserving features of the Orion Finance protocol.
"""

import dash
import plotly.graph_objects as go
from dash import dcc, html

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

fig = go.Figure()
fig.add_trace(go.Scatter(x=[0, 1, 2], y=[0, 1, 0], mode="lines+markers"))
fig.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))

app.layout = html.Div(
    [
        html.Nav(
            [
                html.Img(
                    src="/assets/OF_lockup_white.png",
                    className="logo",
                    style={"height": "40px"},
                ),
                html.A(
                    html.Img(src="/assets/github.png", style={"height": "40px"}),
                    href="https://github.com/OrionFinanceAI/orionfinance-app",
                    target="_blank",
                ),
            ],
            className="navbar",
        ),
        html.Div(
            [
                dcc.Graph(figure=fig, className="main-plot"),
            ],
            className="content",
        ),
    ]
)
