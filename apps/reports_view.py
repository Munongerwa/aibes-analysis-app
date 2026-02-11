import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, callback, no_update, State, ctx, ALL
from flask import session
import os
import json
from .reports import get_report_generator
import datetime
import dash
from dateutil.relativedelta import relativedelta


layout = html.Div([
    dbc.Container([
        # Report generation layout 
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-file-pdf me-2"),
                        "Generate New Report"
                    ], className="fw-bold"),
                    dbc.CardBody([
                        dbc.Form([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Report Type", className="fw-bold"),
                                    dcc.Dropdown(
                                        id="report-type-dropdown",
                                        options=[
                                            {"label": "Daily", "value": "daily"},
                                            {"label": "Weekly", "value": "weekly"},
                                            {"label": "Monthly", "value": "monthly"},
                                            {"label": "Yearly", "value": "yearly"},
                                            {"label": "Custom Range", "value": "custom"}
                                        ],
                                        value="weekly",
                                        className="mb-3"
                                    ),
                                ], width=12, md=4),
                                
                                dbc.Col([
                                    dbc.Label("Start Date", className="fw-bold"),
                                    dcc.DatePickerSingle(
                                        id="report-start-date",
                                        date=datetime.date.today() - datetime.timedelta(days=7),
                                        className="mb-3 w-100"
                                    ),
                                ], width=12, md=4),
                                
                                dbc.Col([
                                    dbc.Label("End Date", className="fw-bold"),
                                    dcc.DatePickerSingle(
                                        id="report-end-date",
                                        date=datetime.date.today(),
                                        className="mb-3 w-100"
                                    ),
                                ], width=12, md=4),
                            ]),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button([
                                        html.I(className="fas fa-file-pdf me-2"),
                                        "Generate Report"
                                    ], id="generate-custom-report-btn", color="success", size="lg", className="w-100 mb-2"),
                                ], width=12, md=4),
                                dbc.Col([
                                    dbc.Button([
                                        html.I(className="fas fa-sync me-2"),
                                        "Refresh Reports"
                                    ], id="refresh-reports-btn", color="primary", size="lg", className="w-100 mb-2"),
                                ], width=12, md=4),
                            ], className="mt-3"),
                        ])
                    ])
                ], className="shadow-sm mb-4"),
            ], width=12)
        ]),
        
        # Status messages
        html.Div(id="generate-report-status", className="mb-3"),
        
        #Filter area
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-filter me-2"),
                        "Filter Reports"
                    ], className="fw-bold"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Search Reports", className="fw-bold"),
                                dbc.Input(
                                    id="reports-search-input",
                                    type="text",
                                    placeholder="Search by filename or report type...",
                                    className="mb-2"
                                ),
                            ], width=12, md=4),
                            dbc.Col([
                                dbc.Label("Report Type Filter", className="fw-bold"),
                                dcc.Dropdown(
                                    id="reports-type-filter",
                                    options=[
                                        {"label": "All Types", "value": "all"},
                                        {"label": "Daily", "value": "daily"},
                                        {"label": "Weekly", "value": "weekly"},
                                        {"label": "Monthly", "value": "monthly"},
                                        {"label": "Yearly", "value": "yearly"},
                                        {"label": "Custom", "value": "custom"}
                                    ],
                                    value="all",
                                    className="mb-2"
                                ),
                            ], width=12, md=3),
                            dbc.Col([
                                dbc.Label("Date Range", className="fw-bold"),
                                dcc.DatePickerRange(
                                    id="reports-date-range",
                                    start_date=datetime.date.today() - datetime.timedelta(days=30),
                                    end_date=datetime.date.today(),
                                    className="mb-2 w-100"
                                ),
                            ], width=12, md=5),
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-times-circle me-2"),
                                    "Clear Filters"
                                ], id="clear-filters-btn", color="secondary", size="sm"),
                            ], width="auto", className="ms-auto"),
                        ], className="mt-2"),
                    ])
                ], className="shadow-sm mb-4"),
            ], width=12)
        ]),
        
        # Deleting report confirmation Modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle([
                html.I(className="fas fa-trash-alt me-2"),
                "Confirm Delete"
            ])),
            dbc.ModalBody([
                html.Div(id="delete-modal-content"),
                html.P("This action cannot be undone.", className="text-danger fw-bold mt-2"),
            ]),
            dbc.ModalFooter([
                dbc.Button([
                    html.I(className="fas fa-trash-alt me-2"),
                    "Delete Report"
                ], id="confirm-delete-btn", color="danger"),
                dbc.Button("Cancel", id="cancel-delete-btn", color="secondary"),
            ])
        ], id="delete-modal", centered=True),
        
        # Preview modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle([
                html.I(className="fas fa-file-pdf me-2"),
                html.Span(id="preview-modal-title", children="Report Preview")
            ]), close_button=True),
            dbc.ModalBody([
                html.Div(id="report-preview-content", children=[
                    html.P("Select a report to preview", className="text-muted text-center")
                ])
            ]),
            dbc.ModalFooter([
                html.Div([
                    dbc.Button("Close", id="preview-close-btn", color="secondary"),
                ], className="w-100 text-end")
            ])
        ], id="preview-modal", size="xl", backdrop="static"),
        
        # Hidden divs to store current filenames
        html.Div(id="current-delete-filename", style={"display": "none"}),
        html.Div(id="current-preview-filename", style={"display": "none"}),
        
        # Reports list section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-history me-2"),
                        "Generated Reports"
                    ], className="fw-bold"),
                    dbc.CardBody([
                        html.Div(id="reports-table-container"),
                    ])
                ], className="shadow-sm")
            ], width=12)
        ], className="mb-4"),
        
    ], className="mt-4", fluid=True)
], className="bg-light min-vh-100 py-4")

def generate_reports_table(reports, search_term="", report_type_filter="all", 
                          start_date=None, end_date=None):
    """Generate the reports table with filtering"""
    if not reports:
        return dbc.Alert("No reports found.", color="info")
    
    # filters application
    filtered_reports = []
    for report in reports:
        try:
            # Parse dates
            report_start_date = datetime.datetime.strptime(report['start_date'], '%Y-%m-%d').date()
            report_end_date = datetime.datetime.strptime(report['end_date'], '%Y-%m-%d').date()
            generated_date = datetime.datetime.strptime(report['date'], '%Y-%m-%d %H:%M:%S')
            
            # Search filter
            if search_term:
                search_lower = search_term.lower()
                if (search_lower not in report['filename'].lower() and 
                    search_lower not in report['report_type'].lower()):
                    continue
            
            # Type filter
            if report_type_filter != "all" and report['report_type'] != report_type_filter:
                continue
            
            # Date range filter
            if start_date and end_date:
                #validating the start date vs the end date
                if not (start_date <= generated_date.date() <= end_date):
                    continue
            
            filtered_reports.append(report)
        except Exception as e:
            print(f"Error processing report {report.get('filename', 'unknown')}: {e}")
            continue
    
    if not filtered_reports:
        return dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "No reports match the current filters."
        ], color="info")
    
    # organizing reports by generated date (latest first)
    sorted_reports = sorted(filtered_reports, 
                           key=lambda x: datetime.datetime.strptime(x['date'], '%Y-%m-%d %H:%M:%S'),
                           reverse=True)
    
    #table header
    table_header = [
        html.Thead([
            html.Tr([
                html.Th("Report Name", style={"width": "30%"}),
                html.Th("Type", style={"width": "15%"}),
                html.Th("Period", style={"width": "25%"}),
                html.Th("Generated Date", style={"width": "15%"}),
                html.Th("Actions", style={"width": "15%"})
            ])
        ])
    ]
    
    #table rows
    rows = []
    for report in sorted_reports:
        try:
            #dates
            start_date_parsed = datetime.datetime.strptime(report['start_date'], '%Y-%m-%d').date()
            end_date_parsed = datetime.datetime.strptime(report['end_date'], '%Y-%m-%d').date()
            generated_date = datetime.datetime.strptime(report['date'], '%Y-%m-%d %H:%M:%S')
            
            row = html.Tr([
                html.Td(html.Strong(report['filename'])),
                html.Td(report['report_type'].title(), className="text-center"),
                html.Td(f"{start_date_parsed.strftime('%Y-%m-%d')} to {end_date_parsed.strftime('%Y-%m-%d')}"),
                html.Td(generated_date.strftime('%Y-%m-%d'), className="text-center"),
                html.Td([
                    dbc.ButtonGroup([
                        dbc.Button([
                            html.I(className="fas fa-eye me-1"),
                        ], 
                        id={"type": "preview-report", "index": report['filename']},
                        size="sm",
                        color="primary",
                        title="Preview"),
                        dbc.Button([
                            html.I(className="fas fa-trash me-1"),
                        ], 
                        id={"type": "delete-report", "index": report['filename']},
                        size="sm",
                        color="danger",
                        title="Delete")
                    ], size="sm")
                ])
            ])
            rows.append(row)
        except Exception as e:
            print(f"Error processing report {report.get('filename', 'unknown')}: {e}")
            continue
    
    if not rows:
        return dbc.Alert("No valid reports found.", color="warning")
    
    table_body = [html.Tbody(rows)]
    table = dbc.Table(table_header + table_body, bordered=True, hover=True, responsive=True, striped=True)
    
    return table

@callback(
    Output("reports-table-container", "children"),
    [Input("refresh-reports-btn", "n_clicks"),
     Input("reports-search-input", "value"),
     Input("reports-type-filter", "value"),
     Input("reports-date-range", "start_date"),
     Input("reports-date-range", "end_date")],
    prevent_initial_call=False
)
def refresh_reports(n_clicks, search_term, report_type_filter, start_date_str, end_date_str):
    """Refresh and display reports with filtering"""
    try:
        # Parse date strings to date objects
        start_date = None
        end_date = None
        if start_date_str:
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        generator = get_report_generator()
        if not generator and session.get('db_connection_string'):
            from .reports import initialize_report_generator
            generator = initialize_report_generator(session['db_connection_string'])
        
        if generator:
            reports = generator.get_generated_reports()
            return generate_reports_table(reports, search_term, report_type_filter, start_date, end_date)
        else:
            return dbc.Alert("Reports system not initialized. Please connect to database first.", color="warning")
    except Exception as e:
        return dbc.Alert(f"Error loading reports: {str(e)}", color="danger")

# Callback to clear filters
@callback(
    [Output("reports-search-input", "value"),
     Output("reports-type-filter", "value"),
     Output("reports-date-range", "start_date"),
     Output("reports-date-range", "end_date")],
    Input("clear-filters-btn", "n_clicks"),
    prevent_initial_call=True
)
def clear_filters(n_clicks):
    """Clear all filters"""
    return "", "all", datetime.date.today() - datetime.timedelta(days=30), datetime.date.today()

# Callback to update date pickers based on report type
@callback(
    [Output("report-start-date", "date"),
     Output("report-end-date", "date")],
    Input("report-type-dropdown", "value"),
    prevent_initial_call=False
)
def update_date_range(report_type):
    end_date = datetime.date.today()
    
    if report_type == "daily":
        start_date = end_date
    elif report_type == "weekly":
        start_date = end_date - datetime.timedelta(days=7)
    elif report_type == "monthly":
        start_date = end_date - relativedelta(months=1)
    elif report_type == "yearly":
        start_date = end_date - relativedelta(years=1)
    else:  # custom
        start_date = end_date - datetime.timedelta(days=7)
    
    return start_date, end_date

@callback(
    Output("generate-report-status", "children"),
    Input("generate-custom-report-btn", "n_clicks"),
    [State("report-type-dropdown", "value"),
     State("report-start-date", "date"),
     State("report-end-date", "date")],
    prevent_initial_call=True
)
def generate_custom_report(n_clicks, report_type, start_date_str, end_date_str):
    """Generate a report for custom date range"""
    if n_clicks is None:
        return no_update
    
    try:
        #dates
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        #validate date range
        if start_date > end_date:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Start date cannot be after end date."
            ], color="danger")
        
        #date range limiting so as to prevent excessive data processing
        if (end_date - start_date).days > 365:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Maximum date range is 365 days."
            ], color="warning")
        
        generator = get_report_generator()
        if not generator and session.get('db_connection_string'):
            from .reports import initialize_report_generator
            generator = initialize_report_generator(session['db_connection_string'])
        
        if generator:
            #report generation
            filepath = generator.generate_pdf_report(start_date, end_date, report_type)
            
            if filepath:
                filename = os.path.basename(filepath)
                return dbc.Alert([
                    html.I(className="fas fa-check-circle me-2"),
                    f"Report generated successfully: {filename}"
                ], color="success")
            else:
                return dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Failed to generate report. Please check the logs."
                ], color="warning")
        else:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Reports system not initialized. Please connect to database first."
            ], color="danger")
    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error generating report: {str(e)}"
        ], color="danger")

# Store selected filenames when buttons are clicked
@callback(
    Output("current-delete-filename", "children"),
    Input({"type": "delete-report", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def store_delete_filename(n_clicks):
    """Store the filename for delete action"""
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return no_update
    
    # Find which button was clicked
    for trigger in ctx.triggered:
        if 'delete-report' in trigger['prop_id'] and '.n_clicks' in trigger['prop_id']:
            prop_id = trigger['prop_id'].replace('.n_clicks', '')
            if prop_id.startswith('{'):
                triggered_dict = json.loads(prop_id)
                filename = triggered_dict.get('index')
                return filename
            else:
                return prop_id
    
    return no_update

@callback(
    Output("current-preview-filename", "children"),
    Input({"type": "preview-report", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def store_preview_filename(n_clicks):
    """Store the filename for preview action"""
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return no_update
    
    # Find which button was clicked
    for trigger in ctx.triggered:
        if 'preview-report' in trigger['prop_id'] and '.n_clicks' in trigger['prop_id']:
            prop_id = trigger['prop_id'].replace('.n_clicks', '')
            if prop_id.startswith('{'):
                triggered_dict = json.loads(prop_id)
                filename = triggered_dict.get('index')
                return filename
            else:
                return prop_id
    
    return no_update

# Modal controller
@callback(
    [Output("delete-modal", "is_open"),
     Output("preview-modal", "is_open")],
    [Input({"type": "delete-report", "index": ALL}, "n_clicks"),
     Input({"type": "preview-report", "index": ALL}, "n_clicks"),
     Input("cancel-delete-btn", "n_clicks"),
     Input("preview-close-btn", "n_clicks"),
     Input("confirm-delete-btn", "n_clicks")],
    prevent_initial_call=True
)
def control_modals(*args):
    """Control modal states"""
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return False, False
    
    triggered_id = ctx.triggered[0]['prop_id']
    
    # Handle opening modals
    if 'delete-report' in triggered_id:
        return True, False
    elif 'preview-report' in triggered_id:
        return False, True
    # Handle closing modals
    elif 'cancel-delete-btn' in triggered_id or 'preview-close-btn' in triggered_id:
        return False, False
    elif 'confirm-delete-btn' in triggered_id:
        # After confirming delete, close delete modal
        return False, False
    else:
        return False, False

# Populate delete modal content
@callback(
    Output("delete-modal-content", "children"),
    Input("current-delete-filename", "children"),
    prevent_initial_call=False
)
def populate_delete_modal(filename):
    """Populate delete modal content"""
    if not filename or filename == no_update:
        return no_update
    
    content = html.Div([
        html.P([
            html.Strong("Are you sure you want to delete this report?"),
            html.Br(),
            html.Code(filename, className="text-danger")
        ])
    ])
    return content

# Populate preview modal content
@callback(
    Output("report-preview-content", "children"),
    Input("current-preview-filename", "children"),
    prevent_initial_call=False
)
def populate_preview_modal(filename):
    """Populate preview modal content"""
    if not filename or filename == no_update:
        return no_update
    
    # Check if file exists
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_reports")
    file_path = os.path.join(reports_dir, filename)
    
    if os.path.exists(file_path):
        # Create preview content with embedded PDF viewer
        preview_content = html.Div([
            html.H5([
                html.I(className="fas fa-file-pdf me-2"),
                f"Report: {filename}"
            ], className="mb-3 text-center"),
            
            # Embedded PDF viewer
            html.Div([
                html.Iframe(
                    src=f"/generated_reports/{filename}",
                    style={
                        "width": "100%",
                        "height": "600px",
                        "border": "1px solid #ddd",
                        "borderRadius": "4px"
                    },
                    title="PDF Preview"
                )
            ], className="mb-3"),
            
            html.P([
                html.Strong("Note: "),
                "If the PDF doesn't display properly, right-click and select 'Save As...' to download the file."
            ], className="small text-muted text-center")
        ])
        return preview_content
    else:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Report file '{filename}' not found on server."
        ], color="danger")

@callback(
    [Output("generate-report-status", "children", allow_duplicate=True),
     Output("refresh-reports-btn", "n_clicks", allow_duplicate=True),
     Output("preview-modal", "is_open", allow_duplicate=True)],  # Close preview modal after delete
    Input("confirm-delete-btn", "n_clicks"),
    State("current-delete-filename", "children"),
    prevent_initial_call=True
)
def delete_report(confirm_clicks, filename):
    """Delete selected report and close preview modal"""
    if not ctx.triggered or confirm_clicks is None:
        return no_update, no_update, no_update
    
    try:
        if filename and filename != no_update:
            generator = get_report_generator()
            if generator:
                success, message = generator.delete_report(filename)
                if success:
                    # Trigger refresh and close preview modal
                    return dbc.Alert([
                        html.I(className="fas fa-check-circle me-2"),
                        f"Report '{filename}' deleted successfully!"
                    ], color="success"), 1, False
                else:
                    return dbc.Alert([
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        f"Failed to delete report: {message}"
                    ], color="danger"), no_update, no_update
            else:
                return dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Reports system not initialized"
                ], color="danger"), no_update, no_update
        else:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Could not determine which report to delete"
            ], color="danger"), no_update, no_update
            
    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error deleting report: {str(e)}"
        ], color="danger"), no_update, no_update