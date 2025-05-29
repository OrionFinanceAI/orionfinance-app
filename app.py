"""
Orion Finance DeFi Protocol.

This is a Dash web application that simulates and visualizes privacy-preserving features of the Orion Finance protocol.
"""

import logging

import dash
import plotly.graph_objects as go
from dash import Input, Output, State, callback, dcc, html
from dash.exceptions import PreventUpdate

from main import build_graph
from simulator_integration import simulator_state

# Configure logging
logger = logging.getLogger("OrionSimulation")

app = dash.Dash(__name__, title="Orion Finance", suppress_callback_exceptions=True)
server = app.server

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
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3("Vault States"),
                                html.Div(id="vault-states"),
                                html.H3("Curator Portfolios"),
                                html.Div(id="curator-portfolios"),
                            ],
                            className="left-panel",
                        ),
                        html.Div(
                            [
                                html.H3("MetaVault Portfolio"),
                                html.Div(id="metavault-portfolio"),
                            ],
                            className="center-panel",
                        ),
                        html.Div(
                            [
                                html.H3("Worker Performance"),
                                html.Div(id="worker-performance"),
                            ],
                            className="right-panel",
                        ),
                    ],
                    className="panels-container",
                ),
                html.Div(
                    [
                        html.Button("Start Simulation", id="start-sim", n_clicks=0),
                    ],
                    className="control-buttons",
                ),
                dcc.Store(id="simulation-state"),
                dcc.Interval(id="update-interval", interval=1000, disabled=True),
            ],
            className="main-content",
        ),
    ]
)


# Callback to update vault states
@callback(
    Output("vault-states", "children"),
    Input("update-interval", "n_intervals"),
    State("simulation-state", "data"),
)
def update_vault_states(n, sim_state):
    if not sim_state:
        raise PreventUpdate

    vault_states = sim_state.get("vault_states", {})
    return html.Div(
        [
            html.Div(
                [
                    html.H4(f"Vault {i + 1}"),
                    html.P(
                        [
                            "Idle TVL: ",
                            html.Span(
                                f"{state.get('idle_tvl', 0):.2f}",
                                style={"font-weight": "bold", "color": "#2a9d8f"},
                            ),
                        ]
                    ),
                ]
            )
            for i, state in enumerate(vault_states.values())
        ]
    )


# Callback to update worker performance
@callback(
    Output("worker-performance", "children"),
    Input("update-interval", "n_intervals"),
    State("simulation-state", "data"),
)
def update_worker_performance(n, sim_state):
    if not sim_state:
        raise PreventUpdate

    worker_state = sim_state.get("worker_state", {})
    portfolios_matrix = worker_state.get("portfolios_matrix")

    if not portfolios_matrix:
        return html.P("No active portfolios")

    # Create performance visualization
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=portfolios_matrix["columns"],
            y=[sum(col) for col in zip(*portfolios_matrix["data"])],
            name="Total TVL per Vault",
        )
    )

    return dcc.Graph(figure=fig)


# Callback to update metavault portfolio
@callback(
    Output("metavault-portfolio", "children"),
    Input("update-interval", "n_intervals"),
    State("simulation-state", "data"),
)
def update_metavault_portfolio(n, sim_state):
    if not sim_state:
        raise PreventUpdate

    metavault_state = sim_state.get("metavault_state", {})
    final_portfolio = metavault_state.get("final_portfolio")

    if not final_portfolio:
        return html.P("No final portfolio available")

    # Create portfolio visualization
    fig = go.Figure()
    fig.add_trace(
        go.Pie(
            labels=final_portfolio["labels"],
            values=final_portfolio["values"],
            name="Portfolio Weights",
        )
    )
    fig.update_layout(showlegend=False)

    return dcc.Graph(figure=fig)


# Callback to update curator portfolios
@callback(
    Output("curator-portfolios", "children"),
    Input("update-interval", "n_intervals"),
    State("simulation-state", "data"),
)
def update_curator_portfolios(n, sim_state):
    if not sim_state:
        raise PreventUpdate

    curator_states = sim_state.get("curator_states", {})

    return html.Div(
        [
            html.Div(
                [
                    html.H4(f"Curator {i + 1}"),
                    html.P(
                        [
                            "Portfolio Status: ",
                            html.Span(
                                "Active"
                                if state.get("has_portfolio")
                                else "No Portfolio",
                                style={
                                    "color": "#2a9d8f"
                                    if state.get("has_portfolio")
                                    else "#e63946",
                                    "font-weight": "bold",
                                },
                            ),
                        ]
                    ),
                ]
            )
            for i, state in enumerate(curator_states.values())
        ]
    )


# Callback to update simulation state
@callback(Output("simulation-state", "data"), Input("update-interval", "n_intervals"))
def update_simulation_state(n):
    return simulator_state.get_next_state()


# Callback to control simulation
@callback(
    Output("update-interval", "disabled"),
    Input("start-sim", "n_clicks"),
    State("update-interval", "disabled"),
)
def control_simulation(start_clicks, current_state):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "start-sim":
        # Start the simulation
        graph = build_graph()
        simulator_state.start_simulation(graph)
        return False

    return current_state


# Add CSS styles
app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                margin: 0;
                padding: 0;
                font-family: Inter, sans-serif;
                background-color: #121212;
                color: #fff;
            }
            .main-content {
                display: flex;
                flex-direction: column;
                height: calc(100vh - 60px);
                position: relative;
            }
            .panels-container {
                display: flex;
                flex: 1;
                gap: 20px;
                padding: 20px;
                overflow: hidden;
            }
            .left-panel, .center-panel, .right-panel {
                background-color: #18191a;
                border-radius: 8px;
                padding: 20px;
                overflow-y: auto;
                flex: 1;
            }
            .control-buttons {
                position: fixed;
                bottom: 20px;
                left: 20px;
                z-index: 1000;
            }
            .control-buttons button {
                background-color: #2a9d8f;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                transition: background-color 0.3s;
            }
            .control-buttons button:hover {
                background-color: #238b7f;
            }
            .navbar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 20px;
                background-color: #18191a;
                height: 60px;
            }
            .logo {
                height: 40px !important;
                width: auto;
                object-fit: contain;
            }
            .navbar img {
                height: 40px !important;
                width: auto;
                object-fit: contain;
            }
            h3 {
                margin-top: 0;
                color: #fff;
                font-size: 1.2em;
                border-bottom: 1px solid #2a9d8f;
                padding-bottom: 10px;
            }
            h4 {
                color: #fff;
                margin: 10px 0;
            }
            /* Graph container styles */
            .js-plotly-plot {
                width: 100% !important;
                height: 100% !important;
            }
            /* Responsive design */
            @media (max-width: 1200px) {
                .panels-container {
                    flex-direction: column;
                }
                .left-panel, .center-panel, .right-panel {
                    width: 100%;
                    margin-bottom: 20px;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)
