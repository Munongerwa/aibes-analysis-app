import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, callback
from flask import session
from sqlalchemy import create_engine
import pandas as pd
import plotly.graph_objs as go
import datetime
import dash

# Function to get user-specific database engine
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
    html.H1([
        html.I(className="fas fa-map-marked-alt me-2"),
        "Land Bank Analysis"
    ], className="mt-3 mb-4 text-center"),
    
    # Connection status indicator
    html.Div(id="land-bank-connection-status"),
    
    # Hidden div to store active time filter level
    html.Div(id="land-bank-time-level", style={"display": "none"}, children="year"),
    
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-filter me-2"),
                        "Analysis Filters"
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Filter Level", className="mb-2"),
                                dbc.ButtonGroup([
                                    dbc.Button("Year", id="level-year", color="primary"),
                                    dbc.Button("Month", id="level-month", color="secondary", outline=True),
                                    dbc.Button("Week", id="level-week", color="secondary", outline=True),
                                    dbc.Button("Day", id="level-day", color="secondary", outline=True)
                                ], id="land-bank-level-toggle", className="mb-3")
                            ], width=12),
                            
                            dbc.Col([
                                dbc.Label("Select Year", className="mb-2"),
                                dcc.Dropdown(
                                    id="land-bank-year-dropdown",
                                    options=[
                                        {'label': str(year), 'value': year} 
                                        for year in range(datetime.datetime.now().year, datetime.datetime.now().year - 5, -1)
                                    ],
                                    value=datetime.datetime.now().year,
                                    clearable=False,
                                    className="mb-2"
                                )
                            ], width=3),
                            
                            dbc.Col([
                                dbc.Label("Select Month", className="mb-2"),
                                dcc.Dropdown(
                                    id="land-bank-month-dropdown",
                                    options=[
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
                                    value=datetime.datetime.now().month,
                                    clearable=False,
                                    className="mb-2"
                                )
                            ], width=3),
                            
                            dbc.Col([
                                dbc.Label("Select Week", className="mb-2"),
                                dcc.Dropdown(
                                    id="land-bank-week-dropdown",
                                    options=[],
                                    placeholder="Select week",
                                    className="mb-2"
                                )
                            ], width=3),
                            
                            dbc.Col([
                                dbc.Label("Select Day", className="mb-2"),
                                dcc.Dropdown(
                                    id="land-bank-day-dropdown",
                                    options=[],
                                    placeholder="Select day",
                                    className="mb-2"
                                )
                            ], width=3),
                        ]),
                        
                        dbc.Button([
                            html.I(className="fas fa-sync me-2"),
                            "Refresh Analysis"
                        ], id="refresh-land-bank-button", color="primary", className="w-100")
                    ])
                ])
            ], width=12)
        ], className="mb-3"),
        
        # Metric Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H4("Total Stands", className="card-title text-center"),
                            html.H2(id="total-stands", children="0 stands", className="text-center text-success fw-bold"),
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=6, md=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H4("Available Stands", className="card-title text-center"),
                            html.H2(id="available-stands", children="0 stands", className="text-center text-primary fw-bold"),
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=6, md=4),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H4("Commercial Stands", className="card-title text-center"),
                            html.H2(id="commercial-stands", children="0 stands", className="text-center text-warning fw-bold"),
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=6, md=4, className="mb-2"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H4("Residential Stands", className="card-title text-center"),
                            html.H2(id="residential-stands", children="0 stands", className="text-center text-info fw-bold"),
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=6, md=4),
            
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H4("Sold Stands", className="card-title text-center"),
                            html.H2(id="sold-stands", children="0 stands", className="text-center text-secondary fw-bold"),
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=6, md=4)
        ], className="mb-4"),
        
        # Charts
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-pie me-2"),
                        "Land Distribution by Status"
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="land-status-pie-chart", style={"height": "400px"})
                    ])
                ], className="mb-4")
            ], width=12, md=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-bar me-2"),
                        "Project Comparison"
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="land-project-bar-chart", style={"height": "400px"})
                    ])
                ], className="mb-4")
            ], width=12, md=6)
        ])
    ], className="mt-4", fluid=True)
])

# Callback to manage level button states
@callback(
    [Output("level-year", "color"),
     Output("level-month", "color"),
     Output("level-week", "color"),
     Output("level-day", "color"),
     Output("level-year", "outline"),
     Output("level-month", "outline"),
     Output("level-week", "outline"),
     Output("level-day", "outline"),
     Output("land-bank-time-level", "children")],
    [Input("level-year", "n_clicks"),
     Input("level-month", "n_clicks"),
     Input("level-week", "n_clicks"),
     Input("level-day", "n_clicks")],
    prevent_initial_call=False
)
def update_level_buttons(year_clicks, month_clicks, week_clicks, day_clicks):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        # Default to year
        return "primary", "secondary", "secondary", "secondary", False, True, True, True, "year"
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "level-year":
        return "primary", "secondary", "secondary", "secondary", False, True, True, True, "year"
    elif button_id == "level-month":
        return "secondary", "primary", "secondary", "secondary", True, False, True, True, "month"
    elif button_id == "level-week":
        return "secondary", "secondary", "primary", "secondary", True, True, False, True, "week"
    elif button_id == "level-day":
        return "secondary", "secondary", "secondary", "primary", True, True, True, False, "day"
    
    # Default fallback
    return "primary", "secondary", "secondary", "secondary", False, True, True, True, "year"

# Callback to populate week dropdown based on year and month
@callback(
    Output("land-bank-week-dropdown", "options"),
    [Input("land-bank-year-dropdown", "value"),
     Input("land-bank-month-dropdown", "value")]
)
def populate_weeks(selected_year, selected_month):
    try:
        # Get weeks in the selected month
        import calendar
        weeks = []
        cal = calendar.monthcalendar(selected_year, selected_month)
        
        for week_num, week in enumerate(cal, 1):
            # Find the Monday of the week (or first day if no Monday)
            monday = next((day for day in week if day != 0), 1)
            weeks.append({
                'label': f'Week {week_num} ({monday}-{min(monday+6, calendar.monthrange(selected_year, selected_month)[1])})',
                'value': week_num
            })
        
        return weeks
    except Exception as e:
        print(f"Error populating weeks: {e}")
        return []

# Callback to populate day dropdown based on year, month, and week
@callback(
    Output("land-bank-day-dropdown", "options"),
    [Input("land-bank-year-dropdown", "value"),
     Input("land-bank-month-dropdown", "value"),
     Input("land-bank-week-dropdown", "value")]
)
def populate_days(selected_year, selected_month, selected_week):
    try:
        if not selected_week:
            return []
            
        # Get days in the selected week
        import calendar
        cal = calendar.monthcalendar(selected_year, selected_month)
        
        if selected_week <= len(cal):
            week = cal[selected_week - 1]
            days = [{'label': f'Day {day}', 'value': day} for day in week if day != 0]
            return days
        else:
            return []
    except Exception as e:
        print(f"Error populating days: {e}")
        return []

#callback for land bank analysis
@callback(
    [Output("land-bank-connection-status", "children"),
     Output("total-stands", "children"),
     Output("available-stands", "children"),
     Output("sold-stands", "children"),
     Output("commercial-stands", "children"),
     Output("residential-stands", "children"),
     Output("land-status-pie-chart", "figure"),
     Output("land-project-bar-chart", "figure")],
    [Input("refresh-land-bank-button", "n_clicks")],
    [Input("land-bank-time-level", "children"),
     Input("land-bank-year-dropdown", "value"),
     Input("land-bank-month-dropdown", "value"),
     Input("land-bank-week-dropdown", "value"),
     Input("land-bank-day-dropdown", "value")]
)
def update_land_bank_analysis(n_clicks, time_level, selected_year, selected_month, selected_week, selected_day):
    engine = get_user_db_engine()
    
    if not engine:
        not_connected_alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Not connected to database. Please connect first."
        ], color="warning")
        
        empty_fig = go.Figure()
        empty_fig.update_layout(title="No Data - Please Connect to Database")
        
        return [not_connected_alert, "0 stands", "0 stands", "0 stands", "0 stands", "0 stands", empty_fig, empty_fig]
    
    try:
        # creating date condition based on time level
        if time_level == "year":
            date_condition = f"YEAR(s.registration_date) = {selected_year}"
            period_label = f"Year {selected_year}"
        elif time_level == "month":
            date_condition = f"YEAR(s.registration_date) = {selected_year} AND MONTH(s.registration_date) = {selected_month}"
            month_name = datetime.date(1900, selected_month, 1).strftime('%B')
            period_label = f"{month_name} {selected_year}"
        elif time_level == "week":
            if selected_week:
                # Approximate week calculation
                date_condition = f"YEAR(s.registration_date) = {selected_year} AND MONTH(s.registration_date) = {selected_month} AND WEEK(s.registration_date) = WEEK('{selected_year}-{selected_month:02d}-01') + {selected_week - 1}"
                period_label = f"Week {selected_week}, {datetime.date(1900, selected_month, 1).strftime('%B')} {selected_year}"
            else:
                date_condition = f"YEAR(s.registration_date) = {selected_year} AND MONTH(s.registration_date) = {selected_month}"
                period_label = f"{datetime.date(1900, selected_month, 1).strftime('%B')} {selected_year}"
        elif time_level == "day":
            if selected_day:
                date_condition = f"YEAR(s.registration_date) = {selected_year} AND MONTH(s.registration_date) = {selected_month} AND DAY(s.registration_date) = {selected_day}"
                period_label = f"Day {selected_day}, {datetime.date(1900, selected_month, 1).strftime('%B')} {selected_year}"
            else:
                date_condition = f"YEAR(s.registration_date) = {selected_year} AND MONTH(s.registration_date) = {selected_month}"
                period_label = f"{datetime.date(1900, selected_month, 1).strftime('%B')} {selected_year}"
        else:
            date_condition = f"YEAR(s.registration_date) = {selected_year}"
            period_label = f"Year {selected_year}"
        
        where_clause = f"WHERE {date_condition}"
        
        # TOTAL STANDS
        total_stands_query = f"""
        SELECT COUNT(s.stand_number) AS total_stands 
        FROM Stands s
        INNER JOIN Projects p ON s.project_id = p.id
        {where_clause}
        """
        total_df = pd.read_sql(total_stands_query, engine)
        total_stands = total_df.iloc[0]['total_stands'] if not total_df.empty and total_df.iloc[0]['total_stands'] else 0
        formatted_total_stands = f"{total_stands:,.0f} stands" if total_stands else "0 stands"
        
        # Available Land stands
        available_stands_query = f"""
        SELECT COUNT(s.stand_number) AS available_stands 
        FROM Stands s
        INNER JOIN Projects p ON s.project_id = p.id
        {where_clause} AND s.available = 1
        """
        available_df = pd.read_sql(available_stands_query, engine)
        available_stands = available_df.iloc[0]['available_stands'] if not available_df.empty and available_df.iloc[0]['available_stands'] else 0
        formatted_available_stands = f"{available_stands:,.0f} stands" if available_stands else "0 stands"
        
        #STANDS sold
        sold_stands_query = f"""
        SELECT COUNT(s.stand_number) AS sold_stands 
        FROM Stands s
        INNER JOIN Projects p ON s.project_id = p.id
        {where_clause} AND s.available = 0
        """
        sold_df = pd.read_sql(sold_stands_query, engine)
        sold_stands = sold_df.iloc[0]['sold_stands'] if not sold_df.empty and sold_df.iloc[0]['sold_stands'] else 0
        formatted_sold_stands = f"{sold_stands:,.0f} stands" if sold_stands else "0 stands"

        #commercial stands sold
        commercial_stands_query = f"""
        SELECT COUNT(s.stand_number) AS commercial_stands 
        FROM Stands s
        INNER JOIN Projects p ON s.project_id = p.id
        {where_clause} AND s.available = 0 AND s.property_description_id = 2
        """
        commercial_df = pd.read_sql(commercial_stands_query, engine)
        commercial_stands = commercial_df.iloc[0]['commercial_stands'] if not commercial_df.empty and commercial_df.iloc[0]['commercial_stands'] else 0
        formatted_commercial_stands = f"{commercial_stands:,.0f} stands" if commercial_stands else "0 stands"

        #residential stands sold
        residential_stands_query = f"""
        SELECT COUNT(s.stand_number) AS residential_stands 
        FROM Stands s
        INNER JOIN Projects p ON s.project_id = p.id
        {where_clause} AND s.available = 0 AND s.property_description_id = 1
        """
        residential_df = pd.read_sql(residential_stands_query, engine)
        residential_stands = residential_df.iloc[0]['residential_stands'] if not residential_df.empty and residential_df.iloc[0]['residential_stands'] else 0
        formatted_residential_stands = f"{residential_stands:,.0f} stands" if residential_stands else "0 stands"

        # Land distribution by status
        status_query = f"""
        SELECT s.available, COUNT(s.stand_number) AS count 
        FROM Stands s
        INNER JOIN Projects p ON s.project_id = p.id
        {where_clause} 
        GROUP BY s.available
        """
        status_df = pd.read_sql(status_query, engine)
        
        if not status_df.empty:
            # Create meaningful labels for availability status
            status_labels = []
            for _, row in status_df.iterrows():
                if row['available'] == 1:
                    status_labels.append("Available")
                else:
                    status_labels.append("Sold")
            
            pie_fig = go.Figure(data=[go.Pie(
                labels=status_labels, 
                values=status_df['count'],
                hole=0.6,
                hovertemplate='<b>%{label}</b><br>' +
                             'Stands: %{value:,}<br>' +
                             '(%{percent})<extra></extra>'
            )])
            pie_fig.update_layout(
                title=f"Land Distribution by Status ({period_label})",
                showlegend=True
            )
        else:
            pie_fig = go.Figure()
            pie_fig.update_layout(title="No Data Available")
        
        # Project comparison chart
        project_query = f"""
        SELECT 
            p.name AS project_name,
            p.id AS project_id,
            COUNT(s.stand_number) AS total_stands,
            COUNT(CASE WHEN s.available = 1 THEN 1 END) AS available_stands,
            COUNT(CASE WHEN s.available = 0 THEN 1 END) AS sold_stands
        FROM Projects p
        INNER JOIN Stands s ON p.id = s.project_id
        {where_clause} 
        GROUP BY p.id, p.name
        ORDER BY total_stands DESC
        """
        project_df = pd.read_sql(project_query, engine)
        
        if not project_df.empty:
            # combined labels with project name and ID
            project_labels = [f"{row['project_name']} (ID: {row['project_id']})" for _, row in project_df.iterrows()]
            
            # bar chart showing available vs sold stands for all projects
            bar_fig = go.Figure()
            
            bar_fig.add_trace(go.Bar(
                name='Available',
                x=project_labels,
                y=project_df['available_stands'],
                marker_color='lightgreen',
                text=[f"{stands:,.0f}" for stands in project_df['available_stands']],
                textposition='auto'
            ))
            
            bar_fig.add_trace(go.Bar(
                name='Sold',
                x=project_labels,
                y=project_df['sold_stands'],
                marker_color='lightcoral',
                text=[f"{stands:,.0f}" for stands in project_df['sold_stands']],
                textposition='auto'
            ))
            
            bar_fig.update_layout(
                title=f"Project Comparison - Available vs Sold ({period_label})",
                xaxis_title="Project",
                yaxis_title="Number of Stands",
                barmode='group',
                xaxis_tickangle=-45,
                hovermode='closest',
                height=400
            )
        else:
            bar_fig = go.Figure()
            bar_fig.update_layout(title="No Data Available")
        
        status = dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            f"Connected to database successfully! Showing data for {period_label}"
        ], color="success")
        
        return [status, formatted_total_stands, formatted_available_stands, formatted_sold_stands, formatted_commercial_stands, formatted_residential_stands, pie_fig, bar_fig]
        
    except Exception as e:
        error_alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Database error: {str(e)}"
        ], color="danger")
        
        empty_fig = go.Figure()
        empty_fig.update_layout(title="Error Loading Data")
        
        return [error_alert, "0 stands", "0 stands", "0 stands", "0 stands", "0 stands", empty_fig, empty_fig]
    finally:
        if engine:
            engine.dispose()