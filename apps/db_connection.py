import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from flask import session
import os
import urllib.parse

# Add PyMySQL support
import pymysql
pymysql.install_as_MySQLdb()

layout = html.Div([
    dcc.Location(id="db-connection-url", refresh=True),  
    
    # Background image 
    html.Div(
        style={
            'position': 'fixed',
            'top': 0,
            'left': 0,
            'width': '100%',
            'height': '100%',
            'backgroundImage': 'url("/assets/backimage.png")',
            'backgroundSize': 'cover',
            'backgroundPosition': 'center',
            'backgroundRepeat': 'no-repeat',
            'zIndex': '-1'
        }
    ),
    
    # Content container with responsive design
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.H4([
                            html.I(className="fas fa-database me-2"),
                            "Database Connection"
                        ], className="text-center mb-0"),
                        className="bg-primary text-white"
                    ),
                    dbc.CardBody([
                        # Connection Type Selection
                        dbc.Row([
                            dbc.Col([
                                dbc.Label([
                                    html.I(className="fas fa-cog me-2"),
                                    "Connection Type"
                                ], className="text-white mb-2"),
                                dcc.Dropdown(
                                    id="connection-type-dropdown",
                                    options=[
                                        {"label": "Local MySQL Workbench", "value": "local"},
                                        {"label": "Online MySQL Database", "value": "online"},
                                        {"label": "Custom Connection String", "value": "custom"}
                                    ],
                                    value="local",
                                    className="mb-3"
                                )
                            ], width=12)
                        ]),
                        
                        # SSL Options for online databases
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label([
                                        html.I(className="fas fa-shield-alt me-2"),
                                        "SSL Mode"
                                    ], className="text-white mb-2"),
                                    dcc.Dropdown(
                                        id="ssl-mode-dropdown",
                                        options=[
                                            {"label": "Required", "value": "REQUIRED"},
                                            {"label": "Preferred", "value": "PREFERRED"},
                                            {"label": "Disabled", "value": "DISABLED"}
                                        ],
                                        value="PREFERRED",
                                        className="mb-3"
                                    ),
                                ], width=12, md=6),
                                
                                dbc.Col([
                                    dbc.Label([
                                        html.I(className="fas fa-key me-2"),
                                        "SSL Certificate Path (Optional)"
                                    ], className="text-white mb-2"),
                                    dbc.Input(
                                        type="text", 
                                        id="ssl-cert-path", 
                                        placeholder="Path to SSL certificate file",
                                        className="form-control mb-3"
                                    ),
                                ], width=12, md=6)
                            ])
                        ], id="online-ssl-options", className="mb-3"),
                        
                        # Connection String Input (for custom connections)
                        html.Div([
                            dbc.Label([
                                html.I(className="fas fa-code me-2"),
                                "Database Connection String"
                            ], className="text-white mb-2"),
                            dbc.Input(
                                type="text", 
                                id="connection-string-input", 
                                placeholder="mysql+pymysql://username:password@host:port/database",
                                className="form-control mb-3"
                            ),
                            dbc.FormText([
                                html.I(className="fas fa-info-circle me-1"),
                                "Format: mysql+pymysql://username:password@host:port/database"
                            ], className="text-muted"),
                        ], id="custom-connection-div", className="mb-3"),
                        
                        # Local/Online Connection Form
                        html.Div([
                            dbc.Form([
                                dbc.Row([
                                    dbc.Label([
                                        html.I(className="fas fa-server me-2"),
                                        "Host"
                                    ], width=12, md=4, className="d-flex align-items-center text-white mb-2 mb-md-0"),
                                    dbc.Col([
                                        dbc.Input(
                                            type="text", 
                                            id="host-input", 
                                            placeholder="Enter host", 
                                            value="localhost",
                                            className="form-control"
                                        ),
                                    ], width=12, md=8)
                                ], className="mb-3 align-items-center"),
                                
                                dbc.Row([
                                    dbc.Label([
                                        html.I(className="fas fa-plug me-2"),
                                        "Port"
                                    ], width=12, md=4, className="d-flex align-items-center text-white mb-2 mb-md-0"),
                                    dbc.Col([
                                        dbc.Input(
                                            type="text", 
                                            id="port-input", 
                                            placeholder="Enter port", 
                                            value="3306",
                                            className="form-control"
                                        ),
                                    ], width=12, md=8)
                                ], className="mb-3 align-items-center"),
                                
                                dbc.Row([
                                    dbc.Label([
                                        html.I(className="fas fa-database me-2"),
                                        "Database"
                                    ], width=12, md=4, className="d-flex align-items-center text-white mb-2 mb-md-0"),
                                    dbc.Col([
                                        dbc.Input(
                                            type="text", 
                                            id="database-input", 
                                            placeholder="Enter database name",
                                            className="form-control"
                                        ),
                                    ], width=12, md=8)
                                ], className="mb-3 align-items-center"),
                                
                                dbc.Row([
                                    dbc.Label([
                                        html.I(className="fas fa-user me-2"),
                                        "Username"
                                    ], width=12, md=4, className="d-flex align-items-center text-white mb-2 mb-md-0"),
                                    dbc.Col([
                                        dbc.Input(
                                            type="text", 
                                            id="username-input", 
                                            placeholder="Enter username",
                                            className="form-control"
                                        ),
                                    ], width=12, md=8)
                                ], className="mb-3 align-items-center"),
                                
                                dbc.Row([
                                    dbc.Label([
                                        html.I(className="fas fa-lock me-2"),
                                        "Password"
                                    ], width=12, md=4, className="d-flex align-items-center text-white mb-2 mb-md-0"),
                                    dbc.Col([
                                        dbc.Input(
                                            type="password", 
                                            id="password-input", 
                                            placeholder="Enter password",
                                            className="form-control"
                                        ),
                                    ], width=12, md=8)
                                ], className="mb-3 align-items-center"),
                            ]),
                        ], id="host-connection-form"),
                        
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-plug me-2"),
                                    "Connect to Database"
                                ], id="connect-button", color="primary", className="w-100"),
                            ], width=12)
                        ], className="mb-3"),
                        
                        # Connection Status
                        html.Div(id="connection-status", className="mt-3"),
                        

                    ], className="p-4"),
                ], 
                className="mt-5 shadow",
                style={
                    'backgroundColor': 'rgba(255, 255, 255, 0.15)',
                    'border': '1px solid rgba(255, 255, 255, 0.2)',
                    'borderRadius': '12px',
                    'position': 'relative',
                    'zIndex': '1',
                    'backdropFilter': 'blur(8px)',
                }
                ),
            ], 
            xs=12, sm=10, md=8, lg=6, xl=5,
            className="mx-auto"
        ),
    ], 
    className="py-5 d-flex align-items-center min-vh-100"
    ),
], style={'minHeight': '100vh'})])

# Callback to handle connection type changes
@callback(
    [Output("custom-connection-div", "style"),
     Output("host-connection-form", "style"),
     Output("online-ssl-options", "style")],
    Input("connection-type-dropdown", "value")
)
def toggle_connection_form(connection_type):
    if connection_type == "custom":
        return [{"display": "block"}, {"display": "none"}, {"display": "none"}]
    elif connection_type == "online":
        return [{"display": "none"}, {"display": "block"}, {"display": "block"}]
    else:  # local
        return [{"display": "none"}, {"display": "block"}, {"display": "none"}]

# Callback to handle database connection
@callback(
    [Output("connection-status", "children"),
     Output("db-connection-url", "pathname")],
    Input("connect-button", "n_clicks"),
    [State("connection-type-dropdown", "value"),
     State("host-input", "value"),
     State("port-input", "value"),
     State("database-input", "value"),
     State("username-input", "value"),
     State("password-input", "value"),
     State("connection-string-input", "value"),
     State("ssl-mode-dropdown", "value"),
     State("ssl-cert-path", "value")],
    prevent_initial_call=True
)
def connect_to_database(n_clicks, connection_type, host, port, database, username, password, connection_string, ssl_mode, ssl_cert_path):
    try:
        # Build connection string based on connection type
        if connection_type == "custom":
            if not connection_string or not connection_string.strip():
                return [dbc.Alert(
                    [html.I(className="fas fa-exclamation-circle me-2"), "Connection string is required!"],
                    color="warning",
                    className="mt-3"
                ), dash.no_update]
            final_connection_string = connection_string
        elif connection_type == "online":
            # Validation for online connection
            if not host or not host.strip():
                return [dbc.Alert(
                    [html.I(className="fas fa-exclamation-circle me-2"), "Host is required!"],
                    color="warning",
                    className="mt-3"
                ), dash.no_update]
            
            if not database or not database.strip():
                return [dbc.Alert(
                    [html.I(className="fas fa-exclamation-circle me-2"), "Database name is required!"],
                    color="warning",
                    className="mt-3"
                ), dash.no_update]
            
            if not username or not username.strip():
                return [dbc.Alert(
                    [html.I(className="fas fa-exclamation-circle me-2"), "Username is required!"],
                    color="warning",
                    className="mt-3"
                ), dash.no_update]
            
            port = port or "3306"
            if password:
                final_connection_string = f"mysql+pymysql://{username}:{urllib.parse.quote(password)}@{host}:{port}/{database}"
            else:
                final_connection_string = f"mysql+pymysql://{username}@{host}:{port}/{database}"
        else:  # local
            # Standard local connection
            if not host or not host.strip():
                return [dbc.Alert(
                    [html.I(className="fas fa-exclamation-circle me-2"), "Host is required!"],
                    color="warning",
                    className="mt-3"
                ), dash.no_update]
            
            if not database or not database.strip():
                return [dbc.Alert(
                    [html.I(className="fas fa-exclamation-circle me-2"), "Database name is required!"],
                    color="warning",
                    className="mt-3"
                ), dash.no_update]
            
            if not username or not username.strip():
                return [dbc.Alert(
                    [html.I(className="fas fa-exclamation-circle me-2"), "Username is required!"],
                    color="warning",
                    className="mt-3"
                ), dash.no_update]
            
            port = port or "3306"
            if password:
                final_connection_string = f"mysql+pymysql://{username}:{urllib.parse.quote(password)}@{host}:{port}/{database}"
            else:
                final_connection_string = f"mysql+pymysql://{username}@{host}:{port}/{database}"
        
        # Test connection with appropriate parameters
        engine_params = {
            'pool_timeout': 30,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
            'echo': False
        }
        
        # Handle SSL for online connections
        if connection_type == "online":
            connect_args = {}
            
            # Handle SSL mode
            if ssl_mode == "DISABLED":
                connect_args['ssl_disabled'] = True
            else:
                connect_args['ssl_disabled'] = False
                connect_args['ssl'] = {'ssl_mode': ssl_mode}
                
                # Handle SSL certificate if provided
                if ssl_cert_path and ssl_cert_path.strip():
                    if os.path.exists(ssl_cert_path):
                        connect_args['ssl']['ssl_ca'] = ssl_cert_path
                    else:
                        return [dbc.Alert([
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            f"SSL certificate file not found: {ssl_cert_path}"
                        ], 
                        color="warning",
                        className="mt-3"
                        ), dash.no_update]
            
            engine_params['connect_args'] = connect_args
        
        engine = create_engine(final_connection_string, **engine_params)
        
        # Test the connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
        
        # Store connection string and SSL info in user session
        session['db_connection_string'] = final_connection_string
        if connection_type == "online":
            session['ssl_mode'] = ssl_mode
            if ssl_cert_path and ssl_cert_path.strip():
                session['ssl_cert_path'] = ssl_cert_path
        
        # Return success message and redirect to dashboard
        success_alert = dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            "Successfully connected to the database! Redirecting to dashboard..."
        ], 
        color="success",
        className="mt-3"
        )
        
        return [success_alert, "/apps/dashboard"] 
        
    except SQLAlchemyError as e:
        error_msg = str(e)
        # Provide more user-friendly error messages
        if "Access denied" in error_msg:
            user_error = "Access denied. Please check your username and password."
        elif "Unknown database" in error_msg:
            user_error = "Database not found. Please check the database name."
        elif "Can't connect" in error_msg or "Connection refused" in error_msg:
            user_error = "Cannot connect to the database server. Please check host and port."
        elif "SSL connection is required" in error_msg:
            user_error = "SSL connection is required. Please enable SSL or check SSL settings."
        elif "certificate verify failed" in error_msg:
            user_error = "SSL certificate verification failed. Please check your SSL certificate path."
        elif "No module named" in error_msg and "MySQLdb" in error_msg:
            user_error = "MySQL driver not found. Please install pymysql: pip install pymysql"
        else:
            user_error = f"Database connection error: {error_msg}"
            
        return [dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            user_error
        ], 
        color="danger",
        className="mt-3"
        ), dash.no_update]
    except Exception as e:
        error_msg = str(e)
        if "No module named" in error_msg and ("MySQLdb" in error_msg or "pymysql" in error_msg):
            user_error = "MySQL driver not found. Please install pymysql: pip install pymysql"
            return [dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                user_error
            ], 
            color="danger",
            className="mt-3"
            ), dash.no_update]
        else:
            return [dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Unexpected error: {error_msg}"
            ], 
            color="danger",
            className="mt-3"
            ), dash.no_update]

def get_db_engine():
    if 'db_connection_string' in session and session['db_connection_string']:
        try:
            engine_params = {
                'pool_timeout': 30,
                'pool_recycle': 3600,
                'pool_pre_ping': True
            }
            
            # Handle SSL if stored (for online connections)
            if 'ssl_mode' in session:
                ssl_mode = session.get('ssl_mode', 'PREFERRED')
                connect_args = {}
                
                if ssl_mode == "DISABLED":
                    connect_args['ssl_disabled'] = True
                else:
                    connect_args['ssl_disabled'] = False
                    connect_args['ssl'] = {'ssl_mode': ssl_mode}
                    
                    # Handle SSL certificate if stored
                    if 'ssl_cert_path' in session:
                        cert_path = session['ssl_cert_path']
                        if os.path.exists(cert_path):
                            connect_args['ssl']['ssl_ca'] = cert_path
                
                engine_params['connect_args'] = connect_args
            
            engine = create_engine(
                session['db_connection_string'],
                **engine_params
            )
            return engine
        except Exception as e:
            print(f"Error creating engine: {e}")
            return None
    return None

def is_connected():
    engine = get_db_engine()
    if engine:
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    return False