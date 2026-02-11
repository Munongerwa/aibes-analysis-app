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

# Initializing the dash app with suppress_callback_exceptions=True
app = dash.Dash(__name__, 
                external_stylesheets=[
                    dbc.themes.BOOTSTRAP,
                    "https://use.fontawesome.com/releases/v6.0.0/css/all.css"
                ],
                suppress_callback_exceptions=True,
                server=True)

# Make the server object available for gunicorn
server = app.server

# Server-side session support
app.server.secret_key = 'bati-aibes'  

# Serve generated reports 
@app.server.route('/generated_reports/<path:filename>')
def serve_report(filename):
    reports_dir = os.path.join(os.path.dirname(__file__), "generated_reports")
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    return send_from_directory(reports_dir, filename)

@app.server.route('/serve-logo/<path:filename>')
def serve_logo(filename):
    logos_dir = os.path.join(os.path.dirname(__file__), "logos")
    if not os.path.exists(logos_dir):
        os.makedirs(logos_dir)
    return send_from_directory(logos_dir, filename)

# Initializing the database tables function
def initialize_database_tables():
    """Initialize all required database tables"""
    try:
        settings_db_path = os.path.join(os.path.dirname(__file__), "settings.db")
        conn = sqlite3.connect(settings_db_path)
        cursor = conn.cursor()
        
        #company settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS company_settings (
                id INTEGER PRIMARY KEY,
                company_name TEXT,
                logo_path TEXT,
                logo_data BLOB,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        #email settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_settings (
                id INTEGER PRIMARY KEY,
                smtp_server TEXT,
                smtp_port INTEGER,
                email_username TEXT,
                email_password TEXT,
                sender_email TEXT,
                sender_name TEXT,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default company settings if none exist
        cursor.execute("SELECT COUNT(*) FROM company_settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO company_settings (id, company_name) 
                VALUES (1, 'AIBES Real Estate')
            ''')
        
        # Insert default email settings if none exist
        cursor.execute("SELECT COUNT(*) FROM email_settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO email_settings (id, smtp_server, smtp_port) 
                VALUES (1, 'smtp.gmail.com', 587)
            ''')
        
        conn.commit()
        conn.close()
        print("Database tables initialized successfully")
    except Exception as e:
        print(f"Error initializing database tables: {e}")

# Logout confirmation modal
logout_modal = dbc.Modal([
    dbc.ModalHeader(dbc.ModalTitle([
        html.I(className="fas fa-sign-out-alt me-2"),
        "Confirm Logout"
    ])),
    dbc.ModalBody([
        html.P("Are you sure you want to logout? This will disconnect you from the database."),
        html.Small("You can reconnect later by going to the Database Connection page.", className="text-muted")
    ]),
    dbc.ModalFooter([
        dbc.Button([
            html.I(className="fas fa-check me-2"),
            "Yes, Logout"
        ], id="confirm-logout-btn", color="danger"),
        dbc.Button([
            html.I(className="fas fa-times me-2"),
            "Cancel"
        ], id="cancel-logout-btn", color="secondary"),
    ]),
], id="logout-modal", centered=True)

# Modernized Navbar with Gradient
navbar = dbc.Navbar(
    dbc.Container([
        # Brand Section
        html.A(
            dbc.Row([
                html.Img(src="/assets/aibes.png", height="40px"),
                
            ],
            align="center",
            className="g-0"
            ),
            href="/",
            style={"textDecoration": "none"},
        ),

        # Desktop Navigation
        dbc.Nav([
            dbc.NavItem(dbc.NavLink("Home", href="/", active="exact", className="mx-2")),
            dbc.NavItem(dbc.NavLink("Dashboard", href="/apps/dashboard", active="exact", className="mx-2")),
            
            dbc.DropdownMenu([
                dbc.DropdownMenuItem("Land Bank", href="/apps/land_bank_analysis"),
                dbc.DropdownMenuItem("Project Analysis", href="/apps/project_analysis"),
                dbc.DropdownMenuItem("Sales Analysis", href="/apps/sales_analysis"),
            ], 
            nav=True, 
            in_navbar=True, 
            label="Analysis",
            className="mx-2"),
            
            dbc.NavItem(dbc.NavLink("Reports", href="/apps/reports_view", active="exact", className="mx-2")),
            dbc.NavItem(dbc.NavLink("Database", href="/apps/db_connection", active="exact", className="mx-2")),
            dbc.NavItem(dbc.NavLink("Settings", href="/apps/settings", active="exact", className="mx-2")),
        ], 
        className="ms-auto d-none d-lg-flex",
        navbar=True,
        ),

        # Connection Status and Logout
        html.Div([
            html.Div(id="navbar-connection-status", className="d-flex align-items-center me-3"),
            dbc.Button([
                "Logout"
            ], id="logout-btn", color="danger", size="sm", className="btn-sm"),
        ], className="d-flex align-items-center"),
        
        # Mobile Toggler
        dbc.NavbarToggler(id="navbar-toggler", className="d-lg-none ms-2"),
    ], fluid=True),
    color="dark",
    dark=True,
    sticky="top",
    className="shadow-sm"
)

# Mobile Collapsible Menu
mobile_collapse = dbc.Collapse([
    dbc.Nav([
        dbc.NavItem(dbc.NavLink("Home", href="/", active="exact")),
        dbc.NavItem(dbc.NavLink("Dashboard", href="/apps/dashboard", active="exact")),
        dbc.DropdownMenu([
            dbc.DropdownMenuItem("Land Bank", href="/apps/land_bank_analysis"),
            dbc.DropdownMenuItem("Project Analysis", href="/apps/project_analysis"),
            dbc.DropdownMenuItem("Sales Analysis", href="/apps/sales_analysis"),
        ], nav=True, in_navbar=True, label="Analysis"),
        dbc.NavItem(dbc.NavLink("Reports", href="/apps/reports_view", active="exact")),
        dbc.NavItem(dbc.NavLink("Database", href="/apps/db_connection", active="exact")),
        dbc.NavItem(dbc.NavLink("Settings", href="/apps/settings", active="exact")),
    ], 
    vertical=True,
    pills=True,
    className="px-3 py-2 bg-dark"
    ),
], id="navbar-collapse-mobile", navbar=True)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    # Multi-user session management
    dcc.Store(id='session-id'), 
    # Logout confirmation modal
    logout_modal,
    # Modernized navbar
    navbar,
    # Mobile menu
    mobile_collapse,
    # Page content
    html.Div(id='page-content', children=[], className="pt-4"),
])

# Session initialization callback
@app.callback(Output('session-id', 'data'),
              Input('url', 'pathname'))
def initialize_session(pathname):
    # Initializing session for each user
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        session['db_connection_string'] = None
    return session['user_id']

# Callback for navbar toggle
@app.callback(
    Output("navbar-collapse-mobile", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse-mobile", "is_open")],
    prevent_initial_call=False
)
def toggle_navbar_collapse(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

# Logout modal callbacks
@app.callback(
    Output("logout-modal", "is_open"),
    [Input("logout-btn", "n_clicks"),
     Input("cancel-logout-btn", "n_clicks")],
    prevent_initial_call=True
)
def toggle_logout_modal(open_clicks, close_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "logout-btn":
        return True
    elif button_id == "cancel-logout-btn":
        return False
    return False

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
        # Clearing user session
        session.pop('db_connection_string', None)
        session.pop('user_id', None)
        # logout success page
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
    # Connection status for navbar
    connection_status = get_connection_status_component()
    # Handling logout page directly
    if pathname == '/apps/logout':
        # Clearing user session
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
        ]), connection_status]
    
    # Protected pages 
    protected_pages = [
        '/apps/dashboard', 
        '/apps/settings', 
        '/apps/land_bank_analysis', 
        '/apps/project_analysis', 
        '/apps/sales_analysis', 
        '/apps/reports_view'
    ]
    
    if pathname in protected_pages:
        if not get_user_db_connection():
            # Protected pages error
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
            return [error_page, connection_status]
    
    # Checking whether user is already connected
    if pathname == '/apps/db_connection':
        if get_user_db_connection():
            # Already connected message
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
            return [already_connected_page, connection_status]
        
    # Page routing
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

# Function to get user-specific database connection
def get_user_db_connection():
    if 'db_connection_string' in session and session['db_connection_string']:
        try:
            engine = create_engine(session['db_connection_string'])
            return engine
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    return None

# Function to get connection status component for navbar
def get_connection_status_component():
    if 'db_connection_string' in session and session['db_connection_string']:
        try:
            engine = create_engine(session['db_connection_string'])
            connection = engine.connect()
            # Get database name 
            try:
                from sqlalchemy.engine.url import make_url
                url = make_url(session['db_connection_string'])
                db_label = url.database or url.host
            except:
                db_label = session['db_connection_string'].split('/')[-1]
            connection.close()
            
            return html.Div([
                html.Span([
                    html.I(className="fas fa-check-circle text-success me-1"),
                    f"Connected: {db_label}"
                ], className="text-success small")
            ], className="d-flex align-items-center")
        except Exception as e:
            print(f"Connection status check error: {e}")
            return html.Div([
                html.Span([
                    html.I(className="fas fa-exclamation-triangle text-warning me-1"),
                    "Connection Lost"
                ], className="text-warning small")
            ], className="d-flex align-items-center")
    else:
        return html.Div([
            html.Span([
                html.I(className="fas fa-times-circle text-danger me-1"),
                "Not Connected"
            ], className="text-danger small")
        ], className="d-flex align-items-center")

# Initialize database tables when the app starts
initialize_database_tables()

if __name__ == '__main__':
    # Get port from environment variable (for Render) or default to 8000
    port = int(os.environ.get('PORT', 8000))
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=False)
    