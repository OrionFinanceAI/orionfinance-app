"""
Orion Finance DeFi Protocol.

This is a Dash web application that simulates and visualizes privacy-preserving features of the Orion Finance protocol.
"""

import logging

import dash
import dash_cytoscape as cyto
import plotly.graph_objects as go
from dash import Input, Output, State, callback, dcc, html
from dash.exceptions import PreventUpdate

from main import build_graph
from simulator_integration import simulator_state

# Configure logging
logger = logging.getLogger("OrionSimulation")

app = dash.Dash(__name__, title="Orion Finance", suppress_callback_exceptions=True)
server = app.server

lp_x_grid = [100, 400, 700]
lp_y = 0
vault_y = 100

curators = ["👩‍💼", "🧑‍💼", "👨‍💼"]

strategy_x_grid = [200, 400, 600]
strategy_y = 500

nodes = [
    *[
        {
            "data": {"id": f"LP{i + 1}", "label": "👥"},
            "position": {"x": x, "y": lp_y},
            "classes": "lp",
        }
        for i, x in enumerate(lp_x_grid)
    ],
    *[
        {
            "data": {"id": f"Vault{i + 1}", "label": "🏦"},
            "position": {"x": x, "y": vault_y},
            "classes": "vault",
        }
        for i, x in enumerate(lp_x_grid)
    ],
    *[
        {
            "data": {"id": f"Curator{i + 1}", "label": curators[i]},
            "position": {"x": x - 120, "y": vault_y},
            "classes": "curator",
        }
        for i, x in enumerate(lp_x_grid)
    ],
    {
        "data": {"id": "PendingPool", "label": "Orion Pending Pool"},
        "position": {"x": 400, "y": 200},
        "classes": "core",
    },
    {
        "data": {"id": "OrionWorker", "label": "Orion Worker"},
        "position": {"x": 700, "y": 200},
        "classes": "person",
    },
    {
        "data": {"id": "WeightManager", "label": "Weight Manager"},
        "position": {"x": 400, "y": 300},
        "classes": "dashed",
    },
    {
        "data": {"id": "YearnV3", "label": "Yearn V3 Vault"},
        "position": {"x": 400, "y": 400},
        "classes": "core",
    },
    *[
        {
            "data": {"id": f"Strategy{i + 1}", "label": f"Strategy {i + 1}"},
            "position": {"x": x, "y": strategy_y},
            "classes": "strategy",
        }
        for i, x in enumerate(strategy_x_grid)
    ],
]

edges = [
    *[
        {
            "data": {"source": f"LP{i + 1}", "target": f"Vault{i + 1}"},
            "classes": "dashed",
        }
        for i in range(len(lp_x_grid))
    ],
    {"data": {"source": "Curator1", "target": "Vault1"}},
    {"data": {"source": "Curator2", "target": "Vault2"}},
    {"data": {"source": "Curator3", "target": "Vault3"}},
    {"data": {"source": "Vault1", "target": "PendingPool"}},
    {"data": {"source": "Vault2", "target": "PendingPool"}},
    {"data": {"source": "Vault3", "target": "PendingPool"}},
    {"data": {"source": "OrionWorker", "target": "PendingPool"}},
    {"data": {"source": "PendingPool", "target": "WeightManager"}},
    {"data": {"source": "WeightManager", "target": "YearnV3"}},
    {"data": {"source": "YearnV3", "target": "Strategy1"}},
    {"data": {"source": "YearnV3", "target": "Strategy2"}},
    {"data": {"source": "YearnV3", "target": "Strategy3"}},
]

# Cytoscape stylesheet

square_size = "50px"

stylesheet = [
    {
        "selector": "node",
        "style": {
            "content": "data(label)",
            "text-valign": "center",
            "text-halign": "center",
            "background-color": "#333",
            "color": "#fff",
            "width": "label",
            "height": "label",
            "padding": "10px",
            "shape": "round-rectangle",
            "font-size": "14px",
            "font-family": "Inter, sans-serif",
        },
    },
    {"selector": ".core", "style": {"background-color": "#e63946"}},
    {
        "selector": ".vault",
        "style": {
            "background-color": "#f1faee",
            "color": "#000",
            "shape": "round-rectangle",
            "height": square_size,
            "width": square_size,
            "font-size": square_size,
        },
    },
    {"selector": ".strategy", "style": {"background-color": "#2a9d8f"}},
    {"selector": ".person", "style": {"background-color": "#1d3557"}},
    {
        "selector": ".curator",
        "style": {
            "background-color": "#e63946",
            "color": "#fff",
            "shape": "round-rectangle",
            "height": square_size,
            "width": square_size,
            "font-size": square_size,
        },
    },
    {
        "selector": ".lp",
        "style": {
            "background-color": "#1d3557",
            "color": "#000",
            "shape": "round-rectangle",
            "height": square_size,
            "width": square_size,
            "font-size": square_size,
        },
    },
    {
        "selector": ".dashed",
        "style": {
            "border-style": "dashed",
            "border-width": "2px",
            "border-color": "#aaa",
        },
    },
    {
        "selector": "edge",
        "style": {
            "line-color": "#aaa",
            "width": 2,
            "target-arrow-color": "#aaa",
            "target-arrow-shape": "triangle",
            "arrow-scale": 1,
            "curve-style": "bezier",
        },
    },
]

app.layout = html.Div([
    html.Nav([
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
    ], className="navbar"),
    
    html.Div([
        # Left panel - Graph visualization
        html.Div([
            cyto.Cytoscape(
                id="orion-graph",
                elements=nodes + edges,
                layout={"name": "preset"},
                stylesheet=stylesheet,
                style={"width": "100%", "height": "100%"},
            )
        ], className="graph-panel"),
        
        # Right panel - State information
        html.Div([
            html.H3("Vault States"),
            html.Div(id="vault-states"),
            
            html.H3("Worker Performance"),
            html.Div(id="worker-performance"),
            
            html.H3("MetaVault Portfolio"),
            html.Div(id="metavault-portfolio"),
            
            html.H3("Curator Portfolios"),
            html.Div(id="curator-portfolios"),
            
            # Control buttons
            html.Div([
                html.Button("Start Simulation", id="start-sim", n_clicks=0),
                html.Button("Stop Simulation", id="stop-sim", n_clicks=0),
            ], className="control-buttons"),
            
            # Hidden div for storing simulation state
            dcc.Store(id="simulation-state"),
            dcc.Interval(id="update-interval", interval=1000, disabled=True),
        ], className="state-panel"),
    ], className="main-content"),
])

# Callback to update vault states
@callback(
    Output("vault-states", "children"),
    Input("update-interval", "n_intervals"),
    State("simulation-state", "data")
)
def update_vault_states(n, sim_state):
    if not sim_state:
        raise PreventUpdate
    
    vault_states = sim_state.get("vault_states", {})
    return html.Div([
        html.Div([
            html.H4(f"Vault {i+1}"),
            html.P([
                "Idle TVL: ",
                html.Span(
                    f"{state.get('idle_tvl', 0):.2f}",
                    style={"font-weight": "bold", "color": "#2a9d8f"}
                )
            ])
        ]) for i, state in enumerate(vault_states.values())
    ])

# Callback to update worker performance
@callback(
    Output("worker-performance", "children"),
    Input("update-interval", "n_intervals"),
    State("simulation-state", "data")
)
def update_worker_performance(n, sim_state):
    if not sim_state:
        raise PreventUpdate
    
    worker_state = sim_state.get("worker_state", {})
    portfolios_matrix = worker_state.get("portfolios_matrix")
    
    if portfolios_matrix is None:
        return html.P("No active portfolios")
    
    # Create performance visualization
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=list(range(len(portfolios_matrix.columns))),
        y=portfolios_matrix.sum(axis=0),
        name="Total TVL per Vault"
    ))
    
    return dcc.Graph(figure=fig)

# Callback to update metavault portfolio
@callback(
    Output("metavault-portfolio", "children"),
    Input("update-interval", "n_intervals"),
    State("simulation-state", "data")
)
def update_metavault_portfolio(n, sim_state):
    if not sim_state:
        raise PreventUpdate
    
    metavault_state = sim_state.get("metavault_state", {})
    final_portfolio = metavault_state.get("final_portfolio")
    
    if final_portfolio is None:
        return html.P("No final portfolio available")
    
    # Create portfolio visualization
    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=final_portfolio.index,
        values=final_portfolio.values,
        name="Portfolio Weights"
    ))
    
    return dcc.Graph(figure=fig)

# Callback to update curator portfolios
@callback(
    Output("curator-portfolios", "children"),
    Input("update-interval", "n_intervals"),
    State("simulation-state", "data")
)
def update_curator_portfolios(n, sim_state):
    if not sim_state:
        raise PreventUpdate
    
    curator_states = sim_state.get("curator_states", {})
    
    return html.Div([
        html.Div([
            html.H4(f"Curator {i+1}"),
            html.P(f"Portfolio Size: {len(state.get('portfolio', {}))} assets")
        ]) for i, state in enumerate(curator_states.values())
    ])

# Callback to update simulation state
@callback(
    Output("simulation-state", "data"),
    Input("update-interval", "n_intervals")
)
def update_simulation_state(n):
    return simulator_state.get_next_state()

# Callback to control simulation
@callback(
    Output("update-interval", "disabled"),
    Input("start-sim", "n_clicks"),
    Input("stop-sim", "n_clicks"),
    State("update-interval", "disabled")
)
def control_simulation(start_clicks, stop_clicks, current_state):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "start-sim":
        # Start the simulation
        graph = build_graph()
        simulator_state.start_simulation(graph)
        return False
    elif button_id == "stop-sim":
        # Stop the simulation
        simulator_state.stop_simulation()
        return True
    
    return current_state

# Add CSS styles
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .main-content {
                display: flex;
                height: calc(100vh - 60px);
            }
            .graph-panel {
                flex: 2;
                padding: 20px;
            }
            .state-panel {
                flex: 1;
                padding: 20px;
                background-color: #f8f9fa;
                overflow-y: auto;
            }
            .control-buttons {
                margin-top: 20px;
                display: flex;
                gap: 10px;
            }
            .navbar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 20px;
                background-color: #1d3557;
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
'''

if __name__ == "__main__":
    app.run(debug=True)
