import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, callback, ctx, State, dash_table
from flask import session
from sqlalchemy import create_engine
import pandas as pd
import plotly.graph_objs as go
import datetime
import calendar
import io
import base64

#get user-specific database engine
def get_user_db_engine():
    if 'db_connection_string' in session and session['db_connection_string']:
        try:
            engine = create_engine(session['db_connection_string'])
            return engine
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    return None

layout = html.Div([
    dbc.Container([
    html.H1([
        html.I(className="fas fa-project-diagram me-2"),
        "Project Analysis"
    ], className="mt-3 mb-4 text-center"),
    
    dbc.Container([
        # Filter Section - Similar to Dashboard Layout
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Button([
                        html.I(className="fas fa-filter me-1"),
                        "Show Filters"
                    ], id="project-filter-toggle-btn", color="primary", size="sm", className="btn-sm"),
                ], className="d-flex align-items-center justify-content-end mb-3")
            ], width=12)
        ]),
        
        dbc.Collapse([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        # Year Filter
                        dbc.Col([
                            html.Div([
                                html.Small([
                                    html.I(className="fas fa-calendar-alt me-1"),
                                    "Select Year"
                                ], className="text-muted mb-1 d-block fw-bold"),
                                dcc.Dropdown(
                                    id="project-year-dropdown",
                                    options=[
                                        {'label': str(year), 'value': year} 
                                        for year in range(datetime.datetime.now().year, datetime.datetime.now().year - 5, -1)
                                    ],
                                    value=datetime.datetime.now().year,
                                    clearable=False,
                                    className="modern-dropdown",
                                )
                            ], style={"display": "inline-block", "width": "150px"})
                        ], width=12, md=3, className="mb-3 mb-md-0"),
                        
                        # Month Filter
                        dbc.Col([
                            html.Div([
                                html.Small([
                                    html.I(className="fas fa-calendar me-1"),
                                    "Select Month"
                                ], className="text-muted mb-1 d-block fw-bold"),
                                dcc.Dropdown(
                                    id="project-month-dropdown",
                                    options=[
                                        {'label': 'All Months', 'value': 0},
                                        {'label': 'January', 'value': 1},
                                        {'label': 'February', 'value': 2},
                                        {'label': 'March', 'value': 3},
                                        {'label': 'April', 'value': 4},
                                        {'label': 'May', 'value': 5},
                                        {'label': 'June', 'value': 6},
                                        {'label': 'July', 'value': 7},
                                        {'label': 'August', 'value': 8},
                                        {'label': 'September', 'value': 9},
                                        {'label': 'October', 'value': 10},
                                        {'label': 'November', 'value': 11},
                                        {'label': 'December', 'value': 12}
                                    ],
                                    value=0,
                                    clearable=False,
                                    className="modern-dropdown",
                                )
                            ])
                        ], width=12, md=3, className="mb-3 mb-md-0"),
                        
                        # Week Filter - Updated to match settings.py format
                        dbc.Col([
                            html.Div([
                                html.Small([
                                    html.I(className="fas fa-calendar-week me-1"),
                                    "Select Week"
                                ], className="text-muted mb-1 d-block fw-bold"),
                                dcc.Dropdown(
                                    id="project-week-dropdown",
                                    options=[],
                                    placeholder="Select week",
                                    className="modern-dropdown"
                                )
                            ])
                        ], width=12, md=3, className="mb-3 mb-md-0"),
                        
                        # Project Filter
                        dbc.Col([
                            html.Div([
                                html.Small([
                                    html.I(className="fas fa-project-diagram me-1"),
                                    "Select Project"
                                ], className="text-muted mb-1 d-block fw-bold"),
                                dcc.Dropdown(
                                    id="project-project-dropdown",
                                    options=[],
                                    placeholder="All Projects",
                                    className="modern-dropdown"
                                )
                            ])
                        ], width=12, md=3, className="mb-3 mb-md-0"),
                    ], className="g-3 align-items-end")
                ], style={"minHeight": "300px", "paddingBottom": "20px"})
            ], className="shadow-sm mb-4")
        ], id="project-filter-collapse", is_open=False),  # Initially closed
        
        # KPI Cards Row - Updated with Stands metrics
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-box-open fa-lg text-success"),
                            ], className="d-flex justify-content-center mb-2"),
                            html.H4("Stands Sold", className="card-title text-center mb-1"),
                            html.H2(id="stands-sold", children="0", className="text-center text-success fw-bold mb-1"),
                            html.Small("Stands with owners", className="text-center text-muted d-block")
                        ], className="text-center")
                    ])
                ], className="shadow-lg h-100", style={"borderLeft": "4px solid #28a745"})
            ], width=12, md=6, lg=3, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-lock fa-lg text-warning"),
                            ], className="d-flex justify-content-center mb-2"),
                            html.H4("Stands Reserved", className="card-title text-center mb-1"),
                            html.H2(id="stands-reserved", children="0", className="text-center text-warning fw-bold mb-1"),
                            html.Small("Reserved stands", className="text-center text-muted d-block")
                        ], className="text-center")
                    ])
                ], className="shadow-lg h-100", style={"borderLeft": "4px solid #ffc107"})
            ], width=12, md=6, lg=3, className="mb-3"),

           dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-store fa-lg text-info"),
                            ], className="d-flex justify-content-center mb-2"),
                            html.H4("Stands Available", className="card-title text-center mb-1"),
                            html.H2(id="stands-available", children="0", className="text-center text-info fw-bold mb-1"),
                            html.Small("Stands for sale", className="text-center text-muted d-block")
                        ], className="text-center")
                    ])
                ], className="shadow-lg h-100", style={"borderLeft": "4px solid #17a2b8"})
            ], width=12, md=6, lg=3, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-project-diagram fa-lg text-primary"),
                            ], className="d-flex justify-content-center mb-2"),
                            html.H4("Total Projects", className="card-title text-center mb-1"),
                            html.H2(id="total-projects", children="0", className="text-center text-primary fw-bold mb-1"),
                            html.Small("Active projects", className="text-center text-muted d-block")
                        ], className="text-center")
                    ])
                ], className="shadow-lg h-100", style={"borderLeft": "4px solid #007bff"})
            ], width=12, md=6, lg=3, className="mb-3"),
        ], className="mb-4"),
                        
        # Refresh Button
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Button([
                        html.I(className="fas fa-sync me-2"),
                        "Refresh Analysis"
                    ], id="refresh-project-button", color="primary", className="w-100 w-md-auto")
                ], className="d-flex justify-content-center justify-content-md-start mb-4")
            ], width=12)
        ]),
    
        # Charts - Updated with donut chart
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.I(className="fas fa-bullseye me-2"),
                            "Stands Sold vs Target by Project",
                            html.Div([
                                dbc.Button([
                                    html.I(className="fas fa-table me-1"),
                                    "View Data"
                                ], id="toggle-project-data-btn", color="link", size="sm", className="ms-2"),
                                dcc.Download(id="download-project-csv")
                            ], className="float-end")
                        ], className="d-flex justify-content-between align-items-center")
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="stands-target-comparison-chart", style={"height": "400px"}),
                        dbc.Collapse([
                            html.Div([
                                dash_table.DataTable(
                                    id="project-data-table",
                                    columns=[],
                                    data=[],
                                    page_size=10,
                                    style_table={'overflowX': 'auto'},
                                    style_cell={
                                        'textAlign': 'left',
                                        'padding': '10px',
                                        'fontFamily': 'Arial, sans-serif'
                                    },
                                    style_header={
                                        'backgroundColor': '#007bff',
                                        'color': 'white',
                                        'fontWeight': 'bold'
                                    },
                                    style_data_conditional=[
                                        {
                                            'if': {'row_index': 'odd'},
                                            'backgroundColor': '#f8f9fa'
                                        }
                                    ]
                                ),
                                html.Div([
                                    dbc.Button([
                                        html.I(className="fas fa-download me-1"),
                                        "Download CSV"
                                    ], id="download-project-data-btn", color="primary", size="sm", className="mt-2")
                                ], className="d-flex justify-content-end")
                            ], className="mt-3")
                        ], id="project-data-collapse", is_open=False)
                    ])
                ], className="mb-4 shadow")
            ], width=12, lg=12),

        ]),
        dbc.Row([
                        
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-pie me-2"),
                        "Residential vs Commercial Stands"
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="residential-commercial-chart", style={"height": "400px"})
                    ])
                ], className="mb-4 shadow")
            ], width=12, lg=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.I(className="fas fa-user-tie me-2"),
                            "Agent Performance - Stands Sold",
                            html.Div([
                                dbc.Button([
                                    html.I(className="fas fa-table me-1"),
                                    "View Data"
                                ], id="toggle-agent-data-btn", color="link", size="sm", className="ms-2"),
                                dcc.Download(id="download-agent-csv")
                            ], className="float-end")
                        ], className="d-flex justify-content-between align-items-center")
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="agent-performance-chart", style={"height": "400px"}),
                        dbc.Collapse([
                            html.Div([
                                dash_table.DataTable(
                                    id="agent-data-table",
                                    columns=[],
                                    data=[],
                                    page_size=10,
                                    style_table={'overflowX': 'auto'},
                                    style_cell={
                                        'textAlign': 'left',
                                        'padding': '10px',
                                        'fontFamily': 'Arial, sans-serif'
                                    },
                                    style_header={
                                        'backgroundColor': '#007bff',
                                        'color': 'white',
                                        'fontWeight': 'bold'
                                    },
                                    style_data_conditional=[
                                        {
                                            'if': {'row_index': 'odd'},
                                            'backgroundColor': '#f8f9fa'
                                        }
                                    ]
                                ),
                                html.Div([
                                    dbc.Button([
                                        html.I(className="fas fa-download me-1"),
                                        "Download CSV"
                                    ], id="download-agent-data-btn", color="primary", size="sm", className="mt-2")
                                ], className="d-flex justify-content-end")
                            ], className="mt-3")
                        ], id="agent-data-collapse", is_open=False)
                    ])
                ], className="mb-4 shadow")
            ], width=12)
        ])
    ], className="mt-4", fluid=True)
    ], className="mt-4", fluid=True, style={"paddingTop": "20px"})
])

# Callback to toggle filter section
@callback(
    [Output("project-filter-collapse", "is_open"),
     Output("project-filter-toggle-btn", "children")],
    Input("project-filter-toggle-btn", "n_clicks"),
    State("project-filter-collapse", "is_open"),
    prevent_initial_call=False
)
def toggle_project_filter_collapse(n_clicks, is_open):
    if n_clicks:
        new_state = not is_open
        button_text = [html.I(className="fas fa-filter me-1"), "Hide Filters"] if new_state else [html.I(className="fas fa-filter me-1"), "Show Filters"]
        return new_state, button_text
    return is_open, [html.I(className="fas fa-filter me-1"), "Show Filters"]

# Callback to populate week dropdown - Updated to match settings.py format
@callback(
    Output("project-week-dropdown", "options"),
    [Input("project-year-dropdown", "value"),
     Input("project-month-dropdown", "value")]
)
def populate_weeks(selected_year, selected_month):
    if selected_month == 0:  # All months
        return []
    
    try:
        # Use ISO calendar week system to match settings.py
        # Get the first day of the selected month
        first_day = datetime.date(selected_year, selected_month, 1)
        # Get the last day of the selected month
        last_day = datetime.date(selected_year, selected_month, calendar.monthrange(selected_year, selected_month)[1])
        
        # Get ISO week numbers for first and last day
        first_week = first_day.isocalendar()[1]
        last_week = last_day.isocalendar()[1]
        year_of_first_week = first_day.isocalendar()[0]
        year_of_last_week = last_day.isocalendar()[0]
        
        # Handle year boundary cases (week 52/53 to week 1 transition)
        if last_week < first_week:
            # Month spans year boundary, weeks go from first_week of current year to last_week of next year
            weeks = []
            # Add remaining weeks of current year
            for week_num in range(first_week, 53):  # Up to week 52
                weeks.append({
                    'label': f'Week {week_num} ({selected_year})',
                    'value': week_num
                })
            # Add beginning weeks of next year
            for week_num in range(1, last_week + 1):
                weeks.append({
                    'label': f'Week {week_num} ({selected_year + 1})',
                    'value': week_num + 100  # Add 100 to distinguish next year weeks
                })
        else:
            # Normal case: all weeks in same year
            weeks = []
            for week_num in range(first_week, last_week + 1):
                weeks.append({
                    'label': f'Week {week_num} ({selected_year})',
                    'value': week_num
                })
        
        return weeks
    except Exception as e:
        print(f"Error populating weeks: {e}")
        return []

# loading project options, callback
@callback(
    Output("project-project-dropdown", "options"),
    [Input("project-year-dropdown", "value"),
     Input("project-month-dropdown", "value"),
     Input("project-week-dropdown", "value")]
)
def load_project_options(selected_year, selected_month, selected_week):
    engine = get_user_db_engine()
    if not engine:
        return []
    
    try:
        # Build WHERE clause for project options based on time filters
        where_conditions = [f"YEAR(s.registration_date) = {selected_year}"]
        
        if selected_month and selected_month != 0:
            where_conditions.append(f"MONTH(s.registration_date) = {selected_month}")
            
        if selected_week and selected_month and selected_month != 0:
            # Calculate date range based on ISO week number
            week_start_date, week_end_date = get_week_date_range(selected_year, selected_month, selected_week)
            if week_start_date and week_end_date:
                where_conditions.append(f"s.registration_date >= '{week_start_date}'")
                where_conditions.append(f"s.registration_date <= '{week_end_date}'")
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Get projects with their names
        query = f"""
        SELECT DISTINCT p.id AS project_id, p.name AS project_name
        FROM Projects p
        INNER JOIN Stands s ON p.id = s.project_id
        {where_clause}
        ORDER BY p.name
        """
        df = pd.read_sql(query, engine)
        options = [{'label': f"{row['project_name']} (ID: {row['project_id']})", 'value': row['project_id']} for _, row in df.iterrows()]
        options.insert(0, {'label': 'All Projects', 'value': 0})
        return options
    except Exception as e:
        print(f"Error loading project options: {e}")
        return []
    finally:
        if engine:
            engine.dispose()

# Helper function to calculate week date range
def get_week_date_range(year, month, week_value):
    """Calculate start and end dates for a given week"""
    try:
        if week_value > 100:
            # This is a week from next year (handled in populate_weeks)
            week_num = week_value - 100
            target_year = year + 1
        else:
            week_num = week_value
            target_year = year
            
        # Find the date for the Monday of the specified ISO week
        # ISO week 1 is the first week with at least 4 days in the new year
        jan_4 = datetime.date(target_year, 1, 4)  # January 4th is always in week 1
        week_1_monday = jan_4 - datetime.timedelta(days=jan_4.weekday())
        
        # Calculate the Monday of the target week
        target_monday = week_1_monday + datetime.timedelta(weeks=week_num - 1)
        target_sunday = target_monday + datetime.timedelta(days=6)
        
        # But we need to make sure it's within the selected month
        month_start = datetime.date(year, month, 1)
        month_end = datetime.date(year, month, calendar.monthrange(year, month)[1])
        
        # Adjust week boundaries to stay within the month
        start_date = max(target_monday, month_start)
        end_date = min(target_sunday, month_end)
        
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    except Exception as e:
        print(f"Error calculating week date range: {e}")
        return None, None

# Toggle callbacks for data tables
@callback(
    Output("project-data-collapse", "is_open"),
    Input("toggle-project-data-btn", "n_clicks"),
    State("project-data-collapse", "is_open"),
)
def toggle_project_data(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@callback(
    Output("agent-data-collapse", "is_open"),
    Input("toggle-agent-data-btn", "n_clicks"),
    State("agent-data-collapse", "is_open"),
)
def toggle_agent_data(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

# Download callbacks
@callback(
    Output("download-project-csv", "data"),
    Input("download-project-data-btn", "n_clicks"),
    State("project-data-table", "data"),
    prevent_initial_call=True,
)
def download_project_csv(n_clicks, data):
    if n_clicks and data:
        df = pd.DataFrame(data)
        return dcc.send_data_frame(df.to_csv, "project_analysis_data.csv", index=False)
    return None

@callback(
    Output("download-agent-csv", "data"),
    Input("download-agent-data-btn", "n_clicks"),
    State("agent-data-table", "data"),
    prevent_initial_call=True,
)
def download_agent_csv(n_clicks, data):
    if n_clicks and data:
        df = pd.DataFrame(data)
        return dcc.send_data_frame(df.to_csv, "agent_performance_data.csv", index=False)
    return None

#project analysis callback
@callback(
    [Output("stands-sold", "children"),
     Output("stands-reserved", "children"),
     Output("stands-available", "children"),
     Output("total-projects", "children"),
     Output("stands-target-comparison-chart", "figure"),
     Output("residential-commercial-chart", "figure"),
     Output("agent-performance-chart", "figure"),
     Output("project-data-table", "columns"),
     Output("project-data-table", "data"),
     Output("agent-data-table", "columns"),
     Output("agent-data-table", "data")],
    [Input("refresh-project-button", "n_clicks")],
    [Input("project-year-dropdown", "value"),
     Input("project-month-dropdown", "value"),
     Input("project-week-dropdown", "value"),
     Input("project-project-dropdown", "value")]
)
def update_project_analysis(n_clicks, selected_year, selected_month, selected_week, selected_project):
    engine = get_user_db_engine()
    
    if not engine:
        empty_fig = go.Figure()
        empty_fig.update_layout(title="No Data - Please Connect to Database")
        
        return ["0", "0", "0", "0", empty_fig, empty_fig, empty_fig, [], [], [], []]
    
    try:
        # Build WHERE clause based on all filters for stands data
        where_conditions = [f"YEAR(s.registration_date) = {selected_year}"]
        
        if selected_month and selected_month != 0:
            where_conditions.append(f"MONTH(s.registration_date) = {selected_month}")
            
        if selected_week and selected_month and selected_month != 0:
            # Calculate date range based on ISO week number
            week_start_date, week_end_date = get_week_date_range(selected_year, selected_month, selected_week)
            if week_start_date and week_end_date:
                where_conditions.append(f"s.registration_date >= '{week_start_date}'")
                where_conditions.append(f"s.registration_date <= '{week_end_date}'")
        
        if selected_project and selected_project != 0:
            where_conditions.append(f"s.project_id = {selected_project}")
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Stands metrics
        stands_query = f"""
        SELECT 
            COUNT(CASE WHEN s.available = 0 THEN 1 END) AS stands_sold,
            COUNT(CASE WHEN s.available = 1 AND s.to_sale = 0 THEN 1 END) AS stands_reserved,
            COUNT(CASE WHEN s.available = 1 AND s.to_sale = 1 THEN 1 END) AS stands_available,
            COUNT(DISTINCT s.project_id) AS total_projects
        FROM Stands s
        INNER JOIN Projects p ON s.project_id = p.id
        {where_clause}
        """
        stands_df = pd.read_sql(stands_query, engine)
        
        if not stands_df.empty:
            stands_sold = stands_df.iloc[0]['stands_sold'] if stands_df.iloc[0]['stands_sold'] else 0
            stands_reserved = stands_df.iloc[0]['stands_reserved'] if stands_df.iloc[0]['stands_reserved'] else 0
            stands_available = stands_df.iloc[0]['stands_available'] if stands_df.iloc[0]['stands_available'] else 0
            total_projects = stands_df.iloc[0]['total_projects'] if stands_df.iloc[0]['total_projects'] else 0
        else:
            stands_sold = stands_reserved = stands_available = total_projects = 0
        
        # Residential vs Commercial Stands Donut Chart
        try:
            # Get residential stands count
            residential_stands_query = f"""
            SELECT COUNT(s.stand_number) AS residential_stands 
            FROM Stands s
            INNER JOIN Projects p ON s.project_id = p.id
            {where_clause} AND s.available = 0 AND s.property_description_id = 1
            """
            residential_df = pd.read_sql(residential_stands_query, engine)
            residential_count = residential_df.iloc[0]['residential_stands'] if not residential_df.empty else 0
            
            # Get commercial stands count
            commercial_stands_query = f"""
            SELECT COUNT(s.stand_number) AS commercial_stands 
            FROM Stands s
            INNER JOIN Projects p ON s.project_id = p.id
            {where_clause} AND s.available = 0 AND s.property_description_id = 2
            """
            commercial_df = pd.read_sql(commercial_stands_query, engine)
            commercial_count = commercial_df.iloc[0]['commercial_stands'] if not commercial_df.empty else 0
            
            # Create donut chart
            if residential_count > 0 or commercial_count > 0:
                donut_fig = go.Figure(data=[go.Pie(
                    labels=['Residential', 'Commercial'],
                    values=[residential_count, commercial_count],
                    hole=0.6,
                    marker_colors=["#ea0c2d", '#007bff'],
                    textinfo='label+percent',
                    textfont_size=14
                )])
                
                # Format title with period information
                period_title = str(selected_year)
                if selected_month and selected_month != 0:
                    month_name = calendar.month_name[selected_month]
                    period_title += f" - {month_name}"
                    if selected_week and selected_week != 0:
                        actual_week = selected_week - 100 if selected_week > 100 else selected_week
                        period_title += f" - Week {actual_week}"
                if selected_project and selected_project != 0:
                    # Get project name for title
                    project_name_query = f"SELECT name FROM Projects WHERE id = {selected_project}"
                    try:
                        project_name_df = pd.read_sql(project_name_query, engine)
                        if not project_name_df.empty:
                            project_name = project_name_df.iloc[0]['name']
                            period_title += f" - {project_name}"
                    except Exception:
                        pass
                
                donut_fig.update_layout(
                    title=f'Residential vs Commercial Stands<br><sub>({period_title})</sub>',
                    annotations=[dict(
                        text=f'Total:<br>{residential_count + commercial_count}',
                        x=0.5, y=0.5, font_size=16, showarrow=False
                    )],
                    showlegend=True
                )
            else:
                donut_fig = go.Figure()
                donut_fig.update_layout(title="No Residential/Commercial Data")
        except Exception as e:
            print(f"Error creating residential/commercial chart: {e}")
            donut_fig = go.Figure()
            donut_fig.update_layout(title="No Residential/Commercial Data")
        
        # Stands Sold vs Target Comparison Chart - Updated to use ISO week system
        try:
            # Build date condition for target filtering - using ISO week system
            target_conditions = [f"target_year = {selected_year}"]
            if selected_month and selected_month != 0:
                target_conditions.append(f"target_month = {selected_month}")
                target_type = "monthly"
            else:
                target_type = "yearly"
                target_conditions.append(f"target_type = '{target_type}'")
            
            # Add week condition if selected
            if selected_week and selected_month and selected_month != 0:
                # Adjust week value for next year weeks
                actual_week = selected_week - 100 if selected_week > 100 else selected_week
                target_conditions.append(f"target_week = {actual_week}")
                target_type = "weekly"
            
            target_where_clause = "WHERE " + " AND ".join(target_conditions)
            
            # Get project data with actual stands sold for the selected period
            project_data_query = f"""
            SELECT 
                p.id AS project_id,
                p.name AS project_name,
                COUNT(s.stand_number) AS stands_sold
            FROM Projects p
            INNER JOIN Stands s ON p.id = s.project_id
            {where_clause}
            AND s.available = 0  -- Only count sold stands
            GROUP BY p.id, p.name
            ORDER BY stands_sold DESC
            """
            
            project_data_df = pd.read_sql(project_data_query, engine)
            
            if not project_data_df.empty:
                # Get targets for the selected period with correct target type
                targets_query = f"""
                SELECT 
                    project_id,
                    stands_target
                FROM aibesinsights_project_targets
                {target_where_clause}
                AND target_type = '{target_type}'
                """
                
                try:
                    targets_df = pd.read_sql(targets_query, engine)
                except Exception:
                    # If targets table doesn't exist, create empty dataframe
                    targets_df = pd.DataFrame(columns=['project_id', 'stands_target'])
                
                # Merge actual data with targets
                if not targets_df.empty:
                    comparison_df = pd.merge(
                        project_data_df, 
                        targets_df, 
                        left_on='project_id', 
                        right_on='project_id', 
                        how='left'
                    )
                    comparison_df['stands_target'] = comparison_df['stands_target'].fillna(0)
                else:
                    comparison_df = project_data_df.copy()
                    comparison_df['stands_target'] = 0
                
                if not comparison_df.empty:
                    # Create comparison chart
                    comparison_fig = go.Figure()
                    
                    # Add actual stands sold bars
                    comparison_fig.add_trace(go.Bar(
                        name='Actual Stands Sold',
                        x=comparison_df['project_name'],
                        y=comparison_df['stands_sold'],
                        marker_color='#28a745',
                        text=comparison_df['stands_sold'],
                        textposition='auto'
                    ))
                    
                    # Add target stands bars
                    comparison_fig.add_trace(go.Bar(
                        name='Target Stands',
                        x=comparison_df['project_name'],
                        y=comparison_df['stands_target'],
                        marker_color='#ffc107',
                        text=comparison_df['stands_target'],
                        textposition='auto'
                    ))
                    
                    # Format title with period information
                    period_title = str(selected_year)
                    if selected_month and selected_month != 0:
                        month_name = calendar.month_name[selected_month]
                        period_title += f" - {month_name}"
                        if selected_week and selected_week != 0:
                            actual_week = selected_week - 100 if selected_week > 100 else selected_week
                            period_title += f" - Week {actual_week}"
                    
                    comparison_fig.update_layout(
                        title=f'Stands Sold vs Target by Project ({period_title})',
                        xaxis_title='Project',
                        yaxis_title='Number of Stands',
                        template='plotly_white',
                        barmode='group',
                        xaxis_tickangle=-45,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )
                    
                    # Prepare data table
                    project_table_columns = [{"name": col, "id": col} for col in comparison_df.columns]
                    project_table_data = comparison_df.to_dict('records')
                else:
                    comparison_fig = go.Figure()
                    comparison_fig.update_layout(title="No Data Available")
                    project_table_columns = []
                    project_table_data = []
            else:
                comparison_fig = go.Figure()
                comparison_fig.update_layout(title="No Data Available")
                project_table_columns = []
                project_table_data = []
        except Exception as e:
            print(f"Error creating stands vs target chart: {e}")
            comparison_fig = go.Figure()
            comparison_fig.update_layout(title="No Data Available")
            project_table_columns = []
            project_table_data = []
        
        # Agent Performance Chart - Horizontal bar chart
        try:
            # Build WHERE clause for agent data
            agent_where_conditions = [f"YEAR(ca.registration_date) = {selected_year}"]
            
            if selected_month and selected_month != 0:
                agent_where_conditions.append(f"MONTH(ca.registration_date) = {selected_month}")
                
            if selected_week and selected_month and selected_month != 0:
                # Calculate date range based on ISO week number
                week_start_date, week_end_date = get_week_date_range(selected_year, selected_month, selected_week)
                if week_start_date and week_end_date:
                    agent_where_conditions.append(f"ca.registration_date >= '{week_start_date}'")
                    agent_where_conditions.append(f"ca.registration_date <= '{week_end_date}'")
            
            if selected_project and selected_project != 0:
                agent_where_conditions.append(f"ca.project_id = {selected_project}")
            
            agent_where_clause = "WHERE " + " AND ".join(agent_where_conditions) if agent_where_conditions else ""
            agent_where_clause += " AND ca.agent_name IS NOT NULL AND ca.agent_name != '' AND ca.deleted = 0" if agent_where_clause else "WHERE ca.agent_name IS NOT NULL AND ca.agent_name != '' AND ca.deleted = 0"
            
            # Get agent performance data
            agent_query = f"""
            SELECT 
                ca.agent_name,
                COUNT(*) AS stands_sold
            FROM customer_accounts ca
            INNER JOIN Projects p ON ca.project_id = p.id
            {agent_where_clause}
            GROUP BY ca.agent_name
            ORDER BY stands_sold DESC
            LIMIT 15
            """
            
            agent_df = pd.read_sql(agent_query, engine)
            
            if not agent_df.empty:
                # Create horizontal bar chart
                agent_fig = go.Figure()
                
                agent_fig.add_trace(go.Bar(
                    x=agent_df['stands_sold'],
                    y=agent_df['agent_name'],
                    orientation='h',
                    marker_color="#9b067d",
                    text=agent_df['stands_sold'],
                    textposition='auto'
                ))
                
                # Format title with period information
                period_title = str(selected_year)
                if selected_month and selected_month != 0:
                    month_name = calendar.month_name[selected_month]
                    period_title += f" - {month_name}"
                    if selected_week and selected_week != 0:
                        actual_week = selected_week - 100 if selected_week > 100 else selected_week
                        period_title += f" - Week {actual_week}"
                if selected_project and selected_project != 0:
                    # Get project name for title
                    project_name_query = f"SELECT name FROM Projects WHERE id = {selected_project}"
                    try:
                        project_name_df = pd.read_sql(project_name_query, engine)
                        if not project_name_df.empty:
                            project_name = project_name_df.iloc[0]['name']
                            period_title += f" - {project_name}"
                    except Exception:
                        pass
                
                agent_fig.update_layout(
                    title=f'Agent Performance - Stands Sold ({period_title})',
                    xaxis_title='Number of Stands Sold',
                    yaxis_title='Agent',
                    template='plotly_white',
                    height=max(400, len(agent_df) * 30 + 100)
                )
                
                # Prepare agent data table
                agent_table_columns = [{"name": col, "id": col} for col in agent_df.columns]
                agent_table_data = agent_df.to_dict('records')
            else:
                agent_fig = go.Figure()
                agent_fig.update_layout(title="No Agent Data Available")
                agent_table_columns = []
                agent_table_data = []
        except Exception as e:
            print(f"Error creating agent performance chart: {e}")
            agent_fig = go.Figure()
            agent_fig.update_layout(title="No Agent Data Available")
            agent_table_columns = []
            agent_table_data = []
        
        return [
            str(stands_sold), 
            str(stands_reserved), 
            str(stands_available), 
            str(total_projects), 
            comparison_fig,
            donut_fig,
            agent_fig,
            project_table_columns,
            project_table_data,
            agent_table_columns,
            agent_table_data
        ]
        
    except Exception as e:
        print(f"Error in update_project_analysis: {e}")
        empty_fig = go.Figure()
        empty_fig.update_layout(title="Error Loading Data")
        
        return ["0", "0", "0", "0", empty_fig, empty_fig, empty_fig, [], [], [], []]
    finally:
        if engine:
            engine.dispose()