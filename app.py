"""
Orion Finance DeFi Protocol.

This is a Dash web application that simulates and visualizes privacy-preserving features of the Orion Finance protocol.
"""

import dash
import dash_cytoscape as cyto
from dash import html

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
                cyto.Cytoscape(
                    id="orion-graph",
                    elements=nodes + edges,
                    layout={"name": "preset"},
                    stylesheet=stylesheet,
                    style={"width": "100%", "height": "100%"},
                )
            ],
            className="content",
        ),
    ]
)
