# apps/home.py - Simple version
import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc

layout = html.Div([
    # Hero Section with inline styles for background
    html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1([
                        html.Span("Welcome to ", style={"color": "#ffffff"}),
                        html.Span("AIBES ANALYSIS", style={"color": "#007bff"})
                    ], className="display-4 fw-bold mb-4"),
                    html.P([
                        "Your comprehensive solution for real estate data analysis, ",
                        "land bank management, and business intelligence reporting."
                    ], className="lead mb-4", style={"color": "rgba(255, 255, 255, 0.9)"}),
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
                    className="mb-3")
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
        "backgroundPosition": "center",
        "backgroundRepeat": "no-repeat",
        "minHeight": "700px",
        "display": "flex",
        "alignItems": "center",
        "position": "relative",
        "backgroundColor": "rgba(0, 0, 0, 0.6)",
        "backgroundBlendMode": "overlay"
    }),
    
    # Features Section
    dbc.Container([
        html.H2("Key Features", className="text-center my-5"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-map-marked-alt fa-2x text-primary mb-3")
                        ], className="text-center"),
                        html.H5("Land Bank Analysis", className="card-title text-center"),
                        html.P([
                            "Comprehensive tracking and analysis of land bank properties ",
                            "with detailed metrics and visualizations."
                        ], className="card-text text-center")
                    ])
                ], className="h-100 shadow-sm")
            ], md=4, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-project-diagram fa-2x text-success mb-3")
                        ], className="text-center"),
                        html.H5("Project Management", className="card-title text-center"),
                        html.P([
                            "Monitor project progress, timelines, and performance ",
                            "across all development initiatives."
                        ], className="card-text text-center")
                    ])
                ], className="h-100 shadow-sm")
            ], md=4, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-chart-bar fa-2x text-info mb-3")
                        ], className="text-center"),
                        html.H5("Sales Analytics", className="card-title text-center"),
                        html.P([
                            "Real-time sales tracking, forecasting, and performance ",
                            "analytics for informed decision making."
                        ], className="card-text text-center")
                    ])
                ], className="h-100 shadow-sm")
            ], md=4, className="mb-4")
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-file-pdf fa-2x text-danger mb-3")
                        ], className="text-center"),
                        html.H5("Automated Reports", className="card-title text-center"),
                        html.P([
                            "Generate professional reports with customizable templates ",
                            "and automated scheduling capabilities."
                        ], className="card-text text-center")
                    ])
                ], className="h-100 shadow-sm")
            ], md=4, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-database fa-2x text-warning mb-3")
                        ], className="text-center"),
                        html.H5("Multi-Database Support", className="card-title text-center"),
                        html.P([
                            "Connect to various database systems including MySQL, ",
                            "PostgreSQL, and cloud databases."
                        ], className="card-text text-center")
                    ])
                ], className="h-100 shadow-sm")
            ], md=4, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-mobile-alt fa-2x text-purple mb-3")
                        ], className="text-center"),
                        html.H5("Mobile Ready", className="card-title text-center"),
                        html.P([
                            "Fully responsive design that works seamlessly ",
                            "on desktops, tablets, and mobile devices."
                        ], className="card-text text-center")
                    ])
                ], className="h-100 shadow-sm")
            ], md=4, className="mb-4")
        ])
    ], className="my-5"),
    

    

], className="bg-light")