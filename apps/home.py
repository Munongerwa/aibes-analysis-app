import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc

layout = html.Div([
    html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1([
                        html.Span("Welcome to ", style={"color": "#ffffff"}),
                        html.Span("AIBES ANALYSIS", style={"color": "#a1d2f5"})
                    ], className="display-4 fw-bold mb-4"),
                    html.P([
                        "Your comprehensive solution for AIBES data analysis, ",
                        "land bank management, and reporting."
                    ], className="lead  mb-4", style={"color": "#ffffff", "fontSize": "1.25rem"}),
                    dbc.Button([
                        "Get Started",
                        html.I(className="fas fa-arrow-right ms-2")
                    ], 
                    href="/apps/dashboard", 
                    size="lg", 
                    className="me-3 mb-3"),
                    dbc.Button([
                        "Connect Database",
                        html.I(className="fas fa-database ms-2")
                    ], 
                    href="/apps/db_connection", 
                    size="lg", 
                    color="light",
                    className="mb-3",
                    style={"color": "#333"})
                ], md=8),
                dbc.Col([
                    html.Div([
                        html.I(className="fas fa-chart-line", style={
                            "fontSize": "10rem", 
                            "color": "#ffffff", 
                            "opacity": "0.3"
                        })
                    ], className="text-end")
                ], md=4, className="d-none d-md-block")
            ], className="py-5 align-items-center")
        ], fluid=True)
    ], style={
        "backgroundImage": "url('/assets/backimage.png')",
        "backgroundSize": "cover",
        "backgroundPosition": "center center",
        "backgroundRepeat": "no-repeat",
        "backgroundAttachment": "fixed",
        "minHeight": "100vh",
        "display": "flex",
        "alignItems": "center",
        "width": "100%",
        "margin": "0",
        "padding": "0"
    }),
], style={
    "margin": "0",
    "padding": "0",
    "width": "100%",
    "height": "100%",
    "overflowX": "hidden"
})