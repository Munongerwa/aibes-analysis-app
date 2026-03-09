# settings.py
import dash
from dash import html, dcc, Input, Output, State, callback, no_update, ALL
import dash_bootstrap_components as dbc
from flask import session
from sqlalchemy import create_engine, text
import base64
from io import BytesIO
from PIL import Image
import uuid
import os
import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple layout without sidebar/appbar 
layout = dbc.Row([
    dbc.Col([
        html.H2([
            html.I(className="fas fa-cogs me-2"),
            "System Settings"
        ], className="mb-4 text-black"),
        
        # Collapsible sections instead of tabs
        html.Div([
            # Company Information Section
            dbc.Card([
                dbc.CardHeader([
                    dbc.Button([
                        html.I(className="fas fa-building me-2"),
                        "Company Information"
                    ], id="company-collapse-button", color="white", className="w-100 text-white fw-bold")
                ]),
                dbc.Collapse([
                    dbc.CardBody([
                        dbc.Form([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Company Name", className="fw-bold"),
                                    dbc.Input(
                                        type="text", 
                                        id="company-name-input",
                                        placeholder="Enter company name",
                                        className="form-control-lg"
                                    ),
                                ], width=12, className="mb-3"),
                            ]),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Company Logo", className="fw-bold"),
                                    dcc.Upload(
                                        id='upload-logo',
                                        children=html.Div([
                                            html.I(className="fas fa-cloud-upload-alt me-2"),
                                            'Drag and Drop or ',
                                            html.A('Select Logo File', className="fw-bold")
                                        ], className="text-center"),
                                        style={
                                            'width': '100%',
                                            'height': '100px',
                                            'lineHeight': '100px',
                                            'borderWidth': '2px',
                                            'borderStyle': 'dashed',
                                            'borderRadius': '10px',
                                            'textAlign': 'center',
                                            'margin': '10px 0'
                                        },
                                        multiple=False,
                                        accept='image/*'
                                    ),
                                    html.Div(id='logo-upload-status'),
                                ], width=12, className="mb-3"),
                            ]),
                        ]),
                        
                        # Logo preview 
                        html.Div(id="logo-preview-section"),
                        
                        dbc.Button([
                            html.I(className="fas fa-save me-2"),
                            "Save Company Settings"
                        ], id="save-company-settings-btn", color="primary", size="lg", className="w-100 mt-3"),
                    ])
                ], id="company-collapse", is_open=True)
            ], className="shadow-sm mb-3"),
            
            # Email Settings Section
            dbc.Card([
                dbc.CardHeader([
                    dbc.Button([
                        html.I(className="fas fa-envelope me-2"),
                        "Email Settings"
                    ], id="email-collapse-button", color="white", className="w-100 text-white fw-bold")
                ]),
                dbc.Collapse([
                    dbc.CardBody([
                        html.H5("Email Configuration", className="mb-3 text-black"),
                        dbc.Form([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("SMTP Server", className="fw-bold"),
                                    dbc.Input(
                                        type="text", 
                                        id="smtp-server-input",
                                        placeholder="smtp.gmail.com"
                                    ),
                                ], width=12, md=6, className="mb-3"),
                                dbc.Col([
                                    dbc.Label("SMTP Port", className="fw-bold"),
                                    dbc.Input(
                                        type="number", 
                                        id="smtp-port-input",
                                        placeholder="587",
                                        value=587
                                    ),
                                ], width=12, md=6, className="mb-3"),
                            ]),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Email Username", className="fw-bold"),
                                    dbc.Input(
                                        type="email", 
                                        id="email-username-input",
                                        placeholder="your-email@gmail.com"
                                    ),
                                ], width=12, className="mb-3"),
                            ]),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Email Password", className="fw-bold"),
                                    dbc.Input(
                                        type="password", 
                                        id="email-password-input",
                                        placeholder="Your email password or app password"
                                    ),
                                    html.Small("Use app-specific password for Gmail", className="text-muted")
                                ], width=12, className="mb-3"),
                            ]),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Sender Email", className="fw-bold"),
                                    dbc.Input(
                                        type="email", 
                                        id="sender-email-input",
                                        placeholder="sender@company.com"
                                    ),
                                ], width=12, md=6, className="mb-3"),
                                dbc.Col([
                                    dbc.Label("Sender Name", className="fw-bold"),
                                    dbc.Input(
                                        type="text", 
                                        id="sender-name-input",
                                        placeholder="Report System"
                                    ),
                                ], width=12, md=6, className="mb-3"),
                            ]),
                        ]),
                        
                        dbc.Button([
                            html.I(className="fas fa-save me-2"),
                            "Save Email Settings"
                        ], id="save-email-settings-btn", color="success", size="lg", className="w-100 mt-3"),
                        
                        html.Hr(),
                        
                        # Testing email
                        html.H5("Test Email Settings", className="mt-4 mb-3"),
                        dbc.Input(
                            type="email", 
                            id="test-email-input",
                            placeholder="recipient@example.com",
                            className="mb-2"
                        ),
                        dbc.Button([
                            html.I(className="fas fa-paper-plane me-2"),
                            "Send Test Email"
                        ], id="send-test-email-btn", color="info", className="w-100"),
                        html.Div(id="test-email-status", className="mt-2"),
                    ])
                ], id="email-collapse", is_open=False)
            ], className="shadow-sm mb-3"),
            
            # Targets Settings Section
            dbc.Card([
                dbc.CardHeader([
                    dbc.Button([
                        html.I(className="fas fa-bullseye me-2"),
                        "Targets Configuration"
                    ], id="targets-collapse-button", color="white", className="w-100 text-white fw-bold")
                ]),
                dbc.Collapse([
                    dbc.CardBody([
                        html.H5("Targets Configuration", className="mb-3 text-black"),
                        
                        # Yearly Targets Section
                        html.H6("Yearly Targets", className="fw-bold mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Target Year", className="fw-bold"),
                                dbc.Select(
                                    id="year-target-year",
                                    options=[{"label": str(year), "value": year} for year in range(2020, 2031)],
                                    value=pd.Timestamp.now().year
                                ),
                            ], width=12, md=4, className="mb-3"),
                            dbc.Col([
                                dbc.Label("Sales Target", className="fw-bold"),
                                dbc.Input(
                                    type="number", 
                                    id="year-sales-target",
                                    placeholder="Enter yearly sales target",
                                    min=0
                                ),
                            ], width=12, md=4, className="mb-3"),
                            dbc.Col([
                                dbc.Label("Stands Target", className="fw-bold"),
                                dbc.Input(
                                    type="number", 
                                    id="year-stands-target",
                                    placeholder="Enter yearly stands target",
                                    min=0
                                ),
                            ], width=12, md=4, className="mb-3"),
                        ]),
                        dbc.Button([
                            html.I(className="fas fa-save me-2"),
                            "Save Yearly Targets"
                        ], id="save-yearly-targets-btn", color="primary", className="mb-4"),
                        
                        # Monthly Targets Section
                        html.H6("Monthly Targets", className="fw-bold mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Target Year", className="fw-bold"),
                                dbc.Select(
                                    id="month-target-year",
                                    options=[{"label": str(year), "value": year} for year in range(2020, 2031)],
                                    value=pd.Timestamp.now().year
                                ),
                            ], width=12, md=3, className="mb-3"),
                            dbc.Col([
                                dbc.Label("Target Month", className="fw-bold"),
                                dbc.Select(
                                    id="month-target-month",
                                    options=[
                                        {"label": "January", "value": 1},
                                        {"label": "February", "value": 2},
                                        {"label": "March", "value": 3},
                                        {"label": "April", "value": 4},
                                        {"label": "May", "value": 5},
                                        {"label": "June", "value": 6},
                                        {"label": "July", "value": 7},
                                        {"label": "August", "value": 8},
                                        {"label": "September", "value": 9},
                                        {"label": "October", "value": 10},
                                        {"label": "November", "value": 11},
                                        {"label": "December", "value": 12}
                                    ],
                                    value=pd.Timestamp.now().month
                                ),
                            ], width=12, md=3, className="mb-3"),
                            dbc.Col([
                                dbc.Label("Sales Target", className="fw-bold"),
                                dbc.Input(
                                    type="number", 
                                    id="month-sales-target",
                                    placeholder="Enter monthly sales target",
                                    min=0
                                ),
                            ], width=12, md=3, className="mb-3"),
                            dbc.Col([
                                dbc.Label("Stands Target", className="fw-bold"),
                                dbc.Input(
                                    type="number", 
                                    id="month-stands-target",
                                    placeholder="Enter monthly stands target",
                                    min=0
                                ),
                            ], width=12, md=3, className="mb-3"),
                        ]),
                        dbc.Button([
                            html.I(className="fas fa-save me-2"),
                            "Save Monthly Targets"
                        ], id="save-monthly-targets-btn", color="success", className="mb-4"),
                        
                        # Weekly Targets Section
                        html.H6("Weekly Targets", className="fw-bold mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Target Year", className="fw-bold"),
                                dbc.Select(
                                    id="week-target-year",
                                    options=[{"label": str(year), "value": year} for year in range(2020, 2031)],
                                    value=pd.Timestamp.now().year
                                ),
                            ], width=12, md=3, className="mb-3"),
                            dbc.Col([
                                dbc.Label("Target Week", className="fw-bold"),
                                dbc.Input(
                                    type="number", 
                                    id="week-target-week",
                                    placeholder="Enter week number (1-52)",
                                    min=1,
                                    max=52,
                                    value=pd.Timestamp.now().isocalendar()[1]
                                ),
                            ], width=12, md=3, className="mb-3"),
                            dbc.Col([
                                dbc.Label("Sales Target", className="fw-bold"),
                                dbc.Input(
                                    type="number", 
                                    id="week-sales-target",
                                    placeholder="Enter weekly sales target",
                                    min=0
                                ),
                            ], width=12, md=3, className="mb-3"),
                            dbc.Col([
                                dbc.Label("Stands Target", className="fw-bold"),
                                dbc.Input(
                                    type="number", 
                                    id="week-stands-target",
                                    placeholder="Enter weekly stands target",
                                    min=0
                                ),
                            ], width=12, md=3, className="mb-3"),
                        ]),
                        dbc.Button([
                            html.I(className="fas fa-save me-2"),
                            "Save Weekly Targets"
                        ], id="save-weekly-targets-btn", color="warning", className="mb-4"),
                        
                        # Project Targets Section
                        html.Hr(),
                        html.H5("Project-Specific Targets", className="fw-bold mb-3"),
                        
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Select Project", className="fw-bold"),
                                dcc.Dropdown(
                                    id="project-target-project",
                                    options=[],  # Will be populated dynamically
                                    placeholder="Select a project"
                                ),
                            ], width=12, md=4, className="mb-3"),
                            
                            dbc.Col([
                                dbc.Label("Target Type", className="fw-bold"),
                                dbc.Select(
                                    id="project-target-type",
                                    options=[
                                        {"label": "Yearly", "value": "yearly"},
                                        {"label": "Monthly", "value": "monthly"},
                                        {"label": "Weekly", "value": "weekly"}
                                    ],
                                    value="yearly"
                                ),
                            ], width=12, md=3, className="mb-3"),
                            
                            dbc.Col([
                                dbc.Label("Target Year", className="fw-bold"),
                                dbc.Select(
                                    id="project-target-year",
                                    options=[{"label": str(year), "value": year} for year in range(2020, 2031)],
                                    value=pd.Timestamp.now().year
                                ),
                            ], width=12, md=2, className="mb-3"),
                            
                            dbc.Col([
                                dbc.Label("Target Period", className="fw-bold"),
                                html.Div(id="project-target-period-container", children=[
                                    dbc.Select(
                                        id="project-target-month-week",
                                        options=[
                                            {"label": "January", "value": 1},
                                            {"label": "February", "value": 2},
                                            {"label": "March", "value": 3},
                                            {"label": "April", "value": 4},
                                            {"label": "May", "value": 5},
                                            {"label": "June", "value": 6},
                                            {"label": "July", "value": 7},
                                            {"label": "August", "value": 8},
                                            {"label": "September", "value": 9},
                                            {"label": "October", "value": 10},
                                            {"label": "November", "value": 11},
                                            {"label": "December", "value": 12}
                                        ],
                                        value=pd.Timestamp.now().month
                                    )
                                ]),
                            ], width=12, md=3, className="mb-3"),
                        ]),
                        
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Sales Target", className="fw-bold"),
                                dbc.Input(
                                    type="number", 
                                    id="project-sales-target",
                                    placeholder="Enter sales target",
                                    min=0
                                ),
                            ], width=12, md=6, className="mb-3"),
                            dbc.Col([
                                dbc.Label("Stands Target", className="fw-bold"),
                                dbc.Input(
                                    type="number", 
                                    id="project-stands-target",
                                    placeholder="Enter stands target",
                                    min=0
                                ),
                            ], width=12, md=6, className="mb-3"),
                        ]),
                        
                        dbc.Button([
                            html.I(className="fas fa-save me-2"),
                            "Save Project Targets"
                        ], id="save-project-targets-btn", color="info", className="mb-4"),
                        
                        # Targets Display
                        html.Hr(),
                        html.H5("Current Targets", className="mt-4 mb-3"),
                        html.Div(id="current-targets-display"),
                        
                    ])
                ], id="targets-collapse", is_open=False)
            ], className="shadow-sm mb-3"),
        ], className="mb-4"),
        
        # Current settings display
        html.Hr(),
        html.H5("Current Settings", className="mt-4"),
        html.Div(id="current-settings-display"),
        
    ], width=12, lg=8),
], className="justify-content-center g-0")

# Collapse toggle callbacks
@callback(
    Output("company-collapse", "is_open"),
    Input("company-collapse-button", "n_clicks"),
    State("company-collapse", "is_open"),
)
def toggle_company_collapse(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@callback(
    Output("email-collapse", "is_open"),
    Input("email-collapse-button", "n_clicks"),
    State("email-collapse", "is_open"),
)
def toggle_email_collapse(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@callback(
    Output("targets-collapse", "is_open"),
    Input("targets-collapse-button", "n_clicks"),
    State("targets-collapse", "is_open"),
)
def toggle_targets_collapse(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

def get_db_engine():
    """Get database engine from session"""
    if 'db_connection_string' in session and session['db_connection_string']:
        try:
            # Use the connected database for settings instead of local settings.db
            engine = create_engine(session['db_connection_string'])
            return engine
        except Exception as e:
            logger.error(f"Error creating engine: {e}")
            return None
    return None

# Fixed version - targets table with single TIMESTAMP column
def init_database_settings(engine):
    """Initialize settings tables in the connected database"""
    try:
        # Create company settings table if not exists
        company_table_query = """
        CREATE TABLE IF NOT EXISTS aibesinsights_company_settings (
            id INT PRIMARY KEY,
            company_name VARCHAR(255),
            logo_path VARCHAR(500),
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # Create email settings table if not exists
        email_table_query = """
        CREATE TABLE IF NOT EXISTS aibesinsights_email_settings (
            id INT PRIMARY KEY,
            smtp_server VARCHAR(255),
            smtp_port INT,
            email_username VARCHAR(255),
            email_password VARCHAR(255),
            sender_email VARCHAR(255),
            sender_name VARCHAR(255),
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # Create targets table if not exists (Single TIMESTAMP column)
        targets_table_query = """
        CREATE TABLE IF NOT EXISTS aibesinsights_targets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            target_type ENUM('yearly', 'monthly', 'weekly') NOT NULL,
            target_year INT NOT NULL,
            target_month INT,
            target_week INT,
            sales_target DECIMAL(15,2),
            stands_target INT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_target (target_type, target_year, target_month, target_week)
        )
        """
        
        # Create project targets table
        project_targets_table_query = """
        CREATE TABLE IF NOT EXISTS aibesinsights_project_targets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            project_id INT NOT NULL,
            target_type ENUM('yearly', 'monthly', 'weekly') NOT NULL,
            target_year INT NOT NULL,
            target_month INT,
            target_week INT,
            sales_target DECIMAL(15,2),
            stands_target INT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_project_target (project_id, target_type, target_year, target_month, target_week),
            FOREIGN KEY (project_id) REFERENCES Projects(id) ON DELETE CASCADE
        )
        """
        
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                conn.execute(text(company_table_query))
                conn.execute(text(email_table_query))
                conn.execute(text(targets_table_query))
                conn.execute(text(project_targets_table_query))
                trans.commit()
            except Exception as e:
                trans.rollback()
                raise e
            
        # Insert default records if they don't exist
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                # Check and insert default company settings
                result = conn.execute(text("SELECT COUNT(*) FROM aibesinsights_company_settings WHERE id = 1"))
                if result.fetchone()[0] == 0:
                    conn.execute(text("""
                        INSERT INTO aibesinsights_company_settings (id, company_name) 
                        VALUES (1, 'AIBES Real Estate')
                    """))
                
                # Check and insert default email settings
                result = conn.execute(text("SELECT COUNT(*) FROM aibesinsights_email_settings WHERE id = 1"))
                if result.fetchone()[0] == 0:
                    conn.execute(text("""
                        INSERT INTO aibesinsights_email_settings (id, smtp_server, smtp_port) 
                        VALUES (1, 'smtp.gmail.com', 587)
                    """))
                
                trans.commit()
            except Exception as e:
                trans.rollback()
                raise e
            
        logger.info("Settings tables initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing settings tables: {e}")
        return False

def save_company_settings(engine, company_name=None, logo_path=None):
    """Save company settings to database"""
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                if logo_path and company_name:
                    query = """
                        UPDATE aibesinsights_company_settings 
                        SET company_name = :company_name, logo_path = :logo_path, updated_date = CURRENT_TIMESTAMP
                        WHERE id = 1
                    """
                    conn.execute(text(query), {"company_name": company_name, "logo_path": logo_path})
                elif company_name:
                    query = """
                        UPDATE aibesinsights_company_settings 
                        SET company_name = :company_name, updated_date = CURRENT_TIMESTAMP
                        WHERE id = 1
                    """
                    conn.execute(text(query), {"company_name": company_name})
                
                trans.commit()
                return True, "Company settings saved successfully"
            except Exception as e:
                trans.rollback()
                raise e
    except Exception as e:
        logger.error(f"Error saving company settings: {e}")
        return False, f"Error saving company settings: {str(e)}"

def save_email_settings(engine, smtp_server=None, smtp_port=None, email_username=None, 
                       email_password=None, sender_email=None, sender_name=None):
    """Save email settings to database"""
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                query = """
                    UPDATE aibesinsights_email_settings 
                    SET smtp_server = :smtp_server, smtp_port = :smtp_port, email_username = :email_username, 
                        email_password = :email_password, sender_email = :sender_email, sender_name = :sender_name, 
                        updated_date = CURRENT_TIMESTAMP
                    WHERE id = 1
                """
                conn.execute(text(query), {
                    "smtp_server": smtp_server, 
                    "smtp_port": smtp_port, 
                    "email_username": email_username,
                    "email_password": email_password, 
                    "sender_email": sender_email, 
                    "sender_name": sender_name
                })
                trans.commit()
                return True, "Email settings saved successfully"
            except Exception as e:
                trans.rollback()
                raise e
    except Exception as e:
        logger.error(f"Error saving email settings: {e}")
        return False, f"Error saving email settings: {str(e)}"

# Updated function to work with single TIMESTAMP column
def save_target_settings(engine, target_type, target_year, target_month=None, target_week=None, 
                        sales_target=None, stands_target=None):
    """Save target settings to database"""
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                # Check if target already exists
                check_query = """
                    SELECT id FROM aibesinsights_targets 
                    WHERE target_type = :target_type 
                    AND target_year = :target_year 
                    AND (:target_month IS NULL OR target_month = :target_month)
                    AND (:target_week IS NULL OR target_week = :target_week)
                """
                
                params = {
                    "target_type": target_type,
                    "target_year": target_year,
                    "target_month": target_month,
                    "target_week": target_week
                }
                
                result = conn.execute(text(check_query), params)
                existing_record = result.fetchone()
                
                if existing_record:
                    # Update existing record
                    update_query = """
                        UPDATE aibesinsights_targets 
                        SET sales_target = :sales_target, stands_target = :stands_target, last_updated = CURRENT_TIMESTAMP
                        WHERE id = :id
                    """
                    conn.execute(text(update_query), {
                        "sales_target": sales_target,
                        "stands_target": stands_target,
                        "id": existing_record[0]
                    })
                else:
                    # Insert new record
                    insert_query = """
                        INSERT INTO aibesinsights_targets 
                        (target_type, target_year, target_month, target_week, sales_target, stands_target)
                        VALUES (:target_type, :target_year, :target_month, :target_week, :sales_target, :stands_target)
                    """
                    conn.execute(text(insert_query), {
                        "target_type": target_type,
                        "target_year": target_year,
                        "target_month": target_month,
                        "target_week": target_week,
                        "sales_target": sales_target,
                        "stands_target": stands_target
                    })
                
                trans.commit()
                return True, f"{target_type.capitalize()} targets saved successfully"
            except Exception as e:
                trans.rollback()
                raise e
    except Exception as e:
        logger.error(f"Error saving {target_type} targets: {e}")
        return False, f"Error saving {target_type} targets: {str(e)}"

def save_project_target_settings(engine, project_id, target_type, target_year, target_month=None, target_week=None, 
                                sales_target=None, stands_target=None):
    """Save project-specific target settings to database"""
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                # Check if target already exists
                check_query = """
                    SELECT id FROM aibesinsights_project_targets 
                    WHERE project_id = :project_id
                    AND target_type = :target_type 
                    AND target_year = :target_year 
                    AND (:target_month IS NULL OR target_month = :target_month)
                    AND (:target_week IS NULL OR target_week = :target_week)
                """
                
                params = {
                    "project_id": project_id,
                    "target_type": target_type,
                    "target_year": target_year,
                    "target_month": target_month,
                    "target_week": target_week
                }
                
                result = conn.execute(text(check_query), params)
                existing_record = result.fetchone()
                
                if existing_record:
                    # Update existing record
                    update_query = """
                        UPDATE aibesinsights_project_targets 
                        SET sales_target = :sales_target, stands_target = :stands_target, last_updated = CURRENT_TIMESTAMP
                        WHERE id = :id
                    """
                    conn.execute(text(update_query), {
                        "sales_target": sales_target,
                        "stands_target": stands_target,
                        "id": existing_record[0]
                    })
                else:
                    # Insert new record
                    insert_query = """
                        INSERT INTO aibesinsights_project_targets 
                        (project_id, target_type, target_year, target_month, target_week, sales_target, stands_target)
                        VALUES (:project_id, :target_type, :target_year, :target_month, :target_week, :sales_target, :stands_target)
                    """
                    conn.execute(text(insert_query), {
                        "project_id": project_id,
                        "target_type": target_type,
                        "target_year": target_year,
                        "target_month": target_month,
                        "target_week": target_week,
                        "sales_target": sales_target,
                        "stands_target": stands_target
                    })
                
                trans.commit()
                return True, f"Project {target_type} targets saved successfully"
            except Exception as e:
                trans.rollback()
                raise e
    except Exception as e:
        logger.error(f"Error saving project {target_type} targets: {e}")
        return False, f"Error saving project {target_type} targets: {str(e)}"

def get_company_settings(engine):
    """Get current company settings from database"""
    try:
        query = "SELECT company_name, logo_path, updated_date FROM aibesinsights_company_settings WHERE id = 1"
        result = pd.read_sql(query, engine)
        
        if not result.empty:
            row = result.iloc[0]
            return {
                'company_name': row['company_name'] or 'AIBES Real Estate',
                'logo_path': row['logo_path'],
                'updated_date': row['updated_date']
            }
        else:
            # Return defaults
            return {
                'company_name': 'AIBES Real Estate',
                'logo_path': None,
                'updated_date': None
            }
    except Exception as e:
        logger.error(f"Error getting company settings: {e}")
        return {
            'company_name': 'AIBES Real Estate',
            'logo_path': None,
            'updated_date': None
        }

def get_email_settings(engine):
    """Get current email settings from database"""
    try:
        query = """
        SELECT smtp_server, smtp_port, email_username, email_password, 
               sender_email, sender_name, updated_date 
        FROM aibesinsights_email_settings WHERE id = 1
        """
        result = pd.read_sql(query, engine)
        
        if not result.empty:
            row = result.iloc[0]
            return {
                'smtp_server': row['smtp_server'] or 'smtp.gmail.com',
                'smtp_port': row['smtp_port'] or 587,
                'email_username': row['email_username'],
                'email_password': row['email_password'],
                'sender_email': row['sender_email'],
                'sender_name': row['sender_name'] or 'AIBES Reports',
                'updated_date': row['updated_date']
            }
        else:
            # Return defaults
            return {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'email_username': None,
                'email_password': None,
                'sender_email': None,
                'sender_name': 'AIBES Reports',
                'updated_date': None
            }
    except Exception as e:
        logger.error(f"Error getting email settings: {e}")
        return {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email_username': None,
            'email_password': None,
            'sender_email': None,
            'sender_name': 'AIBES Reports',
            'updated_date': None
        }

def get_all_targets(engine):
    """Get all targets from database"""
    try:
        query = """
        SELECT target_type, target_year, target_month, target_week, sales_target, stands_target, last_updated
        FROM aibesinsights_targets
        ORDER BY target_type, target_year, target_month, target_week
        """
        result = pd.read_sql(query, engine)
        return result
    except Exception as e:
        logger.error(f"Error getting targets: {e}")
        return pd.DataFrame()

def get_all_project_targets(engine):
    """Get all project targets from database with project names"""
    try:
        query = """
        SELECT pt.project_id, p.name as project_name, pt.target_type, pt.target_year, 
               pt.target_month, pt.target_week, pt.sales_target, pt.stands_target, pt.last_updated
        FROM aibesinsights_project_targets pt
        LEFT JOIN Projects p ON pt.project_id = p.id
        ORDER BY pt.project_id, pt.target_type, pt.target_year, pt.target_month, pt.target_week
        """
        result = pd.read_sql(query, engine)
        return result
    except Exception as e:
        logger.error(f"Error getting project targets: {e}")
        return pd.DataFrame()

def get_projects_list(engine):
    """Get list of projects from database"""
    try:
        query = "SELECT id, name FROM Projects ORDER BY name"
        result = pd.read_sql(query, engine)
        return result
    except Exception as e:
        logger.error(f"Error getting projects list: {e}")
        return pd.DataFrame()

def save_logo_file(logo_data, filename):
    """Save uploaded logo to file system"""
    try:
        # Create logos directory in the application root
        app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logos_dir = os.path.join(app_root, "logos")
        if not os.path.exists(logos_dir):
            os.makedirs(logos_dir)
        
        # Create unique filename
        file_extension = os.path.splitext(filename)[1]
        unique_filename = f"logo_{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(logos_dir, unique_filename)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(logo_data)
        
        return file_path
    except Exception as e:
        logger.error(f"Error saving logo file: {e}")
        return None

# Callbacks for settings functionality
@callback(
    [Output('logo-upload-status', 'children'),
     Output('logo-preview-section', 'children')],
    Input('upload-logo', 'contents'),
    State('upload-logo', 'filename'),
    prevent_initial_call=True
)
def handle_logo_upload(contents, filename):
    """Handle logo upload and preview"""
    if contents is not None:
        try:
            # Parse the uploaded content
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            
            # Validate image
            try:
                img = Image.open(BytesIO(decoded))
                img.verify()
            except Exception:
                return [dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Invalid image file"
                ], color="danger"), None]
            
            # Create preview
            preview = html.Div([
                dbc.Card([
                    dbc.CardHeader("Logo Preview", className="fw-bold"),
                    dbc.CardBody([
                        html.Div([
                            html.Img(
                                src=contents,
                                style={'max-width': '200px', 'max-height': '100px'}
                            )
                        ], className="text-center"),
                        html.Small(f"File: {filename}", className="text-muted d-block text-center mt-2")
                    ])
                ], className="shadow-sm")
            ], className="mt-3")
            
            return [dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Logo ready for upload: {filename}"
            ], color="success"), preview]
            
        except Exception as e:
            return [dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Error processing logo: {str(e)}"
            ], color="danger"), None]
    
    return ["", None]

# Combined callback for loading current settings
@callback(
    [Output('company-name-input', 'value'),
     Output('smtp-server-input', 'value'),
     Output('smtp-port-input', 'value'),
     Output('email-username-input', 'value'),
     Output('sender-email-input', 'value'),
     Output('sender-name-input', 'value'),
     Output('current-settings-display', 'children'),
     Output('current-targets-display', 'children'),
     Output('project-target-project', 'options')],
    Input('targets-collapse', 'is_open')
)
def load_current_settings(is_open):
    """Load current settings into form fields when targets section is opened"""
    engine = get_db_engine()
    if not engine:
        error_display = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Database not connected. Please connect to a database first."
        ], color="warning")
        return ["", "", "", "", "", "", error_display, error_display, []]
    
    # Initialize settings tables if needed
    init_database_settings(engine)
    
    company_settings = get_company_settings(engine)
    email_settings = get_email_settings(engine)
    targets_display = get_targets_display(engine)
    
    # Get projects for dropdown
    projects_df = get_projects_list(engine)
    project_options = []
    if not projects_df.empty:
        for _, row in projects_df.iterrows():
            project_options.append({
                "label": row['name'],
                "value": row['id']
            })
    
    return [
        company_settings['company_name'],
        email_settings['smtp_server'],
        email_settings['smtp_port'],
        email_settings['email_username'],
        email_settings['sender_email'],
        email_settings['sender_name'],
        get_current_settings_display(engine),
        targets_display,
        project_options
    ]

@callback(
    [Output('current-settings-display', 'children', allow_duplicate=True),
     Output('current-targets-display', 'children', allow_duplicate=True)],
    [Input('save-company-settings-btn', 'n_clicks'),
     Input('save-email-settings-btn', 'n_clicks'),
     Input('save-yearly-targets-btn', 'n_clicks'),
     Input('save-monthly-targets-btn', 'n_clicks'),
     Input('save-weekly-targets-btn', 'n_clicks'),
     Input('save-project-targets-btn', 'n_clicks')],
    [State('company-name-input', 'value'),
     State('upload-logo', 'contents'),
     State('upload-logo', 'filename'),
     State('smtp-server-input', 'value'),
     State('smtp-port-input', 'value'),
     State('email-username-input', 'value'),
     State('email-password-input', 'value'),
     State('sender-email-input', 'value'),
     State('sender-name-input', 'value'),
     State('year-target-year', 'value'),
     State('year-sales-target', 'value'),
     State('year-stands-target', 'value'),
     State('month-target-year', 'value'),
     State('month-target-month', 'value'),
     State('month-sales-target', 'value'),
     State('month-stands-target', 'value'),
     State('week-target-year', 'value'),
     State('week-target-week', 'value'),
     State('week-sales-target', 'value'),
     State('week-stands-target', 'value'),
     State('project-target-project', 'value'),
     State('project-target-type', 'value'),
     State('project-target-year', 'value'),
     State('project-target-month-week', 'value'),
     State('project-sales-target', 'value'),
     State('project-stands-target', 'value')],
    prevent_initial_call=True
)
def save_settings(company_clicks, email_clicks, yearly_clicks, monthly_clicks, weekly_clicks, project_clicks,
                 company_name, logo_contents, logo_filename,
                 smtp_server, smtp_port, email_username, email_password, sender_email, sender_name,
                 year_target_year, year_sales_target, year_stands_target,
                 month_target_year, month_target_month, month_sales_target, month_stands_target,
                 week_target_year, week_target_week, week_sales_target, week_stands_target,
                 project_id, project_target_type, project_target_year, project_target_period, 
                 project_sales_target, project_stands_target):
    """Save either company, email, or target settings based on which button was clicked"""
    ctx = dash.callback_context
    if not ctx.triggered:
        engine = get_db_engine()
        if engine:
            return [get_current_settings_display(engine), get_targets_display(engine)]
        else:
            error_alert = dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Database not connected. Please connect to a database first."
            ], color="warning")
            return [error_alert, error_alert]
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    engine = get_db_engine()
    if not engine:
        error_alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Database not connected. Please connect to a database first."
        ], color="warning")
        return [error_alert, error_alert]
    
    # Initialize settings tables if needed
    init_database_settings(engine)
    
    if trigger_id == 'save-company-settings-btn':
        # Handle logo upload if provided
        logo_path = None
        
        if logo_contents and logo_filename:
            try:
                # Parse logo data
                content_type, content_string = logo_contents.split(',')
                logo_data = base64.b64decode(content_string)
                
                # Save logo file
                logo_path = save_logo_file(logo_data, logo_filename)
                if not logo_path:
                    error_alert = dbc.Alert([
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        "Error saving logo file"
                    ], color="danger")
                    return [error_alert, get_targets_display(engine)]
                
            except Exception as e:
                error_alert = dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Error processing logo: {str(e)}"
                ], color="danger")
                return [error_alert, get_targets_display(engine)]
        
        # Save company settings
        success, message = save_company_settings(engine, company_name, logo_path)
        
        alert = dbc.Alert([
            html.I(className="fas fa-check-circle me-2" if success else "fas fa-exclamation-triangle me-2"),
            message
        ], color="success" if success else "danger")
        
        return [alert, get_targets_display(engine)]
    
    elif trigger_id == 'save-email-settings-btn':
        # Save email settings
        success, message = save_email_settings(
            engine, smtp_server, smtp_port, email_username, email_password, sender_email, sender_name
        )
        
        alert = dbc.Alert([
            html.I(className="fas fa-check-circle me-2" if success else "fas fa-exclamation-triangle me-2"),
            message
        ], color="success" if success else "danger")
        
        return [alert, get_targets_display(engine)]
    
    elif trigger_id == 'save-yearly-targets-btn':
        # Save yearly targets
        success, message = save_target_settings(
            engine, 'yearly', year_target_year, None, None, year_sales_target, year_stands_target
        )
        
        alert = dbc.Alert([
            html.I(className="fas fa-check-circle me-2" if success else "fas fa-exclamation-triangle me-2"),
            message
        ], color="success" if success else "danger")
        
        return [get_current_settings_display(engine), alert]
    
    elif trigger_id == 'save-monthly-targets-btn':
        # Save monthly targets
        success, message = save_target_settings(
            engine, 'monthly', month_target_year, month_target_month, None, month_sales_target, month_stands_target
        )
        
        alert = dbc.Alert([
            html.I(className="fas fa-check-circle me-2" if success else "fas fa-exclamation-triangle me-2"),
            message
        ], color="success" if success else "danger")
        
        return [get_current_settings_display(engine), alert]
    
    elif trigger_id == 'save-weekly-targets-btn':
        # Save weekly targets
        success, message = save_target_settings(
            engine, 'weekly', week_target_year, None, week_target_week, week_sales_target, week_stands_target
        )
        
        alert = dbc.Alert([
            html.I(className="fas fa-check-circle me-2" if success else "fas fa-exclamation-triangle me-2"),
            message
        ], color="success" if success else "danger")
        
        return [get_current_settings_display(engine), alert]
    
    elif trigger_id == 'save-project-targets-btn':
        # Save project targets
        if not project_id:
            alert = dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Please select a project"
            ], color="warning")
            return [get_current_settings_display(engine), alert]
        
        # Determine target period based on target type
        target_month = None
        target_week = None
        if project_target_type == 'monthly':
            target_month = project_target_period
        elif project_target_type == 'weekly':
            target_week = project_target_period
        
        success, message = save_project_target_settings(
            engine, project_id, project_target_type, project_target_year, 
            target_month, target_week, project_sales_target, project_stands_target
        )
        
        alert = dbc.Alert([
            html.I(className="fas fa-check-circle me-2" if success else "fas fa-exclamation-triangle me-2"),
            message
        ], color="success" if success else "danger")
        
        return [get_current_settings_display(engine), alert]
    
    # Fallback case
    return [get_current_settings_display(engine), get_targets_display(engine)]

@callback(
    Output('test-email-status', 'children'),
    Input('send-test-email-btn', 'n_clicks'),
    State('test-email-input', 'value'),
    prevent_initial_call=True
)
def send_test_email(n_clicks, test_email):
    """Send a test email to verify settings"""
    if n_clicks and test_email:
        try:
            engine = get_db_engine()
            if not engine:
                return dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Database not connected. Please connect to a database first."
                ], color="warning")
            
            # Get email settings
            email_settings = get_email_settings(engine)
            
            if not email_settings['smtp_server'] or not email_settings['email_username']:
                return dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Email settings not configured. Please save email settings first."
                ], color="warning")
            
            # Try to send test email (this is a simplified example)
            # In a real implementation, you would use the actual email sending logic
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Test email functionality would send to {test_email}! (In a real implementation, this would actually send an email)"
            ], color="success")
        except Exception as e:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Failed to send test email: {str(e)}"
            ], color="danger")
    
    return no_update

@callback(
    Output('project-target-period-container', 'children'),
    Input('project-target-type', 'value')
)
def update_project_target_period_container(target_type):
    """Update the project target period dropdown based on target type"""
    if target_type == 'monthly':
        return dbc.Select(
            id="project-target-month-week",
            options=[
                {"label": "January", "value": 1},
                {"label": "February", "value": 2},
                {"label": "March", "value": 3},
                {"label": "April", "value": 4},
                {"label": "May", "value": 5},
                {"label": "June", "value": 6},
                {"label": "July", "value": 7},
                {"label": "August", "value": 8},
                {"label": "September", "value": 9},
                {"label": "October", "value": 10},
                {"label": "November", "value": 11},
                {"label": "December", "value": 12}
            ],
            value=pd.Timestamp.now().month
        )
    elif target_type == 'weekly':
        return dbc.Select(
            id="project-target-month-week",
            options=[{"label": f"Week {i}", "value": i} for i in range(1, 53)],
            value=pd.Timestamp.now().isocalendar()[1]
        )
    else:  # yearly
        return html.Div("N/A - Yearly targets don't require period selection")

def get_current_settings_display(engine):
    """Get current settings display component"""
    if not engine:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Database not connected. Please connect to a database first."
        ], color="warning")
    
    # Initialize settings tables if needed
    init_database_settings(engine)
    
    company_settings = get_company_settings(engine)
    email_settings = get_email_settings(engine)
    
    # Logo preview
    logo_preview = "No logo uploaded"
    if company_settings['logo_path'] and os.path.exists(company_settings['logo_path']):
        try:
            logo_filename = os.path.basename(company_settings['logo_path'])
            logo_preview = html.Img(
                src=f"/serve-logo/{logo_filename}",
                style={'max-width': '150px', 'max-height': '75px'}
            )
        except:
            logo_preview = "Logo file not found"
    elif company_settings['logo_path']:
        # If logo path exists but file not found, show path
        logo_preview = f"Logo path: {company_settings['logo_path']}"
    
    return dbc.Row([
        dbc.Col([
            html.H6("Company Settings", className="fw-bold mb-1"),
            html.P(f"Name: {company_settings['company_name']}", className="mb-1"),
            html.Div([html.Strong("Logo: "), logo_preview], className="mb-3"),
            html.Small(f"Last updated: {company_settings['updated_date'] or 'Never'}", className="text-muted d-block mb-3"),
        ], width=12, md=6),
        dbc.Col([
            html.H6("Email Settings", className="fw-bold mb-1"),
            html.P(f"SMTP Server: {email_settings['smtp_server']}:{email_settings['smtp_port']}", className="mb-1"),
            html.P(f"Username: {email_settings['email_username'] or 'Not set'}", className="mb-1"),
            html.P(f"Sender: {email_settings['sender_email']} ({email_settings['sender_name']})", className="mb-1"),
            html.Small(f"Last updated: {email_settings['updated_date'] or 'Never'}", className="text-muted d-block"),
        ], width=12, md=6),
    ])

def get_targets_display(engine):
    """Get current targets display component"""
    try:
        targets_df = get_all_targets(engine)
        project_targets_df = get_all_project_targets(engine)
        
        if targets_df.empty and project_targets_df.empty:
            return dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                "No targets have been set yet."
            ], color="info")
        
        # Group targets by type
        yearly_targets = targets_df[targets_df['target_type'] == 'yearly']
        monthly_targets = targets_df[targets_df['target_type'] == 'monthly']
        weekly_targets = targets_df[targets_df['target_type'] == 'weekly']
        
        # Group project targets by type
        project_yearly_targets = project_targets_df[project_targets_df['target_type'] == 'yearly']
        project_monthly_targets = project_targets_df[project_targets_df['target_type'] == 'monthly']
        project_weekly_targets = project_targets_df[project_targets_df['target_type'] == 'weekly']
        
        target_cards = []
        
        # Yearly targets card
        if not yearly_targets.empty or not project_yearly_targets.empty:
            yearly_rows = []
            
            # Overall yearly targets
            for _, row in yearly_targets.iterrows():
                yearly_rows.append(
                    html.Tr([
                        html.Td("Overall"),
                        html.Td(row['target_year']),
                        html.Td(f"${row['sales_target']:,.2f}" if row['sales_target'] else "Not set"),
                        html.Td(row['stands_target'] if row['stands_target'] else "Not set"),
                        html.Td(row['last_updated'].strftime('%Y-%m-%d') if row['last_updated'] else "Never")
                    ])
                )
            
            # Project yearly targets
            for _, row in project_yearly_targets.iterrows():
                yearly_rows.append(
                    html.Tr([
                        html.Td(f"Project: {row['project_name']}" if row['project_name'] else f"Project ID: {row['project_id']}"),
                        html.Td(row['target_year']),
                        html.Td(f"${row['sales_target']:,.2f}" if row['sales_target'] else "Not set"),
                        html.Td(row['stands_target'] if row['stands_target'] else "Not set"),
                        html.Td(row['last_updated'].strftime('%Y-%m-%d') if row['last_updated'] else "Never")
                    ])
                )
            
            target_cards.append(
                dbc.Card([
                    dbc.CardHeader(html.H6("Yearly Targets", className="mb-0")),
                    dbc.CardBody([
                        dbc.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th("Target For"),
                                    html.Th("Year"),
                                    html.Th("Sales Target"),
                                    html.Th("Stands Target"),
                                    html.Th("Last Updated")
                                ])
                            ]),
                            html.Tbody(yearly_rows)
                        ], striped=True, bordered=True, hover=True, responsive=True, size="sm")
                    ])
                ], className="mb-3")
            )
        
        # Monthly targets card
        if not monthly_targets.empty or not project_monthly_targets.empty:
            monthly_rows = []
            month_names = {
                1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
            }
            
            # Overall monthly targets
            for _, row in monthly_targets.iterrows():
                month_name = month_names.get(row['target_month'], f"Month {row['target_month']}")
                monthly_rows.append(
                    html.Tr([
                        html.Td("Overall"),
                        html.Td(f"{row['target_year']}-{month_name}"),
                        html.Td(f"${row['sales_target']:,.2f}" if row['sales_target'] else "Not set"),
                        html.Td(row['stands_target'] if row['stands_target'] else "Not set"),
                        html.Td(row['last_updated'].strftime('%Y-%m-%d') if row['last_updated'] else "Never")
                    ])
                )
            
            # Project monthly targets
            for _, row in project_monthly_targets.iterrows():
                month_name = month_names.get(row['target_month'], f"Month {row['target_month']}")
                monthly_rows.append(
                    html.Tr([
                        html.Td(f"Project: {row['project_name']}" if row['project_name'] else f"Project ID: {row['project_id']}"),
                        html.Td(f"{row['target_year']}-{month_name}"),
                        html.Td(f"${row['sales_target']:,.2f}" if row['sales_target'] else "Not set"),
                        html.Td(row['stands_target'] if row['stands_target'] else "Not set"),
                        html.Td(row['last_updated'].strftime('%Y-%m-%d') if row['last_updated'] else "Never")
                    ])
                )
            
            target_cards.append(
                dbc.Card([
                    dbc.CardHeader(html.H6("Monthly Targets", className="mb-0")),
                    dbc.CardBody([
                        dbc.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th("Target For"),
                                    html.Th("Period"),
                                    html.Th("Sales Target"),
                                    html.Th("Stands Target"),
                                    html.Th("Last Updated")
                                ])
                            ]),
                            html.Tbody(monthly_rows)
                        ], striped=True, bordered=True, hover=True, responsive=True, size="sm")
                    ])
                ], className="mb-3")
            )
        
        # Weekly targets card
        if not weekly_targets.empty or not project_weekly_targets.empty:
            weekly_rows = []
            
            # Overall weekly targets
            for _, row in weekly_targets.iterrows():
                weekly_rows.append(
                    html.Tr([
                        html.Td("Overall"),
                        html.Td(f"{row['target_year']}-W{row['target_week']}"),
                        html.Td(f"${row['sales_target']:,.2f}" if row['sales_target'] else "Not set"),
                        html.Td(row['stands_target'] if row['stands_target'] else "Not set"),
                        html.Td(row['last_updated'].strftime('%Y-%m-%d') if row['last_updated'] else "Never")
                    ])
                )
            
            # Project weekly targets
            for _, row in project_weekly_targets.iterrows():
                weekly_rows.append(
                    html.Tr([
                        html.Td(f"Project: {row['project_name']}" if row['project_name'] else f"Project ID: {row['project_id']}"),
                        html.Td(f"{row['target_year']}-W{row['target_week']}"),
                        html.Td(f"${row['sales_target']:,.2f}" if row['sales_target'] else "Not set"),
                        html.Td(row['stands_target'] if row['stands_target'] else "Not set"),
                        html.Td(row['last_updated'].strftime('%Y-%m-%d') if row['last_updated'] else "Never")
                    ])
                )
            
            target_cards.append(
                dbc.Card([
                    dbc.CardHeader(html.H6("Weekly Targets", className="mb-0")),
                    dbc.CardBody([
                        dbc.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th("Target For"),
                                    html.Th("Period"),
                                    html.Th("Sales Target"),
                                    html.Th("Stands Target"),
                                    html.Th("Last Updated")
                                ])
                            ]),
                            html.Tbody(weekly_rows)
                        ], striped=True, bordered=True, hover=True, responsive=True, size="sm")
                    ])
                ], className="mb-3")
            )
        
        if not target_cards:
            return dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                "No targets have been set yet."
            ], color="info")
        
        return html.Div(target_cards)
        
    except Exception as e:
        logger.error(f"Error displaying targets: {e}")
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error loading targets: {str(e)}"
        ], color="danger")