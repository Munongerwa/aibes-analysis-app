# dashboard.py
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, callback, State, ctx, no_update, dash_table
from flask import session
import pandas as pd
import datetime
import json
import numpy as np
import plotly.graph_objs as go
import io
import base64
import dash

# Conditional ML import
try:
    from sklearn.linear_model import LinearRegression
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# Function to get user-specific database engine
def get_user_db_engine():
    if 'db_connection_string' in session and session['db_connection_string']:
        try:
            from sqlalchemy import create_engine
            engine = create_engine(session['db_connection_string'])
            return engine
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    return None

# Function to create forecast data
def create_forecast(df_monthly, months_ahead=3):
    if df_monthly.empty or len(df_monthly) < 2:
        return pd.DataFrame(columns=['month', 'total_stands_sold', 'type'])
    
    try:
        if ML_AVAILABLE:
            df_monthly = df_monthly.sort_values('month')
            X = np.array(df_monthly['month']).reshape(-1, 1)
            y = df_monthly['total_stands_sold'].values
            
            if len(y) < 2 or np.all(y == 0):
                return simple_forecast(df_monthly, months_ahead)
            
            model = LinearRegression()
            model.fit(X, y)
            
            last_month = df_monthly['month'].max()
            future_months = [last_month + i for i in range(1, months_ahead + 1)]
            future_X = np.array(future_months).reshape(-1, 1)
            predictions = model.predict(future_X)
            predictions = np.maximum(predictions, 0)
            
            forecast_df = pd.DataFrame({
                'month': future_months,
                'total_stands_sold': predictions,
                'type': 'forecast'
            })
        else:
            return simple_forecast(df_monthly, months_ahead)
            
        df_monthly['type'] = 'actual'
        result_df = pd.concat([df_monthly[['month', 'total_stands_sold', 'type']], forecast_df], ignore_index=True)
        return result_df
    except Exception as e:
        print(f"Forecast error: {e}")
        return simple_forecast(df_monthly, months_ahead)

def simple_forecast(df_monthly, months_ahead=3):
    if df_monthly.empty:
        return pd.DataFrame(columns=['month', 'total_stands_sold', 'type'])
    
    df_monthly = df_monthly.sort_values('month')
    recent_data = df_monthly['total_stands_sold'].tail(min(3, len(df_monthly)))
    avg_value = recent_data.mean() if not recent_data.empty else 0
    
    last_month = df_monthly['month'].max()
    
    forecast_data = []
    for i in range(1, months_ahead + 1):
        forecast_data.append({
            'month': last_month + i,
            'total_stands_sold': max(0, avg_value),
            'type': 'forecast'
        })
    
    df_monthly['type'] = 'actual'
    result_df = pd.concat([df_monthly[['month', 'total_stands_sold', 'type']], 
                          pd.DataFrame(forecast_data)], ignore_index=True)
    return result_df

def create_simple_yoy_indicator(change_percent, previous_value):
    """Create a financial dashboard style YoY indicator with trend line and arrow"""
    
    # Handle edge cases
    if previous_value == 0:
        if change_percent == 0:
            return html.Div([
                html.Div([
                    html.I(className="fas fa-minus me-1", style={"color": "#6c757d", "fontSize": "12px"}),
                ], style={"display": "inline-block", "width": "20px", "textAlign": "center"}),
                html.Span("No change", className="small", style={"color": "#6c757d", "marginLeft": "8px"})
            ], className="d-flex align-items-center justify-content-center")
        else:
            # For infinite growth, show upward arrow
            return html.Div([
                html.Div([
                    html.I(className="fas fa-arrow-trend-up me-1", style={"color": "#28a745", "fontSize": "14px"}),
                ], style={"display": "inline-block", "width": "20px", "textAlign": "center"}),
                html.Span(f"+∞% (Prev: 0)", className="small", style={"color": "#28a745", "marginLeft": "8px"})
            ], className="d-flex align-items-center justify-content-center")
    
    # Normal case
    if change_percent > 0:
        # Positive growth - green up arrow
        return html.Div([
            html.Div([
                html.I(className="fas fa-arrow-trend-up me-1", style={"color": "#28a745", "fontSize": "35px"}),
            ], style={"display": "inline-block", "width": "20px", "textAlign": "center"}),
            html.Span(f"+{change_percent:.1f}% (Prev: {previous_value:,.0f})", 
                     className="small", style={"color": "#28a745", "marginLeft": "30px"})
        ], className="d-flex align-items-center justify-content-center")
    elif change_percent < 0:
        # Negative growth - red down arrow
        return html.Div([
            html.Div([
                html.I(className="fas fa-arrow-trend-down me-1", style={"color": "#dc3545", "fontSize": "35px"}),
            ], style={"display": "inline-block", "width": "20px", "textAlign": "center"}),
            html.Span(f"{change_percent:.1f}% (Prev: {previous_value:,.0f})", 
                     className="small", style={"color": "#dc3545", "marginLeft": "30px"})
        ], className="d-flex align-items-center justify-content-center")
    else:
        # No change - gray horizontal arrow
        return html.Div([
            html.Div([
                html.I(className="fas fa-minus me-1", style={"color": "#6c757d", "fontSize": "12px"}),
            ], style={"display": "inline-block", "width": "20px", "textAlign": "center"}),
            html.Span("0% (No change)", className="small", style={"color": "#6c757d", "marginLeft": "8px"})
        ], className="d-flex align-items-center justify-content-center")

# Function to create download link for CSV
def parse_contents(df):
    """Convert dataframe to CSV download link"""
    if df is None or df.empty:
        return None
    
    csv_string = df.to_csv(index=False, encoding='utf-8')
    csv_bytes = csv_string.encode('utf-8')
    b64 = base64.b64encode(csv_bytes).decode()
    href = f"data:text/csv;base64,{b64}"
    return href

# Function to create card header with view toggle controls and download button
def create_card_header(title, graph_id):
    return dbc.CardHeader([
        html.Div([
            html.Span(title, className="fw-bold me-2"),
            html.Div([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-chart-line")
                    ], id=f"{graph_id}-line-btn", color="light", size="sm", className="btn-sm"),
                    dbc.Button([
                        html.I(className="fas fa-chart-bar")
                    ], id=f"{graph_id}-bar-btn", color="light", size="sm", className="btn-sm"),
                    dbc.Button([
                        html.I(className="fas fa-table")
                    ], id=f"{graph_id}-table-btn", color="light", size="sm", className="btn-sm"),
                ], size="sm"),
                html.A(
                    dbc.Button([
                        html.I(className="fas fa-download me-1"),
                        "CSV"
                    ], size="sm", color="primary", className="btn-sm ms-2"),
                    id=f"{graph_id}-download-link",
                    href="",
                    download=f"{graph_id}_data.csv",
                    style={"display": "none"}
                ),
                dcc.Store(id=f"{graph_id}-view-type", data="line"),
                dcc.Store(id=f"{graph_id}-table-data", data="")
            ], className="ms-auto d-flex align-items-center")
        ], className="d-flex align-items-center")
    ], className="fw-bold")

def create_card_header_with_toggle(title, graph_id):
    return dbc.CardHeader([
        html.Div([
            html.Span(title, className="fw-bold me-2"),
            html.Div([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-chart-pie")
                    ], id=f"{graph_id}-pie-btn", color="light", size="sm", className="btn-sm"),
                    dbc.Button([
                        html.I(className="fas fa-chart-bar")
                    ], id=f"{graph_id}-bar-btn", color="light", size="sm", className="btn-sm"),
                    dbc.Button([
                        html.I(className="fas fa-table")
                    ], id=f"{graph_id}-table-btn", color="light", size="sm", className="btn-sm"),
                ], size="sm"),
                html.A(
                    dbc.Button([
                        html.I(className="fas fa-download me-1"),
                        "CSV"
                    ], size="sm", color="primary", className="btn-sm ms-2"),
                    id=f"{graph_id}-download-link",
                    href="",
                    download=f"{graph_id}_data.csv",
                    style={"display": "none"}
                ),
                dcc.Store(id=f"{graph_id}-view-type", data="pie"),
                dcc.Store(id=f"{graph_id}-table-data", data="")
            ], className="ms-auto d-flex align-items-center")
        ], className="d-flex align-items-center")
    ], className="fw-bold")

# Main layout with proper spacing for sidebar
layout = html.Div([
    # Hidden div for logout trigger
    html.Div(id="logout-trigger", style={"display": "none"}),
    
    # Main content area (already has marginLeft for sidebar)
    html.Div([
        # storing report data
        html.Div(id="report-data-store", style={"display": "none"}),
        
        # Main content with reduced top padding
        dbc.Container([
            # Header row with title and filter button
            dbc.Row([
                dbc.Col([
                    html.H2([
                        html.I(className="fas fa-tachometer-alt me-2"),
                        "Quick Insights"
                    ], className="mb-0"),
                ], width=9, className="d-flex align-items-center"),
                
                # Filter button on the right
                dbc.Col([
                    html.Div([
                        dbc.Button([
                            html.I(className="fas fa-filter me-1"),
                        ], id="filter-toggle-btn", color="primary", size="sm", className="btn-sm"),
                    ], className="d-flex align-items-center justify-content-end")
                ], width=3, className="d-flex align-items-center justify-content-end"),
            ], className="g-2 align-items-center py-2 border-bottom mb-3"),
            
            # Dropdown filter section
            dbc.Row([
                dbc.Col([
                    dbc.Collapse([
                        dbc.Card([
                            dbc.CardBody([
                                dbc.Row([
                                    # Time Range Filter
                                    dbc.Col([
                                        html.Div([
                                            html.Small([
                                                html.I(className="fas fa-clock me-1"),
                                                "Time Range"
                                            ], className="text-muted mb-1 d-block fw-bold"),
                                            dcc.RadioItems(
                                                id="time-filter-radio",
                                                options=[
                                                    {"label": "Today", "value": "daily"},
                                                    {"label": "Last 7 Days", "value": "weekly"},
                                                    {"label": "This Year", "value": "yearly"}
                                                ] + ([{"label": "Forecast", "value": "forecast"}] if ML_AVAILABLE else []),
                                                value="yearly",
                                                inline=True,
                                                className="modern-radio-group",
                                                inputClassName="me-1",
                                                labelClassName="d-inline-block me-2 mb-1"
                                            )
                                        ], style={"flex": "1"})
                                    ], width=12, lg=6, className="mb-3 mb-lg-0"),
                                    
                                    # Year Filter
                                    dbc.Col([
                                        html.Div([
                                            html.Small([
                                                html.I(className="fas fa-calendar-alt me-1"),
                                                "Select Year"
                                            ], className="text-muted mb-1 d-block fw-bold"),
                                            dcc.Dropdown(
                                                id="year-dropdown",
                                                options=[
                                                    {'label': str(year), 'value': year} 
                                                    for year in range(datetime.datetime.now().year, datetime.datetime.now().year - 5, -1)
                                                ],
                                                value=datetime.datetime.now().year,
                                                clearable=False,
                                                className="modern-dropdown",
                                            )
                                        ], id="year-filter-container", style={"display": "inline-block", "width": "150px"})
                                    ], width=12, lg=3, className="mb-3 mb-lg-0"),
                                ], className="g-3 align-items-end")
                            ], style={"minHeight": "300px", "paddingBottom": "20px"})
                        ], className="shadow-sm mb-5 h-100")
                    ], id="filter-collapse", is_open=False, style={"zIndex": "1000"})
                ], width=12, className="h-100", style={"position": "relative"})
            ], className="mb-3"),
            
            # KPI Cards Row
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Div([
                                    html.I(className="fas fa-dollar-sign fa-lg text-success"),
                                ], className="justify-content-center mb-2"),
                                html.H6("Total Stand Value", className="card-title text-center mb-1", style={"font-size": "15px"}),
                                html.H4(id="total-stand-value", children="$0", className="text-center text-success fw-bold mb-1,", style={"font-size": "15px"}),
                                html.Small(id="stand-value-period", children="Period: --", className="text-center text-muted d-block", style={"font-size": "15px"}),
                                html.Div(id="stand-value-yoy", className="text-center mt-1", style={"font-size": "15px"})
                            ], className="text-center")
                        ])
                    ], className="shadow-lg h-100", style={"borderLeft": "20px solid #0F3559"})
                ], width=12, md=6, lg=3, className="mb-3"),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Div([
                                    html.I(className="fas fa-house fa-lg text-warning", style={"font-size": "15px"}),
                                ], className="d-flex justify-content-center mb-2", style={"font-size": "15px"}),
                                html.H6("Stands Sold", className="card-title text-center mb-1 text-warning", style={"font-size": "15px"}),
                                html.H4(id="stands-sold-value", children="0", className="text-center fw-bold mb-1", style={"font-size": "15px"}),
                                html.Small(id="stands-sold-period", children="Period: --", className="text-center text-muted d-block", style={"font-size": "15px"}),
                                html.Div(id="stands-sold-yoy", className="text-center mt-1 fw-bold", style={"font-size": "15px"})
                            ], className="text-center")
                        ])
                    ], className="shadow-lg h-100", style={"borderLeft": "20px solid #0F3559"}),
                ], width=12, md=6, lg=3, className="mb-3"),

                # Stands Available for Sale
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Div([
                                    html.I(className="fas fa-tags fa-lg text-info"),
                                ], className="d-flex justify-content-center mb-2"),
                                html.H6("Available Stands", className="card-title text-center mb-1",style={"font-size": "15px"}),
                                html.H4(id="stands-available-value", children="0", className="text-center text-info fw-bold mb-1", style={"font-size": "15px"}),
                                html.Small(id="stands-available-period", children="Period: --", className="text-center text-muted d-block", style={"font-size": "15px"}),
                                html.Div(id="stands-available-yoy", className="text-center mt-1 fw-bold", style={"font-size": "15px"})
                            ], className="text-center")
                        ])
                    ], className="shadow-lg h-100", style={"borderLeft": "20px solid #0F3559"})
                ], width=12, md=6, lg=3, className="mb-3"),

                # reserved stands
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Div([
                                    html.I(className="fas fa-lock fa-lg text-warning"),
                                ], className="d-flex justify-content-center mb-2"),
                                html.H6("Reserved Stands", className="card-title text-center mb-1 text-warning", style={"font-size": "15px"}),
                                html.H4(id="stands-reserved-value", children="0", className="text-center fw-bold mb-1", style={"font-size": "15px"}),
                                html.Small(id="stands-reserved-period", children="Period: --", className="text-center text-muted d-block", style={"font-size": "15px"}),
                                html.Div(id="stands-reserved-yoy", className="text-center mt-1 fw-bold", style={"font-size": "15px"})
                            ], className="text-center")
                        ])
                    ], className="shadow-lg h-100", style={"borderLeft": "20px solid #0F3559"})
                ], width=12, md=6, lg=3, className="mb-3"),
            ], className="mb-4"),
                
            # Manual Report Status
            html.Div(id="manual-report-status", className="mb-3"),
            
            # Graphs Row
            dbc.Row([
                # Pie chart with toggle controls
                dbc.Col([
                    dbc.Card([
                        create_card_header([html.I(className="fas fa-chart-pie me-2"), "Payment Distribution"], "deposits-installments"),
                        dbc.CardBody([
                            html.Div(id="deposits-installments-content")
                        ])
                    ], className="shadow-lg h-100")
                ], width=12, lg=4, className="mb-4"),
                # Area Chart with toggle controls
                dbc.Col([
                    dbc.Card([
                        create_card_header([html.I(className="fas fa-chart-line me-2"), html.Span(id="chart-title")], "stands-sold"),
                        dbc.CardBody([
                            html.Div(id="stands-sold-content")
                        ])
                    ], className="shadow-lg h-100")
                ], width=12, lg=8, className="mb-4")
            ], className="g-4"),
            
            # Project Performance and Sales by Agent Side by Side
            dbc.Row([
                # Project Performance Bar Chart with toggle controls
                dbc.Col([
                    dbc.Card([
                        create_card_header([html.I(className="fas fa-chart-bar me-2"), "Project Performance - Stands Sold"], "project-performance"),
                        dbc.CardBody([
                            html.Div(id="project-performance-content")
                        ])
                    ], className="shadow-lg h-100")
                ], width=12, lg=6, className="mb-4"),
                
                # Sales by Agent Chart with toggle controls
                dbc.Col([
                    dbc.Card([
                        create_card_header_with_toggle([html.I(className="fas fa-user-tie me-2"), "Sales by Agent"], "dashboard-agent-sales"),
                        dbc.CardBody([
                            html.Div(id="dashboard-agent-sales-content")
                        ])
                    ], className="shadow-lg h-100")
                ], width=12, lg=6, className="mb-4")
            ], className="g-4"),
            
            # Project Comparison Line Chart with toggle controls
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        create_card_header([html.I(className="fas fa-chart-line me-2"), "Project Stands Sold Comparison"], "project-comparison"),
                        dbc.CardBody([
                            html.Div(id="project-comparison-content")
                        ])
                    ], className="shadow-lg mb-4")
                ], width=12)
            ], className="g-4"),
        ], className="mt-2", fluid=True, style={"paddingTop": "20px"})  # Significantly reduced padding
    ], className="bg-light py-1", id="main-content")
], )

# Callback to toggle filter section
@callback(
    Output("filter-collapse", "is_open"),
    Input("filter-toggle-btn", "n_clicks"),
    State("filter-collapse", "is_open"),
    prevent_initial_call=False
)
def toggle_filter_collapse(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

# Callback to control dropdown visibility
@callback(
    Output("year-filter-container", "style"),
    Input("time-filter-radio", "value")
)
def toggle_year_filter(time_filter):
    base_style = {"display": "inline-block", "width": "150px"}
    if time_filter in ["yearly", "forecast"]:
        return base_style
    return {"display": "none"}

# Callback to update chart title
@callback(
    Output("chart-title", "children"),
    Input("time-filter-radio", "value"),
    Input("year-dropdown", "value")
)
def update_chart_title(time_filter, selected_year):
    title_map = {
        "daily": "Hourly Stands Sales Trend",
        "weekly": "Daily Stands Sales Trend (Last 7 Days)",
        "yearly": f"Monthly Stands Sales Trend ({selected_year})",
        "forecast": f"Monthly Forecast for {selected_year}" if ML_AVAILABLE else f"Monthly Trend ({selected_year})"
    }
    return title_map.get(time_filter, "Stands Sales Trend")

# Callbacks for Deposits/Installments chart view toggles
@callback(
    [Output("deposits-installments-line-btn", "outline"),
     Output("deposits-installments-bar-btn", "outline"),
     Output("deposits-installments-download-link", "style")],
    [Input("deposits-installments-line-btn", "n_clicks"),
     Input("deposits-installments-bar-btn", "n_clicks"),
     Input("deposits-installments-table-btn", "n_clicks")],
    State("deposits-installments-view-type", "data")
)
def update_deposits_buttons(line_clicks, bar_clicks, table_clicks, current_view):
    triggered_id = ctx.triggered_id if ctx.triggered_id else None
    
    if triggered_id is None:
        download_style = {"display": "none"} if current_view != "table" else {"display": "inline-block"}
        return [True, False, download_style]
    
    if "line" in triggered_id:
        return [False, True, {"display": "none"}]
    elif "bar" in triggered_id:
        return [True, False, {"display": "none"}]
    else:
        return [True, True, {"display": "inline-block"}]

@callback(
    Output("deposits-installments-view-type", "data"),
    Input("deposits-installments-line-btn", "n_clicks"),
    Input("deposits-installments-bar-btn", "n_clicks"),
    Input("deposits-installments-table-btn", "n_clicks")
)
def update_deposits_view_type(line_clicks, bar_clicks, table_clicks):
    triggered_id = ctx.triggered_id if ctx.triggered_id else None
    
    if triggered_id is None:
        return "pie"
    
    if "line" in triggered_id:
        return "pie"
    elif "bar" in triggered_id:
        return "bar"
    else:
        return "table"

# Callbacks for Stands Sold chart view toggles
@callback(
    [Output("stands-sold-line-btn", "outline"),
     Output("stands-sold-bar-btn", "outline"),
     Output("stands-sold-download-link", "style")],
    [Input("stands-sold-line-btn", "n_clicks"),
     Input("stands-sold-bar-btn", "n_clicks"),
     Input("stands-sold-table-btn", "n_clicks")],
    State("stands-sold-view-type", "data")
)
def update_stands_buttons(line_clicks, bar_clicks, table_clicks, current_view):
    triggered_id = ctx.triggered_id if ctx.triggered_id else None
    
    if triggered_id is None:
        download_style = {"display": "none"} if current_view != "table" else {"display": "inline-block"}
        return [True, False, download_style]
    
    if "line" in triggered_id:
        return [False, True, {"display": "none"}]
    elif "bar" in triggered_id:
        return [True, False, {"display": "none"}]
    else:
        return [True, True, {"display": "inline-block"}]

@callback(
    Output("stands-sold-view-type", "data"),
    Input("stands-sold-line-btn", "n_clicks"),
    Input("stands-sold-bar-btn", "n_clicks"),
    Input("stands-sold-table-btn", "n_clicks")
)
def update_stands_view_type(line_clicks, bar_clicks, table_clicks):
    triggered_id = ctx.triggered_id if ctx.triggered_id else None
    
    if triggered_id is None:
        return "line"
    
    if "line" in triggered_id:
        return "line"
    elif "bar" in triggered_id:
        return "bar"
    else:
        return "table"

# Callbacks for Project Performance chart view toggles
@callback(
    [Output("project-performance-line-btn", "outline"),
     Output("project-performance-bar-btn", "outline"),
     Output("project-performance-download-link", "style")],
    [Input("project-performance-line-btn", "n_clicks"),
     Input("project-performance-bar-btn", "n_clicks"),
     Input("project-performance-table-btn", "n_clicks")],
    State("project-performance-view-type", "data")
)
def update_project_buttons(line_clicks, bar_clicks, table_clicks, current_view):
    triggered_id = ctx.triggered_id if ctx.triggered_id else None
    
    if triggered_id is None:
        download_style = {"display": "none"} if current_view != "table" else {"display": "inline-block"}
        return [True, False, download_style]
    
    if "line" in triggered_id:
        return [True, False, {"display": "none"}]
    elif "bar" in triggered_id:
        return [False, True, {"display": "none"}]
    else:
        return [True, True, {"display": "inline-block"}]

@callback(
    Output("project-performance-view-type", "data"),
    Input("project-performance-line-btn", "n_clicks"),
    Input("project-performance-bar-btn", "n_clicks"),
    Input("project-performance-table-btn", "n_clicks")
)
def update_project_view_type(line_clicks, bar_clicks, table_clicks):
    triggered_id = ctx.triggered_id if ctx.triggered_id else None
    
    if triggered_id is None:
        return "bar"
    
    if "line" in triggered_id:
        return "line"
    elif "bar" in triggered_id:
        return "bar"
    else:
        return "table"

# Callbacks for Sales by Agent chart view toggles (UNIQUE NAMES)
@callback(
    [Output("dashboard-agent-sales-pie-btn", "outline"),
     Output("dashboard-agent-sales-bar-btn", "outline"),
     Output("dashboard-agent-sales-download-link", "style")],
    [Input("dashboard-agent-sales-pie-btn", "n_clicks"),
     Input("dashboard-agent-sales-bar-btn", "n_clicks"),
     Input("dashboard-agent-sales-table-btn", "n_clicks")],
    State("dashboard-agent-sales-view-type", "data")
)
def update_dashboard_agent_buttons(pie_clicks, bar_clicks, table_clicks, current_view):
    triggered_id = ctx.triggered_id if ctx.triggered_id else None
    
    if triggered_id is None:
        download_style = {"display": "none"} if current_view != "table" else {"display": "inline-block"}
        return [True, False, download_style]
    
    if "pie" in triggered_id:
        return [False, True, {"display": "none"}]
    elif "bar" in triggered_id:
        return [True, False, {"display": "none"}]
    else:
        return [True, True, {"display": "inline-block"}]

@callback(
    Output("dashboard-agent-sales-view-type", "data"),
    Input("dashboard-agent-sales-pie-btn", "n_clicks"),
    Input("dashboard-agent-sales-bar-btn", "n_clicks"),
    Input("dashboard-agent-sales-table-btn", "n_clicks")
)
def update_dashboard_agent_view_type(pie_clicks, bar_clicks, table_clicks):
    triggered_id = ctx.triggered_id if ctx.triggered_id else None
    
    if triggered_id is None:
        return "pie"
    
    if "pie" in triggered_id:
        return "pie"
    elif "bar" in triggered_id:
        return "bar"
    else:
        return "table"

# Callbacks for Project Comparison chart view toggles (UNIQUE NAMES)
@callback(
    [Output("project-comparison-line-btn", "outline"),
     Output("project-comparison-bar-btn", "outline"),
     Output("project-comparison-download-link", "style")],
    [Input("project-comparison-line-btn", "n_clicks"),
     Input("project-comparison-bar-btn", "n_clicks"),
     Input("project-comparison-table-btn", "n_clicks")],
    State("project-comparison-view-type", "data")
)
def update_project_comparison_buttons(line_clicks, bar_clicks, table_clicks, current_view):
    triggered_id = ctx.triggered_id if ctx.triggered_id else None
    
    if triggered_id is None:
        download_style = {"display": "none"} if current_view != "table" else {"display": "inline-block"}
        return [False, True, download_style]  # Line is default (not outlined)
    
    if "line" in triggered_id:
        return [False, True, {"display": "none"}]
    elif "bar" in triggered_id:
        return [True, False, {"display": "none"}]
    else:
        return [True, True, {"display": "inline-block"}]

@callback(
    Output("project-comparison-view-type", "data"),
    Input("project-comparison-line-btn", "n_clicks"),
    Input("project-comparison-bar-btn", "n_clicks"),
    Input("project-comparison-table-btn", "n_clicks")
)
def update_project_comparison_view_type(line_clicks, bar_clicks, table_clicks):
    triggered_id = ctx.triggered_id if ctx.triggered_id else None
    
    if triggered_id is None:
        return "line"
    
    if "line" in triggered_id:
        return "line"
    elif "bar" in triggered_id:
        return "bar"
    else:
        return "table"

# Download callbacks for each chart
@callback(
    Output("deposits-installments-download-link", "href"),
    Input("deposits-installments-table-data", "data")
)
def update_deposits_download_link(table_data):
    if not table_data:
        return ""
    try:
        df = pd.read_json(table_data, orient='split')
        return parse_contents(df)
    except:
        return ""

@callback(
    Output("stands-sold-download-link", "href"),
    Input("stands-sold-table-data", "data")
)
def update_stands_download_link(table_data):
    if not table_data:
        return ""
    try:
        df = pd.read_json(table_data, orient='split')
        return parse_contents(df)
    except:
        return ""

@callback(
    Output("project-performance-download-link", "href"),
    Input("project-performance-table-data", "data")
)
def update_project_download_link(table_data):
    if not table_data:
        return ""
    try:
        df = pd.read_json(table_data, orient='split')
        return parse_contents(df)
    except:
        return ""

# Download callback for sales by agent (UNIQUE NAME)
@callback(
    Output("dashboard-agent-sales-download-link", "href"),
    Input("dashboard-agent-sales-table-data", "data")
)
def update_dashboard_agent_download_link(table_data):
    if not table_data:
        return ""
    try:
        df = pd.read_json(table_data, orient='split')
        return parse_contents(df)
    except:
        return ""

# Download callback for project comparison (UNIQUE NAME)
@callback(
    Output("project-comparison-download-link", "href"),
    Input("project-comparison-table-data", "data")
)
def update_project_comparison_download_link(table_data):
    if not table_data:
        return ""
    try:
        df = pd.read_json(table_data, orient='split')
        return parse_contents(df)
    except:
        return ""

# Callback to render deposits/installments content based on view type
@callback(
    [Output("deposits-installments-content", "children"),
     Output("deposits-installments-table-data", "data")],
    [Input("deposits-installments-view-type", "data"),
     Input("time-filter-radio", "value"),
     Input("year-dropdown", "value")],
    prevent_initial_call=False
)
def render_deposits_content(view_type, time_filter, selected_year):
    engine = get_user_db_engine()
    table_data_store = ""
    
    if not engine:
        return [html.Div([
            html.I(className="fas fa-exclamation-triangle me-2 text-warning"),
            "Connect to database to view data"
        ], className="text-center p-3"), table_data_store]
    
    try:
        if time_filter == "daily":
            date_condition = "DATE(registration_date) = CURDATE()"
            transaction_date_condition = "DATE(transaction_date) = CURDATE()"
        elif time_filter == "weekly":
            date_condition = "registration_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
            transaction_date_condition = "transaction_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        else:
            date_condition = f"YEAR(registration_date) = {selected_year}"
            transaction_date_condition = f"YEAR(transaction_date) = {selected_year}"
        
        #Total Deposit
        try:
            total_deposit_query = f"""
            SELECT SUM(deposit_amount) AS total_deposit
            FROM customer_accounts
            WHERE {date_condition} AND deleted = 0
            """
            deposit_df = pd.read_sql(total_deposit_query, engine)
            current_deposit = deposit_df.iloc[0]['total_deposit'] if not deposit_df.empty and not pd.isna(deposit_df.iloc[0]['total_deposit']) else 0
        except Exception as e:
            print(f"Deposit query error: {e}")
            current_deposit = 0
        
        #Total Installment
        try:
            total_installment_query = f"""
            SELECT SUM(amount) AS total_installment
            FROM customer_account_invoices
            WHERE {transaction_date_condition} AND description = 'Instalment' AND deleted = 0
            """
            installment_df = pd.read_sql(total_installment_query, engine)
            current_installment = installment_df.iloc[0]['total_installment'] if not installment_df.empty and not pd.isna(installment_df.iloc[0]['total_installment']) else 0
        except Exception as e:
            print(f"Installment query error: {e}")
            current_installment = 0
        
        pie_data = [current_deposit, current_installment]
        pie_labels = ["Deposits", "Installments"]
        pie_colors = ["#0F3559", '#FFB300']
        
        if view_type == "table":
            # Create data table
            table_data = pd.DataFrame({
                'Category': pie_labels,
                'Amount ($)': [f"${val:,.2f}" for val in pie_data]
            })
            table_data_store = table_data.to_json(orient='split')
            
            return [dash_table.DataTable(
                data=table_data.to_dict('records'),
                columns=[{"name": i, "id": i} for i in table_data.columns],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'fontSize': '14px'
                },
                style_header={
                    'backgroundColor': '#0F3559',
                    'color': 'white',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ]
            ), table_data_store]
        elif view_type == "bar":
            # Create bar chart
            fig = go.Figure(data=[go.Bar(
                x=pie_labels,
                y=pie_data,
                marker_color=pie_colors,
                text=[f"${val:,.2f}" for val in pie_data],
                textposition='auto'
            )])
            fig.update_layout(
                title="Payment Distribution",
                height=350,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            return [dcc.Graph(figure=fig, config={'displayModeBar': False}), table_data_store]
        else:
            # Create EXPLODED pie chart (default)
            if sum(pie_data) > 0:
                # Add explosion effect by pulling slices apart
                fig = go.Figure(data=[go.Pie(
                    labels=pie_labels, 
                    values=pie_data, 
                    hole=.4,
                    pull=[0.05, 0.05],  # Explode both slices slightly
                    marker=dict(colors=pie_colors),
                    textinfo='percent+label',
                    hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<br>(%{percent})",
                    textposition='outside'  # Position text outside for better readability
                )])
                fig.update_layout(
                    title_text='Payment Distribution (Exploded)',
                    height=350,
                    margin=dict(l=20, r=20, t=40, b=20),
                    showlegend=False
                )
            else:
                fig = go.Figure()
                fig.update_layout(
                    title="No Payment Data Available",
                    height=350,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
            return [dcc.Graph(figure=fig, config={'displayModeBar': False}), table_data_store]
            
    except Exception as e:
        print(f"Error in render_deposits_content: {e}")
        return [html.Div([
            html.I(className="fas fa-exclamation-triangle me-2 text-danger"),
            f"Error loading data: {str(e)}"
        ], className="text-center p-3"), table_data_store]

# Callback to render stands sold content based on view type
@callback(
    [Output("stands-sold-content", "children"),
     Output("stands-sold-table-data", "data")],
    [Input("stands-sold-view-type", "data"),
     Input("time-filter-radio", "value"),
     Input("year-dropdown", "value")],
    prevent_initial_call=False
)
def render_stands_content(view_type, time_filter, selected_year):
    engine = get_user_db_engine()
    table_data_store = ""
    
    if not engine:
        return [html.Div([
            html.I(className="fas fa-exclamation-triangle me-2 text-warning"),
            "Connect to database to view data"
        ], className="text-center p-3"), table_data_store]
    
    try:
        if time_filter == "yearly" or time_filter == "forecast":
            # Updated query to include sales value
            trend_query = f"""
            SELECT 
                MONTH(registration_date) AS month,
                COUNT(stand_number) AS total_stands_sold,
                SUM(sale_value) AS total_sales_value
            FROM Stands
            WHERE YEAR(registration_date) = {selected_year} AND available = 0
            GROUP BY MONTH(registration_date)
            ORDER BY month
            """
            trend_df = pd.read_sql(trend_query, engine)
            
            all_months = pd.DataFrame({'month': range(1, 13)})
            trend_df = all_months.merge(trend_df, on='month', how='left').fillna(0)
            
            if time_filter == "forecast" and ML_AVAILABLE and not trend_df.empty:
                forecast_df = create_forecast(trend_df, months_ahead=3)
                
                if view_type == "table":
                    # Create data table for forecast with sales value
                    table_data = forecast_df.copy()
                    table_data['month_name'] = table_data['month'].apply(
                        lambda x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][x-1] 
                        if 1 <= x <= 12 else f"Pred {x-12}"
                    )
                    table_data_display = table_data[['month_name', 'total_stands_sold', 'type']].copy()
                    table_data_display.columns = ['Month', 'Stands Sold', 'Type']
                    # Add sales value if available
                    if 'total_sales_value' in trend_df.columns:
                        table_data_display['Sales Value ($)'] = trend_df['total_sales_value'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) and x > 0 else "$0.00")
                    table_data_store = table_data_display.to_json(orient='split')
                    
                    return [dash_table.DataTable(
                        data=table_data_display.to_dict('records'),
                        columns=[{"name": i, "id": i} for i in table_data_display.columns],
                        style_table={'overflowX': 'auto'},
                        style_cell={
                            'textAlign': 'left',
                            'padding': '10px',
                            'fontSize': '14px'
                        },
                        style_header={
                            'backgroundColor': '#0F3559',
                            'color': 'white',
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': 'rgb(248, 248, 248)'
                            }
                        ]
                    ), table_data_store]
                elif view_type == "bar":
                    # Create bar chart for forecast
                    x_data = [m if 1 <= m <= 12 else f"Pred {m-12}" for m in forecast_df['month']]
                    y_data = forecast_df['total_stands_sold']
                    colors = ['#007bff' if t == 'actual' else '#ffc107' for t in forecast_df['type']]
                    
                    fig = go.Figure(data=[go.Bar(
                        x=x_data,
                        y=y_data,
                        marker_color=colors,
                        text=y_data,
                        textposition='auto'
                    )])
                    fig.update_layout(
                        title="Monthly Forecast",
                        xaxis_title='Month',
                        yaxis_title='Stands Sold',
                        height=350,
                        margin=dict(l=40, r=20, t=40, b=40)
                    )
                    return [dcc.Graph(figure=fig, config={'displayModeBar': False}), table_data_store]
                else:
                    # Create line chart for forecast (default)
                    if not forecast_df.empty and len(forecast_df[forecast_df['type'] == 'forecast']) > 0:
                        area_fig = go.Figure()
                        
                        actual_df = forecast_df[forecast_df['type'] == 'actual']
                        if not actual_df.empty:
                            area_fig.add_trace(go.Scatter(
                                x=actual_df['month'],
                                y=actual_df['total_stands_sold'],
                                mode='lines+markers',
                                name='Actual',
                                line=dict(color="#007bff", width=3),
                                marker=dict(size=6)
                            ))
                        
                        forecast_points_df = forecast_df[forecast_df['type'] == 'forecast']
                        if not forecast_points_df.empty and not actual_df.empty:
                            last_actual = actual_df.iloc[-1]
                            forecast_x = [last_actual['month']] + forecast_points_df['month'].tolist()
                            forecast_y = [last_actual['total_stands_sold']] + forecast_points_df['total_stands_sold'].tolist()
                            
                            area_fig.add_trace(go.Scatter(
                                x=forecast_x,
                                y=forecast_y,
                                mode='lines+markers',
                                name='Forecast',
                                line=dict(color="#ffc107", width=3, dash='dash'),
                                marker=dict(size=6, symbol='diamond')
                            ))
                        
                        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        extended_month_names = month_names + [f"Pred {i+1}" for i in range(3)]
                        
                        max_month = max(forecast_df['month']) if not forecast_df.empty else 12
                        area_fig.update_layout(
                            xaxis=dict(
                                tickmode='array',
                                tickvals=list(range(1, min(max_month + 1, 16))),
                                ticktext=extended_month_names[:min(max_month, 15)]
                            ),
                            title="Monthly Forecast",
                            xaxis_title='Month',
                            yaxis_title='Stands Sold',
                            height=350,
                            margin=dict(l=40, r=20, t=40, b=40)
                        )
                        return [dcc.Graph(figure=area_fig, config={'displayModeBar': False}), table_data_store]
                    else:
                        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        x_data = [month_names[m-1] if 1 <= m <= 12 else f"Month {m}" for m in trend_df['month']]
                        y_data = trend_df['total_stands_sold'].tolist()
                        
                        fig = go.Figure(data=[go.Scatter(
                            x=x_data,
                            y=y_data,
                            mode='lines+markers',
                            fill='tozeroy',
                            name='Stands Sold',
                            line=dict(color="#b7a805", width=3),
                            marker=dict(size=6)
                        )])
                        fig.update_layout(
                            title="Monthly Trend",
                            xaxis_title='Month',
                            yaxis_title='Stands Sold',
                            height=350,
                            margin=dict(l=40, r=20, t=40, b=40)
                        )
                        return [dcc.Graph(figure=fig, config={'displayModeBar': False}), table_data_store]
            else:
                if view_type == "table":
                    # Create data table for regular data with sales value
                    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    table_data = pd.DataFrame({
                        'Month': [month_names[m-1] for m in trend_df['month']],
                        'Stands Sold': trend_df['total_stands_sold']
                    })
                    # Add sales value column if available
                    if 'total_sales_value' in trend_df.columns:
                        table_data['Sales Value ($)'] = trend_df['total_sales_value'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) and x > 0 else "$0.00")
                    table_data_store = table_data.to_json(orient='split')
                    
                    return [dash_table.DataTable(
                        data=table_data.to_dict('records'),
                        columns=[{"name": i, "id": i} for i in table_data.columns],
                        style_table={'overflowX': 'auto'},
                        style_cell={
                            'textAlign': 'left',
                            'padding': '10px',
                            'fontSize': '14px'
                        },
                        style_header={
                            'backgroundColor': '#0F3559',
                            'color': 'white',
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': 'rgb(248, 248, 248)'
                            }
                        ]
                    ), table_data_store]
                elif view_type == "bar":
                    # Create bar chart for regular data
                    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    x_data = [month_names[m-1] for m in trend_df['month']]
                    y_data = trend_df['total_stands_sold'].tolist()
                    
                    fig = go.Figure(data=[go.Bar(
                        x=x_data,
                        y=y_data,
                        marker_color="#b7a805",
                        text=y_data,
                        textposition='auto'
                    )])
                    fig.update_layout(
                        title="Monthly Trend",
                        xaxis_title='Month',
                        yaxis_title='Stands Sold',
                        height=350,
                        margin=dict(l=40, r=20, t=40, b=40)
                    )
                    return [dcc.Graph(figure=fig, config={'displayModeBar': False}), table_data_store]
                else:
                    # Create area chart for regular data (default)
                    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    x_data = [month_names[m-1] if 1 <= m <= 12 else f"Month {m}" for m in trend_df['month']]
                    y_data = trend_df['total_stands_sold'].tolist()
                    
                    fig = go.Figure(data=[go.Scatter(
                        x=x_data,
                        y=y_data,
                        mode='lines+markers',
                        fill='tozeroy',
                        name='Stands Sold',
                        line=dict(color="#b7a805", width=3),
                        marker=dict(size=6)
                    )])
                    fig.update_layout(
                        title="Monthly Trend",
                        xaxis_title='Month',
                        yaxis_title='Stands Sold',
                        height=350,
                        margin=dict(l=40, r=20, t=40, b=40)
                    )
                    return [dcc.Graph(figure=fig, config={'displayModeBar': False}), table_data_store]
                
        elif time_filter == "weekly":
            # Updated query to include sales value
            trend_query = """
            SELECT 
                DATE(registration_date) AS day,
                COUNT(stand_number) AS total_stands_sold,
                SUM(sale_value) AS total_sales_value
            FROM Stands
            WHERE registration_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) AND available = 0
            GROUP BY DATE(registration_date)
            ORDER BY day
            """
            trend_df = pd.read_sql(trend_query, engine)
            
            end_date = datetime.date.today()
            start_date = end_date - datetime.timedelta(days=6)
            date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            date_df = pd.DataFrame({'day': date_range.date})
            trend_df['day'] = pd.to_datetime(trend_df['day']).dt.date
            trend_df = date_df.merge(trend_df, left_on='day', right_on='day', how='left').fillna(0)
            
            if view_type == "table":
                # Create data table with sales value
                table_data = trend_df[['day', 'total_stands_sold']].copy()
                table_data.columns = ['Date', 'Stands Sold']
                table_data['Date'] = table_data['Date'].apply(lambda x: x.strftime('%Y-%m-%d'))
                # Add sales value column
                table_data['Sales Value ($)'] = trend_df['total_sales_value'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) and x > 0 else "$0.00")
                table_data_store = table_data.to_json(orient='split')
                
                return [dash_table.DataTable(
                    data=table_data.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in table_data.columns],
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '10px',
                        'fontSize': '14px'
                    },
                    style_header={
                        'backgroundColor': '#0F3559',
                        'color': 'white',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        }
                    ]
                ), table_data_store]
            elif view_type == "bar":
                # Create bar chart
                x_data = [d.strftime('%a') for d in trend_df['day']]
                y_data = trend_df['total_stands_sold'].tolist()
                
                fig = go.Figure(data=[go.Bar(
                    x=x_data,
                    y=y_data,
                    marker_color="#007bff",
                    text=y_data,
                    textposition='auto'
                )])
                fig.update_layout(
                    title='Daily Stands Sales Trend (Last 7 Days)',
                    xaxis_title='Day',
                    yaxis_title='Stands Sold',
                    height=350,
                    margin=dict(l=40, r=20, t=40, b=40)
                )
                return [dcc.Graph(figure=fig, config={'displayModeBar': False}), table_data_store]
            else:
                # Create area chart (default)
                x_data = [d.strftime('%a') for d in trend_df['day']]
                y_data = trend_df['total_stands_sold'].tolist()
                
                fig = go.Figure(data=[go.Scatter(
                    x=x_data,
                    y=y_data,
                    mode='lines+markers',
                    fill='tozeroy',
                    name='Stands Sold',
                    line=dict(color="#007bff", width=3),
                    marker=dict(size=6)
                )])
                fig.update_layout(
                    title='Daily Stands Sales Trend (Last 7 Days)',
                    xaxis_title='Day',
                    yaxis_title='Stands Sold',
                    height=350,
                    margin=dict(l=40, r=20, t=40, b=40)
                )
                return [dcc.Graph(figure=fig, config={'displayModeBar': False}), table_data_store]
                
        else:  # daily
            # Updated query to include sales value
            trend_query = """
            SELECT 
                HOUR(registration_date) AS hour,
                COUNT(stand_number) AS total_stands_sold,
                SUM(sale_value) AS total_sales_value
            FROM Stands
            WHERE DATE(registration_date) = CURDATE() AND available = 0
            GROUP BY HOUR(registration_date)
            ORDER BY hour
            """
            trend_df = pd.read_sql(trend_query, engine)
            
            all_hours = pd.DataFrame({'hour': range(24)})
            trend_df = all_hours.merge(trend_df, on='hour', how='left').fillna(0)
            
            if view_type == "table":
                # Create data table with sales value
                table_data = trend_df[['hour', 'total_stands_sold']].copy()
                table_data.columns = ['Hour', 'Stands Sold']
                # Add sales value column
                table_data['Sales Value ($)'] = trend_df['total_sales_value'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) and x > 0 else "$0.00")
                table_data_store = table_data.to_json(orient='split')
                
                return [dash_table.DataTable(
                    data=table_data.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in table_data.columns],
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '10px',
                        'fontSize': '14px'
                    },
                    style_header={
                        'backgroundColor': '#0F3559',
                        'color': 'white',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        }
                    ]
                ), table_data_store]
            elif view_type == "bar":
                # Create bar chart
                x_data = [f"{h}:00" for h in trend_df['hour']]
                y_data = trend_df['total_stands_sold'].tolist()
                
                fig = go.Figure(data=[go.Bar(
                    x=x_data,
                    y=y_data,
                    marker_color="#001020",
                    text=y_data,
                    textposition='auto'
                )])
                fig.update_layout(
                    title='Hourly Stands Sales Trend (Today)',
                    xaxis_title='Hour',
                    yaxis_title='Stands Sold',
                    height=350,
                    margin=dict(l=40, r=20, t=40, b=40)
                )
                return [dcc.Graph(figure=fig, config={'displayModeBar': False}), table_data_store]
            else:
                # Create area chart (default)
                x_data = [f"{h}:00" for h in trend_df['hour']]
                y_data = trend_df['total_stands_sold'].tolist()
                
                fig = go.Figure(data=[go.Scatter(
                    x=x_data,
                    y=y_data,
                    mode='lines+markers',
                    fill='tozeroy',
                    name='Stands Sold',
                    line=dict(color="#001020", width=3),
                    marker=dict(size=6)
                )])
                fig.update_layout(
                    title='Hourly Stands Sales Trend (Today)',
                    xaxis_title='Hour',
                    yaxis_title='Stands Sold',
                    height=350,
                    margin=dict(l=40, r=20, t=40, b=40)
                )
                return [dcc.Graph(figure=fig, config={'displayModeBar': False}), table_data_store]
                
    except Exception as e:
        print(f"Error in render_stands_content: {e}")
        return [html.Div([
            html.I(className="fas fa-exclamation-triangle me-2 text-danger"),
            f"Error loading data: {str(e)}"
        ], className="text-center p-3"), table_data_store]

# Callback to render project performance content based on view type
@callback(
    [Output("project-performance-content", "children"),
     Output("project-performance-table-data", "data")],
    [Input("project-performance-view-type", "data"),
     Input("time-filter-radio", "value"),
     Input("year-dropdown", "value")],
    prevent_initial_call=False
)   
def render_project_content(view_type, time_filter, selected_year):
    engine = get_user_db_engine()
    table_data_store = ""
    
    if not engine:
        return [html.Div([
            html.I(className="fas fa-exclamation-triangle me-2 text-warning"),
            "Connect to database to view data"
        ], className="text-center p-3"), table_data_store]
    
    try:
        if time_filter == "daily":
            date_condition = "DATE(s.registration_date) = CURDATE()"
        elif time_filter == "weekly":
            date_condition = "s.registration_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        else:
            date_condition = f"YEAR(s.registration_date) = {selected_year}"
        
        project_query = f"""
        SELECT 
            p.name AS project_name,
            p.id AS project_id,
            COUNT(s.stand_number) AS stands_sold,
            SUM(s.sale_value) AS stands_value,
            COUNT(CASE WHEN s.available = 1 THEN 1 END) AS stands_available
        FROM Projects p
        INNER JOIN Stands s ON p.id = s.project_id
        WHERE {date_condition}
        GROUP BY p.id, p.name
        ORDER BY stands_sold DESC
        LIMIT 20
        """
        
        project_df = pd.read_sql(project_query, engine)
        
        if project_df.empty:
            return [html.Div([
                html.I(className="fas fa-info-circle me-2 text-info"),
                "No project data available for selected period"
            ], className="text-center p-3"), table_data_store]
        
        if view_type == "table":
            # Create data table
            table_data = project_df.copy()
            table_data['stands_value'] = table_data['stands_value'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "$0.00")
            table_data_display = table_data[['project_name', 'stands_sold', 'stands_value', 'stands_available']].copy()
            table_data_display.columns = ['Project Name', 'Stands Sold', 'Sales Value ($)', 'Available']
            table_data_store = table_data_display.to_json(orient='split')
            
            return [dash_table.DataTable(
                data=table_data_display.to_dict('records'),
                columns=[{"name": i, "id": i} for i in table_data_display.columns],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'fontSize': '14px'
                },
                style_header={
                    'backgroundColor': '#0F3559',
                    'color': 'white',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ]
            ), table_data_store]
        elif view_type == "line":
            # Create line chart
            fig = go.Figure(data=[go.Scatter(
                x=project_df['project_name'],
                y=project_df['stands_sold'],
                mode='lines+markers',
                line=dict(width=3, color="#FFB300"),
                marker=dict(size=8),
                text=project_df['stands_sold'],
                textposition='top center'
            )])
            fig.update_layout(
                title="Project Performance - Stands Sold (Line)",
                xaxis_title="Project",
                yaxis_title="Stands Sold",
                height=400,
                margin=dict(l=40, r=20, t=50, b=80),
                hovermode='closest'
            )
            fig.update_xaxes(tickangle=45, tickfont=dict(size=10))
            return [dcc.Graph(figure=fig, config={'displayModeBar': True}), table_data_store]
        else:
            # Create bar chart (default)
            project_df['project_label'] = project_df['project_name']
            
            fig = go.Figure(data=[
                go.Bar(
                    x=project_df['project_label'],
                    y=project_df['stands_sold'],
                    marker_color="#FFB300",
                    text=project_df['stands_sold'],
                    textposition='auto',
                    hovertemplate='<b>%{x}</b><br>' +
                                 'Stands Sold: %{y}<br>' +
                                 'Sales Value: $%{customdata[0]:,.2f}<br>' +
                                 'Stands Available: %{customdata[1]}<br>' +
                                 '<extra></extra>',
                    customdata=project_df[['stands_value', 'stands_available']].values
                )
            ])
            
            fig.update_layout(
                title="Project Performance - Stands Sold (Bar)",
                xaxis_title="Project",
                yaxis_title="Stands Sold",
                height=400,
                margin=dict(l=40, r=20, t=50, b=80),
                hovermode='closest'
            )
            
            fig.update_xaxes(tickangle=45, tickfont=dict(size=10))
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            
            return [dcc.Graph(figure=fig, config={'displayModeBar': True}), table_data_store]
            
    except Exception as e:
        print(f"Error in render_project_content: {e}")
        return [html.Div([
            html.I(className="fas fa-exclamation-triangle me-2 text-danger"),
            f"Error loading project data: {str(e)}"
        ], className="text-center p-3"), table_data_store]

# Callback to render sales by agent content based on view type (UNIQUE NAMES)
@callback(
    [Output("dashboard-agent-sales-content", "children"),
     Output("dashboard-agent-sales-table-data", "data")],
    [Input("dashboard-agent-sales-view-type", "data"),
     Input("time-filter-radio", "value"),
     Input("year-dropdown", "value")],
    prevent_initial_call=False
)
def render_dashboard_agent_sales_content(view_type, time_filter, selected_year):
    engine = get_user_db_engine()
    table_data_store = ""
    
    if not engine:
        return [html.Div([
            html.I(className="fas fa-exclamation-triangle me-2 text-warning"),
            "Connect to database to view data"
        ], className="text-center p-3"), table_data_store]
    
    try:
        # Build date condition based on time filter
        if time_filter == "daily":
            date_condition = "DATE(ca.registration_date) = CURDATE()"
        elif time_filter == "weekly":
            date_condition = "ca.registration_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        else:
            date_condition = f"YEAR(ca.registration_date) = {selected_year}"
        
        # Sales by Agent Query - Get detailed data for the selected period
        agent_query = f"""
        SELECT 
            ca.agent_name,
            p.name AS project_name,
            COUNT(*) AS stands_sold,
            SUM(ca.stand_value) AS total_sales
        FROM customer_accounts ca
        INNER JOIN Projects p ON ca.project_id = p.id
        WHERE {date_condition} AND ca.deleted = 0 AND ca.agent_name IS NOT NULL AND ca.agent_name != ''
        GROUP BY ca.agent_name, p.name
        ORDER BY ca.agent_name, p.name
        """
        agent_df = pd.read_sql(agent_query, engine)
        
        if agent_df.empty:
            return [html.Div([
                html.I(className="fas fa-info-circle me-2 text-info"),
                "No agent sales data available for selected period"
            ], className="text-center p-3"), table_data_store]
        
        # Aggregate data by agent for visualization
        agent_summary = agent_df.groupby('agent_name').agg({
            'stands_sold': 'sum',
            'total_sales': 'sum'
        }).reset_index()
        agent_summary = agent_summary.sort_values('total_sales', ascending=False).head(10)
        
        if view_type == "table":
            # Pivot the data to show projects as columns
            # First, get all unique projects for the selected period
            all_projects = agent_df['project_name'].unique()
            
            # Pivot the data
            pivot_df = agent_df.pivot_table(
                index='agent_name',
                columns='project_name',
                values='stands_sold',
                aggfunc='sum',
                fill_value=0
            ).reset_index()
            
            # Ensure all projects are columns (in case some agents don't have sales in all projects)
            for project in all_projects:
                if project not in pivot_df.columns:
                    pivot_df[project] = 0
            
            # Add total stands sold column
            project_columns = [col for col in pivot_df.columns if col != 'agent_name']
            pivot_df['Total Stands'] = pivot_df[project_columns].sum(axis=1)
            
            # Add total sales column
            agent_sales_totals = agent_df.groupby('agent_name')['total_sales'].sum().reset_index()
            pivot_df = pivot_df.merge(agent_sales_totals, on='agent_name', how='left')
            pivot_df.rename(columns={'total_sales': 'Total Sales ($)'}, inplace=True)
            
            # Format currency column
            pivot_df['Total Sales ($)'] = pivot_df['Total Sales ($)'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "$0.00")
            
            # Reorder columns: agent_name, project columns, Total Stands, Total Sales ($)
            ordered_columns = ['agent_name'] + sorted([col for col in project_columns if col != 'Total Stands']) + ['Total Stands', 'Total Sales ($)']
            pivot_df = pivot_df[ordered_columns]
            
            # Rename columns for display
            display_columns = ['Agent Name'] + sorted([col for col in project_columns if col != 'Total Stands']) + ['Total Stands', 'Total Sales ($)']
            pivot_df_display = pivot_df.copy()
            pivot_df_display.columns = display_columns
            
            table_data_store = pivot_df_display.to_json(orient='split')
            
            return [dash_table.DataTable(
                data=pivot_df_display.to_dict('records'),
                columns=[{"name": i, "id": i} for i in pivot_df_display.columns],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'fontSize': '14px',
                    'minWidth': '100px',
                    'width': '100px',
                    'maxWidth': '100px'
                },
                style_header={
                    'backgroundColor': '#0F3559',
                    'color': 'white',
                    'fontWeight': 'bold',
                    'whiteSpace': 'normal',
                    'height': 'auto'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ],
                page_size=15
            ), table_data_store]
        elif view_type == "bar":
            # Create horizontal bar chart
            fig = go.Figure(data=[go.Bar(
                x=agent_summary['total_sales'],
                y=agent_summary['agent_name'],
                orientation='h',
                marker_color='#007bff',
                text=[f"${val:,.0f}" for val in agent_summary['total_sales']],
                textposition='auto'
            )])
            fig.update_layout(
                title="Top Agents by Sales Value",
                xaxis_title="Total Sales ($)",
                yaxis_title="Agent Name",
                height=400,
                margin=dict(l=150, r=20, t=40, b=40),
                yaxis={'categoryorder':'total ascending'}
            )
            return [dcc.Graph(figure=fig, config={'displayModeBar': False}), table_data_store]
        else:
            # Create EXPLODED pie chart (default)
            if agent_summary['total_sales'].sum() > 0:
                fig = go.Figure(data=[go.Pie(
                    labels=agent_summary['agent_name'], 
                    values=agent_summary['total_sales'], 
                    hole=.4,
                    pull=[0.05] * len(agent_summary),  # Explode all slices
                    marker=dict(colors=['#FFB300', "#10EC10", "#f91115", "#15DEE1", "#ca0abd", '#ff7f0e', "#246527", '#d62728', '#9467bd', '#8c564b']),
                    textinfo='percent+label',
                    hovertemplate="<b>%{label}</b><br>Sales: $%{value:,.2f}<br>(%{percent})<br>Stands: %{customdata}",
                    textposition='outside',
                    customdata=agent_summary['stands_sold']
                )])
                fig.update_layout(
                    title_text='Sales by Agent (Exploded)',
                    height=400,
                    margin=dict(l=20, r=20, t=50, b=20),
                    showlegend=False
                )
            else:
                fig = go.Figure()
                fig.update_layout(
                    title="No Agent Sales Data Available",
                    height=400,
                    margin=dict(l=20, r=20, t=50, b=20)
                )
            return [dcc.Graph(figure=fig, config={'displayModeBar': False}), table_data_store]
            
    except Exception as e:
        print(f"Error in render_dashboard_agent_sales_content: {e}")
        return [html.Div([
            html.I(className="fas fa-exclamation-triangle me-2 text-danger"),
            f"Error loading data: {str(e)}"
        ], className="text-center p-3"), table_data_store]

# Callback to render project comparison content based on view type (UNIQUE NAMES)
@callback(
    [Output("project-comparison-content", "children"),
     Output("project-comparison-table-data", "data")],
    [Input("project-comparison-view-type", "data"),
     Input("time-filter-radio", "value"),
     Input("year-dropdown", "value")],
    prevent_initial_call=False
)
def render_project_comparison_content(view_type, time_filter, selected_year):
    engine = get_user_db_engine()
    table_data_store = ""
    
    if not engine:
        return [html.Div([
            html.I(className="fas fa-exclamation-triangle me-2 text-warning"),
            "Connect to database to view data"
        ], className="text-center p-3"), table_data_store]
    
    try:
        # Build date condition based on time filter
        if time_filter == "daily":
            # Hourly data for today with sales value and stands sold
            query = f"""
            SELECT 
                p.name AS project_name,
                HOUR(s.registration_date) AS hour,
                COUNT(s.stand_number) AS stands_sold,
                SUM(s.sale_value) AS sales_value
            FROM Stands s
            INNER JOIN Projects p ON s.project_id = p.id
            WHERE DATE(s.registration_date) = CURDATE() AND s.available = 0
            GROUP BY p.name, HOUR(s.registration_date)
            ORDER BY p.name, hour
            """
            df = pd.read_sql(query, engine)
            
            if df.empty:
                if view_type == "table":
                    return [html.Div("No data available", className="text-center p-3"), table_data_store]
                fig = go.Figure()
                fig.update_layout(
                    title="No Project Data Available for Today",
                    height=400,
                    margin=dict(l=40, r=20, t=40, b=40)
                )
                return [dcc.Graph(figure=fig, config={'displayModeBar': False}), table_data_store]
            
            # Create hourly timeline
            hours = list(range(24))
            hour_labels = [f"{h}:00" for h in hours]
            
            if view_type == "table":
                # Create pivot table with hours as columns showing sales value only
                pivot_df = df.pivot(index='project_name', columns='hour', values='sales_value').fillna(0)
                pivot_df.columns = [f"Hour {col}" for col in pivot_df.columns]
                pivot_df.reset_index(inplace=True)
                
                # Calculate totals
                pivot_df['Total Sales ($)'] = pivot_df.drop('project_name', axis=1).sum(axis=1)
                
                # Format currency columns
                currency_columns = [col for col in pivot_df.columns if col.startswith('Hour')]
                for col in currency_columns:
                    pivot_df[col] = pivot_df[col].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) and x > 0 else "$0.00")
                pivot_df['Total Sales ($)'] = pivot_df['Total Sales ($)'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) and x > 0 else "$0.00")
                
                # Reorder columns
                cols = ['project_name'] + [f"Hour {h}" for h in range(24)] + ['Total Sales ($)']
                pivot_df = pivot_df[cols]
                pivot_df.columns = ['Project Name'] + [f"Hour {h}" for h in range(24)] + ['Total Sales ($)']
                
                table_data_store = pivot_df.to_json(orient='split')
                
                return [dash_table.DataTable(
                    data=pivot_df.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in pivot_df.columns],
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '8px',
                        'fontSize': '11px',
                        'minWidth': '80px',
                        'width': '80px',
                        'maxWidth': '80px'
                    },
                    style_header={
                        'backgroundColor': '#0F3559',
                        'color': 'white',
                        'fontWeight': 'bold',
                        'whiteSpace': 'normal',
                        'height': 'auto'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        }
                    ],
                    page_size=15
                ), table_data_store]
            elif view_type == "bar":
                # Create grouped bar chart with hours as x-axis and projects as grouped bars showing sales value
                fig = go.Figure()
                
                # Get unique projects
                projects = df['project_name'].unique()
                
                # Define color palette
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
                
                # For each hour, create grouped bars for each project
                for i, project in enumerate(projects):
                    project_data = df[df['project_name'] == project]
                    
                    # Create complete hourly data
                    hourly_data = pd.DataFrame({'hour': hours})
                    hourly_data = hourly_data.merge(project_data[['hour', 'sales_value', 'stands_sold']], on='hour', how='left').fillna(0)
                    
                    fig.add_trace(go.Bar(
                        x=hour_labels,
                        y=hourly_data['sales_value'],
                        name=project,
                        marker_color=colors[i % len(colors)],
                        text=[f"Stands: {int(st)}<br>Value: ${val:,.0f}" for st, val in zip(hourly_data['stands_sold'], hourly_data['sales_value'])],
                        textposition='auto'
                    ))
                
                fig.update_layout(
                    title="Project Sales Value Comparison - Hourly Grouped (Today)",
                    xaxis_title="Hour",
                    yaxis_title="Sales Value ($)",
                    height=400,
                    margin=dict(l=40, r=20, t=40, b=40),
                    barmode='group'
                )
                return [dcc.Graph(figure=fig, config={'displayModeBar': False}), table_data_store]
            else:
                # Create line chart (default) showing sales value with tooltip showing stands sold
                fig = go.Figure()
                
                # Get unique projects
                projects = df['project_name'].unique()
                
                # Define color palette
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
                
                for i, project in enumerate(projects):
                    project_data = df[df['project_name'] == project]
                    
                    # Create complete hourly data
                    hourly_data = pd.DataFrame({'hour': hours})
                    hourly_data = hourly_data.merge(project_data[['hour', 'sales_value', 'stands_sold']], on='hour', how='left').fillna(0)
                    
                    fig.add_trace(go.Scatter(
                        x=hour_labels,
                        y=hourly_data['sales_value'],
                        mode='lines+markers',
                        name=project,
                        line=dict(width=3, color=colors[i % len(colors)]),
                        marker=dict(size=6),
                        hovertemplate='<b>%{fullData.name}</b><br>' +
                                     'Hour: %{x}<br>' +
                                     'Sales Value: $%{y:,.2f}<br>' +
                                     'Stands Sold: %{customdata}<br>' +
                                     '<extra></extra>',
                        customdata=hourly_data['stands_sold']
                    ))
                
                fig.update_layout(
                    title="Project Sales Value Comparison - Hourly (Today)",
                    xaxis_title="Hour",
                    yaxis_title="Sales Value ($)",
                    height=400,
                    margin=dict(l=40, r=20, t=40, b=40),
                    hovermode='x unified'
                )
                return [dcc.Graph(figure=fig, config={'displayModeBar': False}), table_data_store]
                
        elif time_filter == "weekly":
            # Daily data for last 7 days with sales value and stands sold
            query = """
            SELECT 
                p.name AS project_name,
                DATE(s.registration_date) AS day,
                COUNT(s.stand_number) AS stands_sold,
                SUM(s.sale_value) AS sales_value
            FROM Stands s
            INNER JOIN Projects p ON s.project_id = p.id
            WHERE s.registration_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) AND s.available = 0
            GROUP BY p.name, DATE(s.registration_date)
            ORDER BY p.name, day
            """
            df = pd.read_sql(query, engine)
            
            if df.empty:
                if view_type == "table":
                    return [html.Div("No data available", className="text-center p-3"), table_data_store]
                fig = go.Figure()
                fig.update_layout(
                    title="No Project Data Available for Last 7 Days",
                    height=400,
                    margin=dict(l=40, r=20, t=40, b=40)
                )
                return [dcc.Graph(figure=fig, config={'displayModeBar': False}), table_data_store]
            
            # Create daily timeline
            end_date = datetime.date.today()
            start_date = end_date - datetime.timedelta(days=6)
            date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            dates = date_range.date
            day_labels = [d.strftime('%a %m/%d') for d in dates]
            
            if view_type == "table":
                # Create pivot table with days as columns showing sales value only
                df['day'] = pd.to_datetime(df['day']).dt.date
                pivot_df = df.pivot(index='project_name', columns='day', values='sales_value').fillna(0)
                pivot_df.columns = [col.strftime('%a %m/%d') for col in pivot_df.columns]
                pivot_df.reset_index(inplace=True)
                
                # Calculate totals
                pivot_df['Total Sales ($)'] = pivot_df.drop('project_name', axis=1).sum(axis=1)
                
                # Format currency columns
                currency_columns = [col for col in pivot_df.columns if col != 'project_name' and col != 'Total Sales ($)']
                for col in currency_columns:
                    pivot_df[col] = pivot_df[col].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) and x > 0 else "$0.00")
                pivot_df['Total Sales ($)'] = pivot_df['Total Sales ($)'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) and x > 0 else "$0.00")
                
                # Reorder columns
                cols = ['project_name'] + [d.strftime('%a %m/%d') for d in dates] + ['Total Sales ($)']
                pivot_df = pivot_df[cols]
                pivot_df.columns = ['Project Name'] + [d.strftime('%a %m/%d') for d in dates] + ['Total Sales ($)']
                
                table_data_store = pivot_df.to_json(orient='split')
                
                return [dash_table.DataTable(
                    data=pivot_df.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in pivot_df.columns],
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '8px',
                        'fontSize': '11px',
                        'minWidth': '100px',
                        'width': '100px',
                        'maxWidth': '100px'
                    },
                    style_header={
                        'backgroundColor': '#0F3559',
                        'color': 'white',
                        'fontWeight': 'bold',
                        'whiteSpace': 'normal',
                        'height': 'auto'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        }
                    ],
                    page_size=15
                ), table_data_store]
            elif view_type == "bar":
                # Create grouped bar chart with days as x-axis and projects as grouped bars showing sales value
                fig = go.Figure()
                
                # Get unique projects
                projects = df['project_name'].unique()
                
                # Define color palette
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
                
                # Convert dates to string for grouping
                df['day_str'] = pd.to_datetime(df['day']).dt.date.apply(lambda x: x.strftime('%a %m/%d'))
                
                # For each day, create grouped bars for each project
                for i, project in enumerate(projects):
                    project_data = df[df['project_name'] == project]
                    
                    # Create complete daily data
                    daily_data = pd.DataFrame({'day': [d.strftime('%a %m/%d') for d in dates]})
                    daily_data = daily_data.merge(project_data[['day_str', 'sales_value', 'stands_sold']], left_on='day', right_on='day_str', how='left').fillna(0)
                    
                    fig.add_trace(go.Bar(
                        x=daily_data['day'],
                        y=daily_data['sales_value'],
                        name=project,
                        marker_color=colors[i % len(colors)],
                        text=[f"Stands: {int(st)}<br>Value: ${val:,.0f}" for st, val in zip(daily_data['stands_sold'], daily_data['sales_value'])],
                        textposition='auto'
                    ))
                
                fig.update_layout(
                    title="Project Sales Value Comparison - Daily Grouped (Last 7 Days)",
                    xaxis_title="Day",
                    yaxis_title="Sales Value ($)",
                    height=400,
                    margin=dict(l=40, r=20, t=40, b=40),
                    barmode='group'
                )
                return [dcc.Graph(figure=fig, config={'displayModeBar': False}), table_data_store]
            else:
                # Create line chart (default) showing sales value with tooltip showing stands sold
                fig = go.Figure()
                
                # Get unique projects
                projects = df['project_name'].unique()
                
                # Define color palette
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
                
                for i, project in enumerate(projects):
                    project_data = df[df['project_name'] == project]
                    project_data['day'] = pd.to_datetime(project_data['day']).dt.date
                    
                    # Create complete daily data
                    daily_data = pd.DataFrame({'day': dates})
                    daily_data = daily_data.merge(project_data[['day', 'sales_value', 'stands_sold']], on='day', how='left').fillna(0)
                    
                    fig.add_trace(go.Scatter(
                        x=day_labels,
                        y=daily_data['sales_value'],
                        mode='lines+markers',
                        name=project,
                        line=dict(width=3, color=colors[i % len(colors)]),
                        marker=dict(size=6),
                        hovertemplate='<b>%{fullData.name}</b><br>' +
                                     'Day: %{x}<br>' +
                                     'Sales Value: $%{y:,.2f}<br>' +
                                     'Stands Sold: %{customdata}<br>' +
                                     '<extra></extra>',
                        customdata=daily_data['stands_sold']
                    ))
                
                fig.update_layout(
                    title="Project Sales Value Comparison - Daily (Last 7 Days)",
                    xaxis_title="Day",
                    yaxis_title="Sales Value ($)",
                    height=400,
                    margin=dict(l=40, r=20, t=40, b=40),
                    hovermode='x unified'
                )
                return [dcc.Graph(figure=fig, config={'displayModeBar': False}), table_data_store]
                
        else:  # yearly or forecast
            # Monthly data for selected year with sales value and stands sold
            query = f"""
            SELECT 
                p.name AS project_name,
                MONTH(s.registration_date) AS month,
                COUNT(s.stand_number) AS stands_sold,
                SUM(s.sale_value) AS sales_value
            FROM Stands s
            INNER JOIN Projects p ON s.project_id = p.id
            WHERE YEAR(s.registration_date) = {selected_year} AND s.available = 0
            GROUP BY p.name, MONTH(s.registration_date)
            ORDER BY p.name, month
            """
            df = pd.read_sql(query, engine)
            
            if df.empty:
                if view_type == "table":
                    return [html.Div("No data available", className="text-center p-3"), table_data_store]
                fig = go.Figure()
                fig.update_layout(
                    title=f"No Project Data Available for {selected_year}",
                    height=400,
                    margin=dict(l=40, r=20, t=40, b=40)
                )
                return [dcc.Graph(figure=fig, config={'displayModeBar': False}), table_data_store]
            
            # Create monthly timeline
            months = list(range(1, 13))
            month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            if view_type == "table":
                # Create pivot table with months as columns showing sales value only
                pivot_df = df.pivot(index='project_name', columns='month', values='sales_value').fillna(0)
                pivot_df.columns = [month_labels[col-1] for col in pivot_df.columns]
                pivot_df.reset_index(inplace=True)
                
                # Calculate totals
                pivot_df['Total Sales ($)'] = pivot_df.drop('project_name', axis=1).sum(axis=1)
                
                # Format currency columns
                currency_columns = [col for col in pivot_df.columns if col != 'project_name' and col != 'Total Sales ($)']
                for col in currency_columns:
                    pivot_df[col] = pivot_df[col].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) and x > 0 else "$0.00")
                pivot_df['Total Sales ($)'] = pivot_df['Total Sales ($)'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) and x > 0 else "$0.00")
                
                # Reorder columns
                cols = ['project_name'] + month_labels + ['Total Sales ($)']
                pivot_df = pivot_df[cols]
                pivot_df.columns = ['Project Name'] + month_labels + ['Total Sales ($)']
                
                table_data_store = pivot_df.to_json(orient='split')
                
                return [dash_table.DataTable(
                    data=pivot_df.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in pivot_df.columns],
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '8px',
                        'fontSize': '11px',
                        'minWidth': '80px',
                        'width': '80px',
                        'maxWidth': '80px'
                    },
                    style_header={
                        'backgroundColor': '#0F3559',
                        'color': 'white',
                        'fontWeight': 'bold',
                        'whiteSpace': 'normal',
                        'height': 'auto'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        }
                    ],
                    page_size=15
                ), table_data_store]
            elif view_type == "bar":
                # Create grouped bar chart with months as x-axis and projects as grouped bars showing sales value
                fig = go.Figure()
                
                # Get unique projects
                projects = df['project_name'].unique()
                
                # Define color palette
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
                
                # For each month, create grouped bars for each project
                for i, project in enumerate(projects):
                    project_data = df[df['project_name'] == project]
                    
                    # Create complete monthly data
                    monthly_data = pd.DataFrame({'month': months})
                    monthly_data = monthly_data.merge(project_data[['month', 'sales_value', 'stands_sold']], on='month', how='left').fillna(0)
                    
                    fig.add_trace(go.Bar(
                        x=month_labels,
                        y=monthly_data['sales_value'],
                        name=project,
                        marker_color=colors[i % len(colors)],
                        text=[f"Stands: {int(st)}<br>Value: ${val:,.0f}" for st, val in zip(monthly_data['stands_sold'], monthly_data['sales_value'])],
                        textposition='auto'
                    ))
                
                fig.update_layout(
                    title=f"Project Sales Value Comparison - Monthly Grouped ({selected_year})",
                    xaxis_title="Month",
                    yaxis_title="Sales Value ($)",
                    height=400,
                    margin=dict(l=40, r=20, t=40, b=40),
                    barmode='group'
                )
                return [dcc.Graph(figure=fig, config={'displayModeBar': False}), table_data_store]
            else:
                # Create line chart (default) showing sales value with tooltip showing stands sold
                fig = go.Figure()
                
                # Get unique projects
                projects = df['project_name'].unique()
                
                # Define color palette
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
                
                for i, project in enumerate(projects):
                    project_data = df[df['project_name'] == project]
                    
                    # Create complete monthly data
                    monthly_data = pd.DataFrame({'month': months})
                    monthly_data = monthly_data.merge(project_data[['month', 'sales_value', 'stands_sold']], on='month', how='left').fillna(0)
                    
                    fig.add_trace(go.Scatter(
                        x=month_labels,
                        y=monthly_data['sales_value'],
                        mode='lines+markers',
                        name=project,
                        line=dict(width=3, color=colors[i % len(colors)]),
                        marker=dict(size=6),
                        hovertemplate='<b>%{fullData.name}</b><br>' +
                                     'Month: %{x}<br>' +
                                     'Sales Value: $%{y:,.2f}<br>' +
                                     'Stands Sold: %{customdata}<br>' +
                                     '<extra></extra>',
                        customdata=monthly_data['stands_sold']
                    ))
                
                fig.update_layout(
                    title=f"Project Sales Value Comparison - Monthly ({selected_year})",
                    xaxis_title="Month",
                    yaxis_title="Sales Value ($)",
                    height=400,
                    margin=dict(l=40, r=20, t=40, b=40),
                    hovermode='x unified'
                )
                return [dcc.Graph(figure=fig, config={'displayModeBar': False}), table_data_store]
        
    except Exception as e:
        print(f"Error in render_project_comparison_content: {e}")
        return [html.Div([
            html.I(className="fas fa-exclamation-triangle me-2 text-danger"),
            f"Error loading project comparison data: {str(e)}"
        ], className="text-center p-3"), table_data_store]
    finally:
        if engine:
            try:
                engine.dispose()
            except:
                pass

# Main dashboard callback 
@callback(
    [Output("total-stand-value", "children"),
     Output("stands-sold-value", "children"),
     Output("stands-available-value", "children"),
     Output("stands-reserved-value", "children"),
     Output("stand-value-period", "children"),
     Output("stands-sold-period", "children"),
     Output("stands-available-period", "children"),
     Output("stands-reserved-period", "children"),
     Output("stand-value-yoy", "children"),
     Output("stands-sold-yoy", "children"),
     Output("stands-available-yoy", "children"),
     Output("stands-reserved-yoy", "children"),
     Output("report-data-store", "children")],
    [Input("time-filter-radio", "value"),
     Input("year-dropdown", "value")],
    prevent_initial_call=False
)
def update_dashboard_metrics(time_filter, selected_year):
    engine = get_user_db_engine()
    
    period_label_map = {
        "daily": "Today",
        "weekly": "Last 7 Days",
        "yearly": f"Year: {selected_year}",
        "forecast": f"Forecast for {selected_year}" if ML_AVAILABLE else f"Year: {selected_year}"
    }
    
    period_text = period_label_map.get(time_filter, "Period: --")
    
    if not engine:
        not_connected_alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Not connected to database. Please connect first."
        ], color="warning")
        
        return ["$0", "0", "0", "0", 
                period_text, period_text, period_text, period_text,
                create_simple_yoy_indicator(0, 0), 
                create_simple_yoy_indicator(0, 0), 
                create_simple_yoy_indicator(0, 0), 
                create_simple_yoy_indicator(0, 0), 
                "{}"]
    
    try:
        if time_filter == "daily":
            date_condition = "DATE(registration_date) = CURDATE()"
            transaction_date_condition = "DATE(transaction_date) = CURDATE()"
        elif time_filter == "weekly":
            date_condition = "registration_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
            transaction_date_condition = "transaction_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        else:
            date_condition = f"YEAR(registration_date) = {selected_year}"
            transaction_date_condition = f"YEAR(transaction_date) = {selected_year}"
        
        #Total Stand Value
        try:
            total_stand_value_query = f"""
            SELECT SUM(sale_value) AS total_sale_value
            FROM Stands
            WHERE {date_condition}
            """
            stand_value_df = pd.read_sql(total_stand_value_query, engine)
            current_stand_value = stand_value_df.iloc[0]['total_sale_value'] if not stand_value_df.empty and not pd.isna(stand_value_df.iloc[0]['total_sale_value']) else 0
        except Exception as e:
            print(f"Stand value query error: {e}")
            current_stand_value = 0
        formatted_stand_value = f"${current_stand_value:,.2f}" if current_stand_value else "$0"
        
        #Number of Stands Sold
        try:
            stands_sold_query = f"""
            SELECT COUNT(stand_number) AS total_stands_sold
            FROM Stands
            WHERE {date_condition} AND available = 0
            """
            stands_sold_df = pd.read_sql(stands_sold_query, engine)
            current_stands_sold = stands_sold_df.iloc[0]['total_stands_sold'] if not stands_sold_df.empty and not pd.isna(stands_sold_df.iloc[0]['total_stands_sold']) else 0
        except Exception as e:
            print(f"Stands sold query error: {e}")
            current_stands_sold = 0
        formatted_stands_sold = str(current_stands_sold) if current_stands_sold else "0"
        
        # Stands Available for Sale (available = 1 AND to_sale = 1)
        try:
            stands_available_query = f"""
            SELECT COUNT(stand_number) AS total_stands_available
            FROM Stands
            WHERE {date_condition} AND available = 1 AND to_sale = 1
            """
            stands_available_df = pd.read_sql(stands_available_query, engine)
            current_stands_available = stands_available_df.iloc[0]['total_stands_available'] if not stands_available_df.empty and not pd.isna(stands_available_df.iloc[0]['total_stands_available']) else 0
        except Exception as e:
            print(f"Stands available query error: {e}")
            current_stands_available = 0
        formatted_stands_available = str(current_stands_available) if current_stands_available else "0"
        
        # Reserved Stands (available = 1 AND to_sale = 0)
        try:
            stands_reserved_query = f"""
            SELECT COUNT(stand_number) AS total_stands_reserved
            FROM Stands
            WHERE {date_condition} AND available = 1 AND to_sale = 0
            """
            stands_reserved_df = pd.read_sql(stands_reserved_query, engine)
            current_stands_reserved = stands_reserved_df.iloc[0]['total_stands_reserved'] if not stands_reserved_df.empty and not pd.isna(stands_reserved_df.iloc[0]['total_stands_reserved']) else 0
        except Exception as e:
            print(f"Stands reserved query error: {e}")
            current_stands_reserved = 0
        formatted_stands_reserved = str(current_stands_reserved) if current_stands_reserved else "0"
        
        #Total Deposit
        try:
            total_deposit_query = f"""
            SELECT SUM(deposit_amount) AS total_deposit
            FROM customer_accounts
            WHERE {date_condition} AND deleted = 0
            """
            deposit_df = pd.read_sql(total_deposit_query, engine)
            current_deposit = deposit_df.iloc[0]['total_deposit'] if not deposit_df.empty and not pd.isna(deposit_df.iloc[0]['total_deposit']) else 0
        except Exception as e:
            print(f"Deposit query error: {e}")
            current_deposit = 0
        
        #Total Installment
        try:
            total_installment_query = f"""
            SELECT SUM(amount) AS total_installment
            FROM customer_account_invoices
            WHERE {transaction_date_condition} AND description = 'Instalment' AND deleted = 0
            """
            installment_df = pd.read_sql(total_installment_query, engine)
            current_installment = installment_df.iloc[0]['total_installment'] if not installment_df.empty and not pd.isna(installment_df.iloc[0]['total_installment']) else 0
        except Exception as e:
            print(f"Installment query error: {e}")
            current_installment = 0
        
        report_data = {
            'total_stand_value': formatted_stand_value,
            'stands_sold': formatted_stands_sold,
            'stands_available': formatted_stands_available,
            'stands_reserved': formatted_stands_reserved,
            'period_text': period_text
        }
        report_data_json = json.dumps(report_data)
        
        def calculate_yoy_change(current, previous):
            if previous == 0:
                if current == 0:
                    return 0, 0
                else:
                    return float('inf'), previous  # Return infinity for +∞%
            else:
                change = ((current - previous) / previous) * 100
                return change, previous
        
        if time_filter == "yearly":
            previous_year = selected_year - 1
            
            try:
                prev_stand_query = f"""
                SELECT SUM(sale_value) AS total_sale_value
                FROM Stands
                WHERE YEAR(registration_date) = {previous_year}
                """
                prev_stand_df = pd.read_sql(prev_stand_query, engine)
                previous_stand_value = prev_stand_df.iloc[0]['total_sale_value'] if not prev_stand_df.empty and not pd.isna(prev_stand_df.iloc[0]['total_sale_value']) else 0
            except:
                previous_stand_value = 0
                
            try:
                prev_sold_query = f"""
                SELECT COUNT(stand_number) AS total_stands_sold
                FROM Stands
                WHERE YEAR(registration_date) = {previous_year} AND available = 0
                """
                prev_sold_df = pd.read_sql(prev_sold_query, engine)
                previous_stands_sold = prev_sold_df.iloc[0]['total_stands_sold'] if not prev_sold_df.empty and not pd.isna(prev_sold_df.iloc[0]['total_stands_sold']) else 0
            except:
                previous_stands_sold = 0
                
            try:
                prev_available_query = f"""
                SELECT COUNT(stand_number) AS total_stands_available
                FROM Stands
                WHERE YEAR(registration_date) = {previous_year} AND available = 1 AND to_sale = 1
                """
                prev_available_df = pd.read_sql(prev_available_query, engine)
                previous_stands_available = prev_available_df.iloc[0]['total_stands_available'] if not prev_available_df.empty and not pd.isna(prev_available_df.iloc[0]['total_stands_available']) else 0
            except:
                previous_stands_available = 0
                
            try:
                prev_reserved_query = f"""
                SELECT COUNT(stand_number) AS total_stands_reserved
                FROM Stands
                WHERE YEAR(registration_date) = {previous_year} AND available = 1 AND to_sale = 0
                """
                prev_reserved_df = pd.read_sql(prev_reserved_query, engine)
                previous_stands_reserved = prev_reserved_df.iloc[0]['total_stands_reserved'] if not prev_reserved_df.empty and not pd.isna(prev_reserved_df.iloc[0]['total_stands_reserved']) else 0
            except:
                previous_stands_reserved = 0
            
            # Calculate YoY changes
            stand_value_change, stand_value_prev = calculate_yoy_change(current_stand_value, previous_stand_value)
            stands_sold_change, stands_sold_prev = calculate_yoy_change(current_stands_sold, previous_stands_sold)
            stands_available_change, stands_available_prev = calculate_yoy_change(current_stands_available, previous_stands_available)
            stands_reserved_change, stands_reserved_prev = calculate_yoy_change(current_stands_reserved, previous_stands_reserved)
            
            # Create simple indicators
            stand_value_yoy = create_simple_yoy_indicator(stand_value_change, stand_value_prev)
            stands_sold_yoy = create_simple_yoy_indicator(stands_sold_change, stands_sold_prev)
            stands_available_yoy = create_simple_yoy_indicator(stands_available_change, stands_available_prev)
            stands_reserved_yoy = create_simple_yoy_indicator(stands_reserved_change, stands_reserved_prev)

        else:
            # For non-yearly periods, use simple indicators
            stand_value_yoy = create_simple_yoy_indicator(0, 0)
            stands_sold_yoy = create_simple_yoy_indicator(0, 0)
            stands_available_yoy = create_simple_yoy_indicator(0, 0)
            stands_reserved_yoy = create_simple_yoy_indicator(0, 0)
        
        return [formatted_stand_value, formatted_stands_sold, formatted_stands_available, 
                formatted_stands_reserved, 
                period_text, period_text, period_text, period_text,
                stand_value_yoy, stands_sold_yoy, stands_available_yoy, stands_reserved_yoy, 
                report_data_json]
        
    except Exception as e:
        print(f"Main callback error: {e}")
        
        # Return default values with simple indicators on error
        return ["$0", "0", "0", "0", 
                period_text, period_text, period_text, period_text,
                create_simple_yoy_indicator(0, 0), 
                create_simple_yoy_indicator(0, 0), 
                create_simple_yoy_indicator(0, 0), 
                create_simple_yoy_indicator(0, 0), 
                "{}"]
    finally:
        if engine:
            try:
                engine.dispose()
            except:
                pass