# report_view.py
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, callback, no_update, State, ctx, ALL
from flask import session
import os
import json
import logging
from .reports import get_report_generator
import datetime
import dash

from dateutil.relativedelta import relativedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple layout without sidebar/appbar - these will be added by app.py
layout = html.Div([
    # Loading wrapper for main content
    dcc.Loading(
        id="loading-main",
        type="default",
        children=[
            html.Div([
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
                                        ], width=12, md=6),
                                        dbc.Col([
                                            dbc.Button([
                                                html.I(className="fas fa-sync me-2"),
                                                "Refresh Reports"
                                            ], id="refresh-reports-btn", color="primary", size="lg", className="w-100 mb-2"),
                                        ], width=12, md=6),
                                    ], className="mt-3"),
                                ])
                            ],style={"minHeight": "390px", "paddingBottom": "20px"})
                        ], className="shadow-sm mb-4"),
                    ], width=12)
                ]),
                
                # Status messages
                html.Div(id="generate-report-status", className="mb-3"),
                
                # Filter area
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
                        ], style={"minHeight": "500px"})
                    ]),
                    dbc.ModalFooter([
                        html.Div([
                            dbc.Button("Close", id="preview-close-btn", color="secondary"),
                        ], className="w-100 text-end")
                    ])
                ], id="preview-modal", size="xl", backdrop="static", fullscreen=True),
                
                # Reports list section
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.I(className="fas fa-history me-2"),
                                "Generated Reports"
                            ], className="fw-bold"),
                            dbc.CardBody([
                                html.Div(id="reports-table-container", style={"minHeight": "400px"}),
                            ])
                        ], className="shadow-sm")
                    ], width=12)
                ], className="mb-4"),
            ])
        ]
    ),
    
    # Hidden divs to store current filenames
    html.Div(id="current-delete-filename", style={"display": "none"}),
    html.Div(id="current-preview-filename", style={"display": "none"}),
    # Store to track which button was clicked
    dcc.Store(id="triggered-button-store", data=None),
], className="g-0")


def generate_reports_table(reports, search_term="", report_type_filter="all", 
                          start_date=None, end_date=None):
    """Generate the reports table with filtering"""
    if not reports:
        return dbc.Alert("No reports found.", color="info")
    
    # filters application
    filtered_reports = []
    for report in reports:
        try:
            # Parse dates safely using fromisoformat (Python ≥3.7)
            generated_date_str = report['date'].split()[0]  # e.g., "2023-10-05 14:30:22"
            generated_date = datetime.date.fromisoformat(generated_date_str)
            
            report_start_date = datetime.date.fromisoformat(report['start_date'])
            report_end_date = datetime.date.fromisoformat(report['end_date'])
            
            # Search filter
            if search_term:
                search_lower = search_term.lower()
                if (search_lower not in report['filename'].lower() and 
                    search_lower not in report['report_type'].lower()):
                    continue
            
            # Type filter
            if report_type_filter != "all" and report['report_type'] != report_type_filter:
                continue
            
            # Date range filter (filter by generated date)
            if start_date and end_date:
                if not (start_date <= generated_date <= end_date):
                    continue
            
            filtered_reports.append(report)
        except Exception as e:
            logger.warning(f"Error processing report {report.get('filename', 'unknown')}: {e}")
            continue
    
    if not filtered_reports:
        return dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "No reports match the current filters."
        ], color="info")
    
    # organizing reports by generated date (latest first)
    sorted_reports = sorted(filtered_reports, 
                           key=lambda x: datetime.date.fromisoformat(x['date'].split()[0]),
                           reverse=True)
    
    # table header
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
    
    # table rows
    rows = []
    for report in sorted_reports:
        try:
            generated_date_str = report['date'].split()[0]
            generated_date = datetime.date.fromisoformat(generated_date_str)
            start_date_parsed = datetime.date.fromisoformat(report['start_date'])
            end_date_parsed = datetime.date.fromisoformat(report['end_date'])
            
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
                            html.I(className="fas fa-download me-1"),
                        ], 
                        id={"type": "download-report", "index": report['filename']},
                        size="sm",
                        color="success",
                        title="Download",
                        href=f"/generated_reports/{report['filename']}",
                        download=True),
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
            logger.warning(f"Error building row for report {report.get('filename', 'unknown')}: {e}")
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
        # Parse date strings to date objects safely
        start_date = None
        end_date = None
        if start_date_str:
            start_date = datetime.date.fromisoformat(start_date_str)
        if end_date_str:
            end_date = datetime.date.fromisoformat(end_date_str)
        
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
        logger.error(f"Error in refresh_reports: {e}")
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
    [Output("generate-report-status", "children", allow_duplicate=True),
     Output("reports-table-container", "children", allow_duplicate=True)],
    Input("generate-custom-report-btn", "n_clicks"),
    [State("report-type-dropdown", "value"),
     State("report-start-date", "date"),
     State("report-end-date", "date")],
    prevent_initial_call=True
)
def generate_custom_report(n_clicks, report_type, start_date_str, end_date_str):
    """Generate a report for custom date range"""
    if n_clicks is None:
        return no_update, no_update
    
    try:
        # Parse dates safely
        start_date = datetime.date.fromisoformat(start_date_str)
        end_date = datetime.date.fromisoformat(end_date_str)
        
        # Validate date range
        if start_date > end_date:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Start date cannot be after end date."
            ], color="danger"), no_update
        
        # Limit date range
        if (end_date - start_date).days > 365:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Maximum date range is 365 days."
            ], color="warning"), no_update
        
        generator = get_report_generator()
        if not generator and session.get('db_connection_string'):
            from .reports import initialize_report_generator
            generator = initialize_report_generator(session['db_connection_string'])
        
        if generator:
            # Generate report
            filepath = generator.generate_pdf_report(start_date, end_date, report_type)
            
            if filepath:
                filename = os.path.basename(filepath)
                # Fetch updated reports list to display the newly generated report
                reports = generator.get_generated_reports()
                return (
                    dbc.Alert([
                        html.I(className="fas fa-check-circle me-2"),
                        f"Report generated successfully: {filename}"
                    ], color="success"),
                    generate_reports_table(reports)
                )
            else:
                return (
                    dbc.Alert([
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        "Failed to generate report. Please check the logs."
                    ], color="warning"),
                    no_update
                )
        else:
            return (
                dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Reports system not initialized. Please connect to database first."
                ], color="danger"),
                no_update
            )
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return (
            dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Error generating report: {str(e)}"
            ], color="danger"),
            no_update
        )


# Store selected filenames when buttons are clicked (improved robustness)
@callback(
    [Output("current-delete-filename", "children"),
     Output("triggered-button-store", "data")],
    Input({"type": "delete-report", "index": ALL}, "n_clicks"),
    State({"type": "delete-report", "index": ALL}, "id"),
    prevent_initial_call=True
)
def store_delete_filename(n_clicks, ids):
    """Store the filename for delete action and track which button was clicked"""
    ctx = dash.callback_context

    if not ctx.triggered:
        return no_update, no_update

    # Find first clicked button
    for i, click in enumerate(n_clicks):
        if click and click > 0:
            return ids[i]['index'], ids[i]  # Store both filename and button id

    return no_update, no_update


@callback(
    [Output("current-preview-filename", "children"),
     Output("triggered-button-store", "data", allow_duplicate=True)],
    Input({"type": "preview-report", "index": ALL}, "n_clicks"),
    State({"type": "preview-report", "index": ALL}, "id"),
    prevent_initial_call=True
)
def store_preview_filename(n_clicks, ids):
    """Store the filename for preview action and track which button was clicked"""
    ctx = dash.callback_context

    if not ctx.triggered:
        return no_update, no_update

    # Find first clicked button
    for i, click in enumerate(n_clicks):
        if click and click > 0:
            return ids[i]['index'], ids[i]  # Store both filename and button id

    return no_update, no_update


# MODAL CONTROLS: SEPARATED FOR SAFETY
# Delete Modal
@callback(
    Output("delete-modal", "is_open"),
    [Input("triggered-button-store", "data"),
     Input("cancel-delete-btn", "n_clicks"),
     Input("confirm-delete-btn", "n_clicks")],
    prevent_initial_call=True
)
def control_delete_modal(triggered_button, cancel_clicks, confirm_clicks):
    """Control delete modal state based on specific button click"""
    ctx = dash.callback_context

    if not ctx.triggered:
        return False

    triggered_id = ctx.triggered[0]['prop_id']

    if 'triggered-button-store' in triggered_id:
        # Check if the triggered button was a delete button
        if triggered_button and triggered_button.get('type') == 'delete-report':
            return True
    elif 'cancel-delete-btn' in triggered_id or 'confirm-delete-btn' in triggered_id:
        return False

    return False


# Preview Modal
@callback(
    Output("preview-modal", "is_open"),
    [Input("triggered-button-store", "data"),
     Input("preview-close-btn", "n_clicks")],
    prevent_initial_call=True
)
def control_preview_modal(triggered_button, close_clicks):
    """Control preview modal state based on specific button click"""
    ctx = dash.callback_context

    if not ctx.triggered:
        return False

    triggered_id = ctx.triggered[0]['prop_id']

    if 'triggered-button-store' in triggered_id:
        # Check if the triggered button was a preview button
        if triggered_button and triggered_button.get('type') == 'preview-report':
            return True
    elif 'preview-close-btn' in triggered_id:
        return False

    return False


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
    
    return html.Div([
        html.P([
            html.Strong("Are you sure you want to delete this report?"),
            html.Br(),
            html.Code(filename, className="text-danger")
        ])
    ])


# Populate preview modal content (with security)
@callback(
    [Output("report-preview-content", "children"),
     Output("preview-modal-title", "children")],
    Input("current-preview-filename", "children"),
    prevent_initial_call=True
)
def populate_preview_modal(filename):
    """Populate preview modal content with path traversal protection"""
    if not filename or filename == no_update:
        return no_update, no_update
    
    # Sanitize filename (prevent path traversal)
    safe_filename = os.path.basename(filename)
    
    # Construct safe absolute path
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_reports")
    file_path = os.path.abspath(os.path.join(reports_dir, safe_filename))
    
    # Verify file is inside reports_dir
    if not file_path.startswith(os.path.abspath(reports_dir)):
        logger.warning(f"Invalid file path attempted: {filename}")
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Invalid file path."
        ], color="danger"), "Error"
    
    if os.path.exists(file_path):
        # Create preview content
        preview_content = html.Div([
            html.H5([
                html.I(className="fas fa-file-pdf me-2"),
                f"Report: {safe_filename}"
            ], className="mb-3 text-center"),
            
            # Embedded PDF viewer
            html.Div([
                html.Embed(
                    src=f"/generated_reports/{safe_filename}",
                    type="application/pdf",
                    style={
                        "width": "100%",
                        "height": "70vh",
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
        return preview_content, f"Report Preview: {safe_filename}"
    else:
        logger.error(f"Report file not found: {safe_filename}")
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Report file '{safe_filename}' not found on server."
        ], color="danger"), "Report Preview"


@callback(
    [Output("generate-report-status", "children"),
     Output("reports-table-container", "children", allow_duplicate=True),  # ← ADD THIS
     Output("preview-modal", "is_open", allow_duplicate=True)],  # also safe to add here
    Input("confirm-delete-btn", "n_clicks"),
    State("current-delete-filename", "children"),
    prevent_initial_call=True
)
def delete_report(confirm_clicks, filename):
    if not ctx.triggered or confirm_clicks is None:
        return no_update, no_update, no_update
    
    try:
        if filename and filename != no_update:
            generator = get_report_generator()
            if generator:
                success, message = generator.delete_report(filename)
                if success:
                    # Fetch updated reports list
                    reports = generator.get_generated_reports()
                    return (
                        dbc.Alert([
                            html.I(className="fas fa-check-circle me-2"),
                            f"Report '{filename}' deleted successfully!"
                        ], color="success"),
                        generate_reports_table(reports),
                        False  # Close preview modal
                    )
                else:
                    return (
                        dbc.Alert([
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            f"Failed to delete report: {message}"
                        ], color="danger"),
                        no_update,
                        no_update
                    )
            else:
                return (
                    dbc.Alert([
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        "Reports system not initialized"
                    ], color="danger"),
                    no_update,
                    no_update
                )
        else:
            return (
                dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Could not determine which report to delete"
                ], color="danger"),
                no_update,
                no_update
            )
            
    except Exception as e:
        logger.error(f"Error deleting report: {e}")
        return (
            dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Error deleting report: {str(e)}"
            ], color="danger"),
            no_update,
            no_update
        )