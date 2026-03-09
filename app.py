# app.py
import dash
from dash import dcc, html, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
from flask import session, send_from_directory
import datetime
import uuid
import os
import sqlite3
from sqlalchemy import create_engine, text
import sys
import atexit
import signal
import logging
import tempfile

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Handle PyInstaller paths
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# Add project directory to Python path for PyInstaller compatibility
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
    sys.path.insert(0, application_path)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# App configuration
APP_NAME = "AIBES Analytics"  

# Initializing the dash app with suppress_callback_exceptions=True
app = dash.Dash(__name__, 
                external_stylesheets=[
                    dbc.themes.BOOTSTRAP,
                    "https://use.fontawesome.com/releases/v6.0.0/css/all.css"
                ],
                suppress_callback_exceptions=True,
                server=True,
                title=APP_NAME,  
                assets_folder=resource_path('assets'),  # PyInstaller compatible assets folder
                meta_tags=[  #viewport meta tag for better mobile responsiveness
                    {"name": "viewport", "content": "width=device-width, initial-scale=1"}
                ])

# Make the server object available for gunicorn
server = app.server

# Configure session middleware - FIXED FOR FLASK 2.0+ COMPATIBILITY
# Ensure session cookie name is set
if not hasattr(server, 'session_cookie_name'):
    server.session_cookie_name = 'session'

# Use filesystem sessions with temporary directory
server.config['SECRET_KEY'] = 'bati-aibes'
server.config['SESSION_TYPE'] = 'filesystem'
server.config['SESSION_FILE_DIR'] = tempfile.mkdtemp()
server.config['SESSION_PERMANENT'] = False
server.config['SESSION_USE_SIGNER'] = True
server.config['SESSION_KEY_PREFIX'] = 'aibes_'

# Import and initialize Flask-Session after config
from flask_session import Session
Session(server)

# Store active connections for cleanup
active_connections = {}

# Function to cleanup database connections on shutdown
def cleanup_connections():
    """Clean up all active database connections"""
    try:
        for user_id, conn_string in list(active_connections.items()):
            logger.info(f"Cleaning up connection for user: {user_id}")
            # Remove from active connections
            active_connections.pop(user_id, None)
        logger.info("All connections cleaned up successfully")
    except Exception as e:
        logger.error(f"Error cleaning up connections: {e}")

# Register cleanup function
atexit.register(cleanup_connections)

# Handle SIGTERM (graceful shutdown)
def signal_handler(sig, frame):
    cleanup_connections()
    logger.info("Application shutdown gracefully")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Serve generated reports 
@app.server.route('/generated_reports/<path:filename>')
def serve_report(filename):
    reports_dir = os.path.join(application_path, "generated_reports")
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    return send_from_directory(reports_dir, filename)

@app.server.route('/serve-logo/<path:filename>')
def serve_logo(filename):
    logos_dir = os.path.join(application_path, "logos")
    if not os.path.exists(logos_dir):
        os.makedirs(logos_dir)
    return send_from_directory(logos_dir, filename)

# Initializing the database tables function
def initialize_database_tables():
    """Initialize all required database tables"""
    try:
        settings_db_path = os.path.join(application_path, "settings.db")
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
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database tables: {e}")

# Import apps after basic app initialization but before layout definition
try:
    from apps import home, dashboard, db_connection, land_bank_analysis, sales_analysis, reports_view, settings
except ImportError as e:
    logger.warning(f"Error importing apps: {e}")
    # Create mock modules for development
    class MockLayout:
        layout = html.Div("App not available")
    
    home = MockLayout()
    dashboard = MockLayout()
    db_connection = MockLayout()
    land_bank_analysis = MockLayout()
    sales_analysis = MockLayout()
    reports_view = MockLayout()
    settings = MockLayout()

# Function to get connection status for appbar
def get_connection_status_component():
    with server.app_context():
        is_connected = ('db_connection_string' in session and 
                       session['db_connection_string'] and
                       session.get('user_id'))
        
        if is_connected:
            try:
                engine = create_engine(session['db_connection_string'])
                with engine.connect() as connection:
                    result = connection.execute(text("SELECT 1"))
                    result.fetchone()
                
                # Get database name 
                try:
                    from sqlalchemy.engine.url import make_url
                    url = make_url(session['db_connection_string'])
                    db_label = url.database or url.host
                except:
                    db_label = session['db_connection_string'].split('/')[-1]
                
                # Store active connection
                user_id = session.get('user_id', 'unknown')
                active_connections[user_id] = session['db_connection_string']
                
                return html.Div([
                    html.Span([
                        html.I(className="fas fa-check-circle text-success me-1"),
                        html.Span(f"Connected: {db_label}", className="d-none d-md-inline"),
                        html.Span("✓", className="d-md-none")
                    ], className="text-success small")
                ], className="d-flex align-items-center")
            except Exception as e:
                logger.error(f"Connection status check error: {e}")
                return html.Div([
                    html.Span([
                        html.I(className="fas fa-exclamation-triangle text-warning me-1"),
                        html.Span("Connection Lost", className="d-none d-md-inline"),
                        html.Span("⚠", className="d-md-none")
                    ], className="text-warning small")
                ], className="d-flex align-items-center")
        else:
            return html.Div([
                html.Span([
                    html.I(className="fas fa-times-circle text-danger me-1"),
                    html.Span("Not Connected", className="d-none d-md-inline"),
                    html.Span("✗", className="d-md-none")
                ], className="text-danger small")
            ], className="d-flex align-items-center")

# Function to create auth button based on connection state
def create_auth_button(is_connected):
    if is_connected:
        return dbc.Button([
            html.I(className="fas fa-sign-out-alt me-1"),
            html.Span("Logout", className="d-none d-md-inline")
        ], id="auth-btn", color="danger", size="sm", className="btn-sm")
    else:
        return dbc.Button([
            html.I(className="fas fa-sign-in-alt me-1"),
            html.Span("Login", className="d-none d-md-inline")
        ], id="auth-btn", color="success", size="sm", className="btn-sm", href="/apps/db_connection")

#top appbar component (FIXED POSITION)
def create_top_appbar():
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Button([
                        html.I(className="fas fa-bars")
                    ], id="sidebar-toggle", className="btn btn-sm btn-outline-dark me-2"),
                    html.A([
                        html.Img(src="/assets/aibes.png", height="30px", className="me-2"),
                        html.Span(APP_NAME, className="fs-5 fw-bold", style={"color": "#12385C"})
                    ], href="/", className="d-flex align-items-center text-decoration-none")
                ], className="d-flex align-items-center")
            ], width=6, className="d-flex align-items-center"),
            
            #Connection Status and Auth Button (aligned right)
            dbc.Col([
                html.Div([
                    # Connection Status
                    html.Div(id="appbar-connection-status", className="me-3"),
                    
                    # Dynamic Auth Button (Login/Logout)
                    html.Div(id="auth-button-container")
                ], className="d-flex align-items-center justify-content-end")  #right alignment
            ], width=6, className="d-flex align-items-center justify-content-end")  #align the column itself
        ], className="gx-0")
    ], className="p-2 shadow", 
       style={
           "height": "60px",
           "position": "fixed",
           "backgroundColor": "white",
           "top": "0",
           "left": "0",
           "right": "0",
           "zIndex": "1001",
           "transition": "all 0.3s"
       })

# Create sidebar component
def create_sidebar():
    return html.Div([
        # Sidebar Navigation
        dbc.Nav([
            dbc.NavLink([
                html.I(className="fas fa-home me-2"),
                html.Span("Home", id="nav-text-home", className="nav-text")
            ], href="/", active="exact"),
            
            dbc.NavLink([
                html.I(className="fas fa-tachometer-alt me-2"),
                html.Span("Quick Insights", id="nav-text-dashboard", className="nav-text")
            ], href="/apps/dashboard", active="exact"),
            
            dbc.NavLink([
                html.I(className="fas fa-map me-2"),
                html.Span("Project And Stands Analysis", id="nav-text-land-bank", className="nav-text")
            ], href="/apps/land_bank_analysis", active="exact"),
            
            dbc.NavLink([
                html.I(className="fas fa-dollar-sign me-2"),
                html.Span("Sales Analysis", id="nav-text-sales-analysis", className="nav-text")
            ], href="/apps/sales_analysis", active="exact"),
            
            dbc.NavLink([
                html.I(className="fas fa-file-alt me-2"),
                html.Span("Reports", id="nav-text-reports", className="nav-text")
            ], href="/apps/reports_view", active="exact"),
            
            dbc.NavLink([
                html.I(className="fas fa-database me-2"),
                html.Span("Database", id="nav-text-database", className="nav-text")
            ], href="/apps/db_connection", active="exact"),
            
            dbc.NavLink([
                html.I(className="fas fa-cog me-2"),
                html.Span("Settings", id="nav-text-settings", className="nav-text")
            ], href="/apps/settings", active="exact"),
        ], vertical=True, pills=True, className="flex-column px-2 py-3"),
    ], className="text-white vh-100 position-fixed", 
       style={
           "width": "250px", 
           "zIndex": 1000, 
           "transition": "all 0.3s", 
           "top": "60px",
           "backgroundColor": "#092F53"  # Dark blue background
       },
       id="main-sidebar")

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

# Login modal
login_modal = dbc.Modal([
    dbc.ModalHeader(dbc.ModalTitle([
        html.I(className="fas fa-sign-in-alt me-2"),
        "Login Required"
    ])),
    dbc.ModalBody([
        html.P("Please connect to a database to access this feature."),
        html.Div(id="login-error-message")
    ]),
    dbc.ModalFooter([
        dbc.Button([
            html.I(className="fas fa-database me-2"),
            "Connect to Database"
        ], href="/apps/db_connection", color="primary"),
        dbc.Button([
            html.I(className="fas fa-times me-2"),
            "Cancel"
        ], id="cancel-login-btn", color="secondary"),
    ]),
], id="login-modal", centered=True)

# App layout with appbar and sidebar
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    # Multi-user session management
    dcc.Store(id='session-id'), 
    # Store to track sidebar state
    dcc.Store(id='sidebar-state', data=True),  # True = expanded, False = collapsed
    # Logout confirmation modal
    logout_modal,
    # Login modal
    login_modal,
    # Top Appbar (FIXED)
    create_top_appbar(),
    # Sidebar (POSITIONED BELOW APPBAR)
    create_sidebar(),
    # Page content with margin for sidebar and appbar
    html.Div(id='page-content', children=[], className="", 
             style={
                 "marginLeft": "250px", 
                 "marginTop": "60px",
                 "minHeight": "calc(100vh - 60px)", 
                 "transition": "margin-left 0.3s"
             })
])

# Session initialization callback
@callback(Output('session-id', 'data'),
          Input('url', 'pathname'))
def initialize_session(pathname):
    # Initializing session for each user
    with server.app_context():
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
            session['db_connection_string'] = None
        return session['user_id']

# Sidebar toggle callback
@callback(
    [Output('main-sidebar', 'style'),
     Output('page-content', 'style'),
     Output('sidebar-state', 'data'),
     Output('nav-text-home', 'className'),
     Output('nav-text-dashboard', 'className'),
     Output('nav-text-land-bank', 'className'),
     Output('nav-text-sales-analysis', 'className'),
     Output('nav-text-reports', 'className'),
     Output('nav-text-database', 'className'),
     Output('nav-text-settings', 'className')],
    [Input('sidebar-toggle', 'n_clicks')],
    [State('sidebar-state', 'data')],
    prevent_initial_call=False
)
def toggle_sidebar(n_clicks, sidebar_expanded):
    if n_clicks is None:
        # Initial state - expanded
        new_sidebar_style = {"width": "250px", "zIndex": 1000, "transition": "all 0.3s", "top": "60px", "backgroundColor": "#092F53"}
        new_content_style = {"marginLeft": "250px", "marginTop": "60px", "minHeight": "calc(100vh - 60px)", "transition": "margin-left 0.3s"}
        new_sidebar_state = True
        nav_classes = "nav-text"
    else:
        # Toggle state
        if sidebar_expanded:
            # Collapse sidebar
            new_sidebar_style = {"width": "60px", "zIndex": 1000, "transition": "all 0.3s", "top": "60px", "backgroundColor": "#092F53"}
            new_content_style = {"marginLeft": "60px", "marginTop": "60px", "minHeight": "calc(100vh - 60px)", "transition": "margin-left 0.3s"}
            new_sidebar_state = False
            nav_classes = "d-none"
        else:
            # Expand sidebar
            new_sidebar_style = {"width": "250px", "zIndex": 1000, "transition": "all 0.3s", "top": "60px", "backgroundColor": "#092F53"}
            new_content_style = {"marginLeft": "250px", "marginTop": "60px", "minHeight": "calc(100vh - 60px)", "transition": "margin-left 0.3s"}
            new_sidebar_state = True
            nav_classes = "nav-text"
    
    return [new_sidebar_style, new_content_style, new_sidebar_state, nav_classes, nav_classes, 
            nav_classes, nav_classes, nav_classes, nav_classes, nav_classes]

# Update connection status and auth button in appbar
@callback(
    [Output('appbar-connection-status', 'children'),
     Output('auth-button-container', 'children')],
    [Input('url', 'pathname')],
    prevent_initial_call=False
)
def update_appbar_components(pathname):
    # Get connection status
    connection_status = get_connection_status_component()
    
    # Check if user is connected
    with server.app_context():
        is_connected = ('db_connection_string' in session and 
                       session['db_connection_string'] and
                       session.get('user_id'))
    
    # Create appropriate auth button
    auth_button = create_auth_button(is_connected)
    
    return [connection_status, auth_button]

# Combined modal callback for both login and logout modals
@callback(
    [Output("logout-modal", "is_open"),
     Output("login-modal", "is_open")],
    [Input("auth-button-container", "children"),  # Changed to listen to container changes
     Input("cancel-logout-btn", "n_clicks"),
     Input("cancel-login-btn", "n_clicks"),
     Input("url", "pathname")],
    prevent_initial_call=False
)
def handle_modals(auth_container_children, cancel_logout_clicks, cancel_login_clicks, pathname):
    # Default state - both modals closed
    logout_modal_open = False
    login_modal_open = False
    
    triggered_id = ctx.triggered_id if ctx.triggered_id else None
    
    # Handle logout modal triggers
    if triggered_id == "auth-button-container":
        # Check if auth button changed to logout button (meaning user is now connected)
        # We don't want to show modal just because button changed
        pass
    elif triggered_id == "cancel-logout-btn":
        logout_modal_open = False
        
    # Handle login modal triggers
    elif triggered_id == "cancel-login-btn":
        login_modal_open = False
        
    # Handle protected route access
    protected_pages = [
        '/apps/dashboard', 
        '/apps/settings', 
        '/apps/land_bank_analysis', 
        '/apps/sales_analysis', 
        '/apps/reports_view'
    ]
    
    if triggered_id == "url" and pathname in protected_pages:
        if not get_user_db_connection():
            login_modal_open = True
    
    return [logout_modal_open, login_modal_open]

# Separate callback for handling logout click
@callback(
    Output("logout-modal", "is_open", allow_duplicate=True),
    Input("auth-btn", "n_clicks"),
    prevent_initial_call=True
)
def handle_logout_click(n_clicks):
    if n_clicks:
        with server.app_context():
            is_connected = ('db_connection_string' in session and 
                           session['db_connection_string'] and
                           session.get('user_id'))
            if is_connected:
                return True
    return False

# Main page content callback
@callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname'),
     Input('confirm-logout-btn', 'n_clicks')],
    prevent_initial_call='initial_duplicate'
)
def display_page(pathname, logout_clicks):
    triggered_id = ctx.triggered_id if ctx.triggered_id else None
    
    # Handle logout
    if triggered_id == 'confirm-logout-btn':
        # Clean up connection
        with server.app_context():
            user_id = session.get('user_id')
            if user_id:
                active_connections.pop(user_id, None)
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
                            "Login Again"
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
        return logout_success_page
    
    # Protected pages 
    protected_pages = [
        '/apps/dashboard', 
        '/apps/settings', 
        '/apps/land_bank_analysis', 
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
            return error_page
    
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
            return already_connected_page
        
    # Page routing
    if pathname == '/':
        return home.layout
    elif pathname == '/apps/db_connection':
        return db_connection.layout
    elif pathname == '/apps/dashboard':
        return dashboard.layout
    elif pathname == '/apps/land_bank_analysis':
        return land_bank_analysis.layout
    elif pathname == '/apps/sales_analysis':
        return sales_analysis.layout
    elif pathname == '/apps/reports_view':
        return reports_view.layout
    elif pathname == '/apps/settings':
        return settings.layout
    else:
        not_found = dbc.Container([
            html.H1("404 - Page not found"),
            html.P("The requested page does not exist."),
            dbc.Button("Go Home", href="/", color="primary", className="mt-3")
        ], className="text-center mt-5")
        return not_found

# Function to get user-specific database connection with connection tracking
def get_user_db_connection():
    with server.app_context():
        if 'db_connection_string' in session and session['db_connection_string']:
            try:
                engine = create_engine(session['db_connection_string'])
                # Store active connection
                user_id = session.get('user_id', 'unknown')
                if user_id:
                    active_connections[user_id] = session['db_connection_string']
                return engine
            except Exception as e:
                logger.error(f"Database connection error: {e}")
                # Remove from active connections on error
                user_id = session.get('user_id')
                if user_id:
                    active_connections.pop(user_id, None)
                return None
        return None

# Initialize database tables when the app starts
initialize_database_tables()

# Initialize favicon route
@app.server.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.server.root_path, 'assets'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    # Get port from environment variable (for Render) or default to 8050
    port = int(os.environ.get('PORT', 8050))
    
    # Run the app
    app.run_server(debug=False)