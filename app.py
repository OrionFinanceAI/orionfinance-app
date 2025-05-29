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
from utils import N_VAULTS

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
                                html.H3("Vaults State"),
                                html.Div(id="vault-states"),
                            ],
                            className="panel",
                        ),
                        html.Div(
                            [
                                html.H3("Curators State"),
                                html.Div(id="curator-portfolios"),
                            ],
                            className="panel",
                        ),
                        html.Div(
                            [
                                html.H3("Batched Portfolio State"),
                                html.Div(id="metavault-portfolio"),
                            ],
                            className="panel",
                        ),
                        html.Div(
                            [
                                html.H3("P&L Oracle State"),
                                html.Div(id="price-oracle-state"),
                            ],
                            className="panel",
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
    vault_states = sim_state.get("vault_states", {}) if sim_state else {}
    return html.Div(
        [
            html.Div(
                [
                    html.H4(f"Vault {i + 1}"),
                    html.P(
                        [
                            "TVL: ",
                            html.Span(
                                f"${state.get('tvl', 'N/A'):.2f}" if state and isinstance(state.get('tvl'), float) else 'N/A',
                                style={"font-weight": "bold", "color": "#2a9d8f" if state else "#grey"},
                            ),
                        ]
                    ),
                ]
            )
            for i, state in enumerate(vault_states.values())
        ] +
        [
            html.Div(
                [
                    html.H4(f"Vault {i + 1}"),
                    html.P(
                        [
                            "TVL: ",
                            html.Span("N/A", style={"font-weight": "bold", "color": "#grey"}),
                        ]
                    ),
                ]
            )
            for i in range(len(vault_states), N_VAULTS)
        ]
    )


# Callback to update curator portfolios
@callback(
    Output("curator-portfolios", "children"),
    Input("update-interval", "n_intervals"),
    State("simulation-state", "data"),
)
def update_curator_portfolios(n, sim_state):
    curator_states = sim_state.get("curator_states", {}) if sim_state else {}
    return html.Div(
        [
            html.Div(
                [
                    html.H4(f"Curator {i + 1}"),
                    html.P(
                        [
                            "Portfolio Status: ",
                            html.Span(
                                "Active" if state and state.get("has_portfolio") else "No Portfolio",
                                style={
                                    "color": "#2a9d8f" if state and state.get("has_portfolio") else "#e63946",
                                    "font-weight": "bold",
                                },
                            ),
                        ]
                    ),
                ]
            )
            for i, state in enumerate(curator_states.values())
        ] +
        [
            html.Div(
                [
                    html.H4(f"Curator {i + 1}"),
                    html.P(
                        [
                            "Portfolio Status: ",
                            html.Span("N/A", style={"font-weight": "bold", "color": "#grey"}),
                        ]
                    ),
                ]
            )
            for i in range(len(curator_states), N_VAULTS)
        ]
    )


# Callback to update metavault portfolio (Now Batched Portfolio State - Pie Chart)
@callback(
    Output("metavault-portfolio", "children"),
    Input("update-interval", "n_intervals"),
    State("simulation-state", "data"),
)
def update_batched_portfolio_state(n, sim_state):
    if not sim_state or not sim_state.get("metavault_state", {}).get("final_portfolio"):
        # Show placeholder grey pie chart
        fig_placeholder_pie = go.Figure()
        fig_placeholder_pie.add_trace(
            go.Pie(
                values=[1],
                marker_colors=['#808080'], # Grey color
                hole=0.3, # Optional: make it a donut for distinction
                textinfo='none',
                hoverinfo='none'
            )
        )
        fig_placeholder_pie.update_layout(
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=20, b=20),
            annotations=[dict(text='No Data', x=0.5, y=0.5, font_size=16, showarrow=False, font_color='#aaaaaa')]
        )
        return dcc.Graph(figure=fig_placeholder_pie, style={'height': '100%', 'width': '100%'})

    metavault_state = sim_state.get("metavault_state", {})
    final_portfolio = metavault_state.get("final_portfolio")

    # Create portfolio visualization (Pie Chart)
    fig_pie = go.Figure()
    fig_pie.add_trace(
        go.Pie(
            labels=final_portfolio["labels"],
            values=final_portfolio["values"],
            name="Portfolio Weights",
            textinfo='none'
        )
    )
    fig_pie.update_layout(
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20)
    )
    return dcc.Graph(figure=fig_pie, style={'height': '100%', 'width': '100%'})


# New callback for P&L Oracle State (Histogram)
@callback(
    Output("price-oracle-state", "children"),
    Input("update-interval", "n_intervals"),
    State("simulation-state", "data"),
)
def update_price_oracle_state(n, sim_state):
    if not sim_state or not sim_state.get("worker_state", {}).get("latest_returns"):
        # Show placeholder empty grid
        fig_placeholder_hist = go.Figure()
        fig_placeholder_hist.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title="Return (%)",
            yaxis_title="Frequency",
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis=dict(showgrid=True, zeroline=False, gridcolor='#444444', color='#2a9d8f'), # Dim grid lines
            yaxis=dict(showgrid=True, zeroline=False, gridcolor='#444444', color='#2a9d8f'), # Dim grid lines
            annotations=[dict(text='No Data', x=0.5, y=0.5, xref='paper', yref='paper', font_size=16, showarrow=False, font_color='#aaaaaa')]
        )
        return dcc.Graph(figure=fig_placeholder_hist, style={'height': '100%', 'width': '100%'})

    worker_state = sim_state.get("worker_state", {})
    latest_returns = worker_state.get("latest_returns", [])

    # Create histogram of R_t values
    fig_hist = go.Figure()
    fig_hist.add_trace(
        go.Histogram(
            x=[r * 100 for r in latest_returns], # Convert to percentage
            nbinsx=40,
            name="Returns Distribution",
            marker_color='#2a9d8f'
        )
    )
    fig_hist.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title="Return (%)",
        yaxis_title="Frequency", 
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(gridcolor='#444444', color='#2a9d8f'), # Dim grid lines and match text color
        yaxis=dict(gridcolor='#444444', color='#2a9d8f')  # Dim grid lines and match text color
    )
    return dcc.Graph(figure=fig_hist, style={'height': '100%', 'width': '100%'})


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
                height: calc(100vh - 60px); /* Full viewport height minus navbar */
                position: relative;
            }
            .panels-container {
                display: flex;
                flex-wrap: wrap; /* Allow panels to wrap */
                flex: 1; /* Allow container to grow and shrink, taking available space */
                gap: 20px;
                padding: 20px;
                /* Removed overflow: hidden; to diagnose layout issues if content overflows */
                /* align-content: flex-start; /* Aligns wrapped lines to the start; useful if rows have different heights */
            }
            .panel {
                background-color: #18191a;
                border-radius: 8px;
                padding: 20px; /* Inner padding of the panel */
                box-sizing: border-box; /* Padding included in element's total width and height */
                display: flex; /* Use flex for panel content */
                flex-direction: column; /* Stack content (H3, graph div) vertically */
                overflow-y: auto; /* Allow vertical scroll within panel if its content overflows its calculated height */

                /* Default for large screens (2x2 grid): */
                flex-basis: calc(50% - 10px); /* Width: 50% of container minus half the gap */
                height: calc(50% - 10px);   /* Height: 50% of container minus half the gap */
                /* No min-height here for the 2x2 view to ensure percentage height is respected */
            }

            /* Target the direct child div that holds the graph or list content */
            .panel > .js-plotly-plot,          /* Targets the Plotly graph div directly if it's a direct child */
            .panel > div[id^="vault-states"],
            .panel > div[id^="curator-portfolios"],
            .panel > div[id^="metavault-portfolio"],
            .panel > div[id^="price-oracle-state"] {
                flex-grow: 1; /* Allows this div to take up available vertical space in the panel */
                min-height: 0; /* Crucial for flex children to shrink properly and not overflow their parent */
                /* Ensure width is also handled if direct child is not dcc.Graph which handles its own width */
                width: 100%;
            }

            /* Medium screens */
            @media (max-width: 1200px) and (min-width: 769px) {
                .panel {
                    flex-basis: calc(50% - 10px); /* Maintain two panels wide */
                    height: auto;                 /* Let content determine height */
                    min-height: 300px;            /* Ensure a decent minimum height for content */
                }
            }

            /* Small screens */
            @media (max-width: 768px) {
                .panels-container {
                    flex-direction: column; /* Stack panels vertically */
                    flex-wrap: nowrap;      /* No wrapping when in single column */
                    overflow-y: auto;       /* Allow scrolling for the entire container if stacked panels exceed viewport */
                }
                .panel {
                    flex-basis: 100%;    /* Full width for each panel */
                    height: auto;        /* Let content determine height */
                    min-height: 300px;   /* Adjust as needed for stacked view */
                    /* margin-bottom: 20px; /* Gap should handle this in flex-direction: column if supported */
                }
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
                margin-bottom: 15px; /* Add some space below the header */
            }
            h4 {
                color: #fff;
                margin: 10px 0;
                font-size: 1em;
            }
            /* Graph container styles */
            .js-plotly-plot {
                width: 100% !important;
                height: 100% !important;
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
