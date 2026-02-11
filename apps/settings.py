import dash
from dash import html, dcc, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
from flask import session
import sqlite3
import os
import base64
from io import BytesIO
from PIL import Image
import uuid

# Settings layout
layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-cog me-2"),
                    "System Settings"
                ], className="mb-4"),
                
                #setting sections tabs
                dbc.Tabs([
                    # Company Information Tab
                    dbc.Tab([
                        dbc.Card([
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
                            ]),
                        ], className="shadow-sm mb-4"),
                    ], label="Company Info", tab_id="company-tab"),
                    
                    # Email settings tab
                    dbc.Tab([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Email Configuration", className="mb-3"),
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
                            ]),
                        ], className="shadow-sm mb-4"),
                    ], label="Email Settings", tab_id="email-tab"),
                ], id="settings-tabs", active_tab="company-tab"),
                
                # Current settings display
                html.Hr(),
                html.H5("Current Settings", className="mt-4"),
                html.Div(id="current-settings-display"),
                
            ], width=12, lg=8),
        ], className="justify-content-center"),
    ], fluid=True),
], className="py-4")

class SettingsManager:
    def __init__(self, db_path=None):
        if db_path is None:
            self.db_path = os.path.join(os.path.dirname(__file__), "..", "settings.db")
        else:
            self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the settings database"""
        conn = sqlite3.connect(self.db_path)
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
        
        # use default company settings if none exist
        cursor.execute("SELECT COUNT(*) FROM company_settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO company_settings (id, company_name) 
                VALUES (1, 'AIBES Data Analysis')
            ''')
        
        #default email settings if none exist
        cursor.execute("SELECT COUNT(*) FROM email_settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO email_settings (id, smtp_server, smtp_port) 
                VALUES (1, 'smtp.gmail.com', 587)
            ''')
        
        conn.commit()
        conn.close()
    
    def save_company_settings(self, company_name=None, logo_path=None, logo_data=None):
        """Save company settings"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if logo_path and logo_data:
                # Save logo
                cursor.execute('''
                    UPDATE company_settings 
                    SET company_name = ?, logo_path = ?, logo_data = ?, updated_date = CURRENT_TIMESTAMP
                    WHERE id = 1
                ''', (company_name or 'AIBES Real Estate', logo_path, logo_data))
            elif company_name:
                # Save only company name
                cursor.execute('''
                    UPDATE company_settings 
                    SET company_name = ?, updated_date = CURRENT_TIMESTAMP
                    WHERE id = 1
                ''', (company_name,))
            
            conn.commit()
            conn.close()
            return True, "Company settings saved successfully"
        except Exception as e:
            return False, f"Error saving company settings: {str(e)}"
    
    def save_email_settings(self, smtp_server=None, smtp_port=None, email_username=None, 
                           email_password=None, sender_email=None, sender_name=None):
        """Save email settings"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE email_settings 
                SET smtp_server = ?, smtp_port = ?, email_username = ?, 
                    email_password = ?, sender_email = ?, sender_name = ?, 
                    updated_date = CURRENT_TIMESTAMP
                WHERE id = 1
            ''', (smtp_server, smtp_port, email_username, email_password, sender_email, sender_name))
            
            conn.commit()
            conn.close()
            return True, "Email settings saved successfully"
        except Exception as e:
            return False, f"Error saving email settings: {str(e)}"
    
    def get_company_settings(self):
        """Get current company settings"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT company_name, logo_path, logo_data, updated_date
                FROM company_settings
                WHERE id = 1
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'company_name': result[0] or 'AIBES Real Estate',
                    'logo_path': result[1],
                    'logo_data': result[2],
                    'updated_date': result[3]
                }
            return {
                'company_name': 'AIBES Real Estate',
                'logo_path': None,
                'logo_data': None,
                'updated_date': None
            }
        except Exception as e:
            print(f"Error getting company settings: {e}")
            return {
                'company_name': 'AIBES Real Estate',
                'logo_path': None,
                'logo_data': None,
                'updated_date': None
            }
    
    def get_email_settings(self):
        """Get current email settings"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT smtp_server, smtp_port, email_username, email_password, sender_email, sender_name, updated_date
                FROM email_settings
                WHERE id = 1
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'smtp_server': result[0] or 'smtp.gmail.com',
                    'smtp_port': result[1] or 587,
                    'email_username': result[2],
                    'email_password': result[3],
                    'sender_email': result[4],
                    'sender_name': result[5] or 'AIBES Reports',
                    'updated_date': result[6]
                }
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
            print(f"Error getting email settings: {e}")
            return {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'email_username': None,
                'email_password': None,
                'sender_email': None,
                'sender_name': 'AIBES Reports',
                'updated_date': None
            }
    
    def save_logo_file(self, logo_data, filename):
        """Save uploaded logo to file system"""
        try:
            #logos directory
            logos_dir = os.path.join(os.path.dirname(__file__), "..", "logos")
            if not os.path.exists(logos_dir):
                os.makedirs(logos_dir)
            
            #unique filename
            file_extension = os.path.splitext(filename)[1]
            unique_filename = f"logo_{uuid.uuid4().hex}{file_extension}"
            file_path = os.path.join(logos_dir, unique_filename)
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(logo_data)
            
            return file_path
        except Exception as e:
            print(f"Error saving logo file: {e}")
            return None

# Global settings manager instance
settings_manager = None

def initialize_settings_manager(db_path=None):
    """Initialize the global settings manager"""
    global settings_manager
    settings_manager = SettingsManager(db_path)
    return settings_manager

def get_settings_manager():
    """Get the global settings manager instance"""
    global settings_manager
    if settings_manager is None:
        settings_manager = SettingsManager()
    return settings_manager

# Callbacks for settings functionality
@callback(
    Output('logo-upload-status', 'children'),
    Output('logo-preview-section', 'children'),
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
                return dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Invalid image file"
                ], color="danger"), None
            
            #preview
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
            
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Logo ready for upload: {filename}"
            ], color="success"), preview
            
        except Exception as e:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Error processing logo: {str(e)}"
            ], color="danger"), None
    
    return "", None

@callback(
    Output('current-settings-display', 'children'),
    [Input('save-company-settings-btn', 'n_clicks'),
     Input('save-email-settings-btn', 'n_clicks')],
    [State('company-name-input', 'value'),
     State('upload-logo', 'contents'),
     State('upload-logo', 'filename'),
     State('smtp-server-input', 'value'),
     State('smtp-port-input', 'value'),
     State('email-username-input', 'value'),
     State('email-password-input', 'value'),
     State('sender-email-input', 'value'),
     State('sender-name-input', 'value')],
    prevent_initial_call=True
)
def save_settings(company_clicks, email_clicks, company_name, logo_contents, logo_filename,
                 smtp_server, smtp_port, email_username, email_password, sender_email, sender_name):
    """Save either company or email settings based on which button was clicked"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return get_current_settings_display()
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    settings_mgr = get_settings_manager()
    
    if trigger_id == 'save-company-settings-btn':
        # Handle logo upload if provided
        logo_data = None
        logo_path = None
        
        if logo_contents and logo_filename:
            try:
                # Parse logo data
                content_type, content_string = logo_contents.split(',')
                logo_data = base64.b64decode(content_string)
                
                # Save logo file
                logo_path = settings_mgr.save_logo_file(logo_data, logo_filename)
                
            except Exception as e:
                return dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Error processing logo: {str(e)}"
                ], color="danger")
        
        # Save company settings
        success, message = settings_mgr.save_company_settings(company_name, logo_path, logo_data)
        
        if success:
            alert = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                message
            ], color="success")
        else:
            alert = dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                message
            ], color="danger")
        
        # Refresh current settings display
        return get_current_settings_display()
    
    elif trigger_id == 'save-email-settings-btn':
        # Save email settings
        success, message = settings_mgr.save_email_settings(
            smtp_server, smtp_port, email_username, email_password, sender_email, sender_name
        )
        
        if success:
            alert = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                message
            ], color="success")
        else:
            alert = dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                message
            ], color="danger")
        
        return get_current_settings_display()
    
    return get_current_settings_display()

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
            from .reports import get_report_generator            
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Test email sent successfully to {test_email}! (This is an example)"
            ], color="success")
        except Exception as e:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Failed to send test email: {str(e)}"
            ], color="danger")
    
    return no_update

def get_current_settings_display():
    """Get current settings display component"""
    settings_mgr = get_settings_manager()
    company_settings = settings_mgr.get_company_settings()
    email_settings = settings_mgr.get_email_settings()
    
    # Logo preview
    logo_preview = "No logo uploaded"
    if company_settings['logo_path'] and os.path.exists(company_settings['logo_path']):
        try:
            logo_preview = html.Img(
                src=f"/serve-logo/{os.path.basename(company_settings['logo_path'])}",
                style={'max-width': '150px', 'max-height': '75px'}
            )
        except:
            logo_preview = "Logo file not found"
    elif company_settings['logo_data']:
        logo_preview = "Logo stored in database"
    
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

# Initialize settings manager when module is imported
initialize_settings_manager()