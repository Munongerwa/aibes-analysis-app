# app.py
import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
from flask import session, send_from_directory
import datetime
import uuid
import os
import sqlite3
from sqlalchemy import create_engine
from apps import home, dashboard, db_connection, land_bank_analysis, project_analysis, sales_analysis, reports_view, settings

# Add these imports at the top
import os
import pymysql
pymysql.install_as_MySQLdb()

# Update the server configuration for production
app = dash.Dash(__name__, 
                external_stylesheets=[
                    dbc.themes.BOOTSTRAP,
                    "https://use.fontawesome.com/releases/v6.0.0/css/all.css"
                ],
                suppress_callback_exceptions=True,
                server=True)

# Secure secret key
app.server.secret_key = os.environ.get('SECRET_KEY', 'your-default-secret-key-change-in-production')

# Serve static files with better caching
@app.server.route('/assets/<path:filename>')
def serve_assets(filename):
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
    return send_from_directory(assets_dir, filename, 
                             cache_timeout=0 if app.config.get('DEBUG', False) else 31536000)

# Update the display_page callback to use the improved connection check
@app.callback(
    [Output('page-content', 'children'),
     Output('navbar-connection-status', 'children')],
    [Input('url', 'pathname'),
     Input('confirm-logout-btn', 'n_clicks')],
    prevent_initial_call=False
)
def display_page(pathname, logout_clicks):
    ctx = dash.callback_context
    
    # Handle logout
    if ctx.triggered and ctx.triggered[0]['prop_id'] == 'confirm-logout-btn.n_clicks':
        session.pop('db_connection_string', None)
        session.pop('user_id', None)
        
        logout_success_page = html.Div([
            dbc.Container([
                dbc.Alert([
                    html.I(className="fas fa-check-circle me-2"),
                    "You have been logged out successfully and disconnected from the database!"
                ], color="success", className="mt-5 text-center"),
                dbc.Row([
                    dbc.Col([
                        dbc.Button([
                            html.I(className="fas fa-sign-in-alt me-2"),
                            "Reconnect to Database"
                        ], href="/apps/db_connection", color="primary", className="me-2")
                    ], width="auto"),
                    dbc.Col([
                        dbc.Button([
                            html.I(className="fas fa-home me-2"),
                            "Go to Home"
                        ], href="/", color="secondary")
                    ], width="auto")
                ], className="justify-content-center mt-3")
            ], className="text-center")
        ])
        return [logout_success_page, get_connection_status_component()]
    
    # Handle direct logout route
    if pathname == '/apps/logout':
        session.pop('db_connection_string', None)
        session.pop('user_id', None)
        return [html.Div([
            dbc.Container([
                dbc.Alert([
                    html.I(className="fas fa-check-circle me-2"),
                    "You have been logged out successfully and disconnected from the database!"
                ], color="success", className="mt-5 text-center"),
                dbc.Button([
                    html.I(className="fas fa-sign-in-alt me-2"),
                    "Login Again"
                ], href="/apps/db_connection", color="primary", className="mt-3")
            ], className="text-center")
        ]), get_connection_status_component()]
    
    # Protected pages check
    protected_pages = [
        '/apps/dashboard', 
        '/apps/settings', 
        '/apps/land_bank_analysis', 
        '/apps/project_analysis', 
        '/apps/sales_analysis', 
        '/apps/reports_view'
    ]
    
    if pathname in protected_pages:
        # Use the improved connection check
        engine = get_user_db_connection()
        if not engine:
            error_page = html.Div([
                dbc.Container([
                    dbc.Alert([
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        "Database connection required! Please connect to database first."
                    ], color="warning", className="mt-5 text-center"),
                    dbc.Button([
                        html.I(className="fas fa-database me-2"),
                        "Go to Connection Page"
                    ], href="/apps/db_connection", color="primary", className="mt-3")
                ], className="text-center")
            ])
            return [error_page, get_connection_status_component()]
    
    # Already connected check for db_connection page
    if pathname == '/apps/db_connection':
        engine = get_user_db_connection()
        if engine:
            try:
                with engine.connect() as connection:
                    result = connection.execute("SELECT 1")
                    result.fetchone()
                already_connected_page = html.Div([
                    dbc.Container([
                        dbc.Alert([
                            html.I(className="fas fa-check-circle me-2"),
                            "You are already connected to the database!"
                        ], color="success", className="mt-5 text-center"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-chart-line me-2"),
                                    "Go to Dashboard"
                                ], href="/apps/dashboard", color="primary", className="me-2")
                            ], width="auto"),
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-home me-2"),
                                    "Go to Home"
                                ], href="/", color="secondary")
                            ], width="auto")
                        ], className="justify-content-center mt-3")
                    ], className="text-center")
                ])
                return [already_connected_page, get_connection_status_component()]
            except:
                # Connection is broken, allow reconnection
                pass
    
    # Page routing
    connection_status = get_connection_status_component()
    
    if pathname == '/':
        return [home.layout, connection_status]
    elif pathname == '/apps/db_connection':
        return [db_connection.layout, connection_status]
    elif pathname == '/apps/dashboard':
        return [dashboard.layout, connection_status]
    elif pathname == '/apps/land_bank_analysis':
        return [land_bank_analysis.layout, connection_status]
    elif pathname == '/apps/project_analysis':
        return [project_analysis.layout, connection_status]
    elif pathname == '/apps/sales_analysis':
        return [sales_analysis.layout, connection_status]
    elif pathname == '/apps/reports_view':
        return [reports_view.layout, connection_status]
    elif pathname == '/apps/settings':
        return [settings.layout, connection_status]
    else:
        not_found = dbc.Container([
            html.H1("404 - Page not found"),
            html.P("The requested page does not exist."),
            dbc.Button("Go Home", href="/", color="primary", className="mt-3")
        ], className="text-center mt-5")
        return [not_found, connection_status]

# Improved database connection function
def get_user_db_connection():
    if 'db_connection_string' in session and session['db_connection_string']:
        try:
            engine = create_engine(
                session['db_connection_string'],
                pool_timeout=30,
                pool_recycle=3600,
                pool_pre_ping=True,
                echo=False
            )
            return engine
        except Exception as e:
            print(f"Database connection error: {e}")
            session.pop('db_connection_string', None)  # Remove invalid connection
            return None
    return None

# Enhanced connection status component
def get_connection_status_component():
    if 'db_connection_string' in session and session['db_connection_string']:
        try:
            engine = create_engine(
                session['db_connection_string'],
                pool_timeout=10,
                pool_pre_ping=True
            )
            
            with engine.connect() as connection:
                result = connection.execute("SELECT 1")
                result.fetchone()
            
            # Extract database info
            try:
                from sqlalchemy.engine.url import make_url
                url = make_url(session['db_connection_string'])
                db_label = url.database or url.host
                host_info = url.host
            except:
                db_label = "Connected DB"
                host_info = "Unknown"
            
            return html.Div([
                html.Span([
                    html.I(className="fas fa-check-circle text-success me-1"),
                    f"Connected: {db_label}"
                ], className="text-success small", title=f"Connected to {host_info}")
            ], className="d-flex align-items-center")
        except Exception as e:
            print(f"Connection status check error: {e}")
            return html.Div([
                html.Span([
                    html.I(className="fas fa-exclamation-triangle text-warning me-1"),
                    "Connection Lost"
                ], className="text-warning small", title="Click to reconnect")
            ], className="d-flex align-items-center")
    else:
        return html.Div([
            html.Span([
                html.I(className="fas fa-times-circle text-danger me-1"),
                "Not Connected"
            ], className="text-danger small")
        ], className="d-flex align-items-center")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    if debug:
        app.run(host='0.0.0.0', port=port, debug=True)
    else:
        app.run(host='0.0.0.0', port=port, debug=False)