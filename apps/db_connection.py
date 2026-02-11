import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from flask import session



layout = html.Div([
    dcc.Location(id="db-connection-url", refresh=True),  
    
    #background image 
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
    
    # Content container
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
                        dbc.Form([
                            dbc.Row([
                                dbc.Label([
                                    html.I(className="fas fa-server me-2"),
                                    "Host"
                                ], width=4, className="d-flex align-items-center text-white"),
                                dbc.Col([
                                    dbc.Input(
                                        type="text", 
                                        id="host-input", 
                                        placeholder="Enter host", 
                                        value="localhost",
                                        className="form-control"
                                    ),
                                ], width=8)
                            ], className="mb-3"),
                            
                            dbc.Row([
                                dbc.Label([
                                    html.I(className="fas fa-database me-2"),
                                    "Database"
                                ], width=4, className="d-flex align-items-center text-white"),
                                dbc.Col([
                                    dbc.Input(
                                        type="text", 
                                        id="database-input", 
                                        placeholder="Enter database name",
                                        className="form-control"
                                    ),
                                ], width=8)
                            ], className="mb-3"),
                            
                            dbc.Row([
                                dbc.Label([
                                    html.I(className="fas fa-user me-2"),
                                    "Username"
                                ], width=4, className="d-flex align-items-center text-white"),
                                dbc.Col([
                                    dbc.Input(
                                        type="text", 
                                        id="username-input", 
                                        placeholder="Enter username",
                                        className="form-control"
                                    ),
                                ], width=8)
                            ], className="mb-3"),
                            
                            dbc.Row([
                                dbc.Label([
                                    html.I(className="fas fa-lock me-2"),
                                    "Password"
                                ], width=4, className="d-flex align-items-center text-white"),
                                dbc.Col([
                                    dbc.Input(
                                        type="password", 
                                        id="password-input", 
                                        placeholder="Enter password",
                                        className="form-control"
                                    ),
                                ], width=8)
                            ], className="mb-3"),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button([
                                        html.I(className="fas fa-plug me-2"),
                                        "Connect to Database"
                                    ], id="connect-button", color="primary", className="w-100"),
                                ], width=12)
                            ], className="mb-3"),
                        ]),
                        html.Div(id="connection-status", className="mt-3 text-center"),
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
            ], width={"size": 5, "offset": 3}),
        ]),
    ], fluid=True, className="py-5"),
])

# Callback to handle database connection (redirect)
@callback(
    [Output("connection-status", "children"),
     Output("db-connection-url", "pathname")],
    Input("connect-button", "n_clicks"),
    State("host-input", "value"),
    State("database-input", "value"),
    State("username-input", "value"),
    State("password-input", "value"),
    prevent_initial_call=True
)
def connect_to_database(n_clicks, host, database, username, password):
    # Validation of required fields
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
    
    try:
        # connection string
        if password:
            connection_string = f"mysql+pymysql://{username}:{password}@{host}/{database}"
        else:
            connection_string = f"mysql+pymysql://{username}@{host}/{database}"
        
        # Test connection
        engine = create_engine(connection_string)
        connection = engine.connect()
        connection.close()
        
        # Store connection string in user session
        session['db_connection_string'] = connection_string
        
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
        return [dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error connecting to database: {str(e)}"
        ], 
        color="danger",
        className="mt-3"
        ), dash.no_update]
    except Exception as e:
        return [dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Unexpected error: {str(e)}"
        ], 
        color="danger",
        className="mt-3"
        ), dash.no_update]

# Function to get database engine for current user
def get_db_engine():
    if 'db_connection_string' in session and session['db_connection_string']:
        try:
            engine = create_engine(session['db_connection_string'])
            return engine
        except:
            pass
    return None

# Function to check if connected for current user
def is_connected():
    if 'db_connection_string' in session and session['db_connection_string']:
        try:
            engine = create_engine(session['db_connection_string'])
            connection = engine.connect()
            connection.close()
            return True
        except:
            return False
    return False