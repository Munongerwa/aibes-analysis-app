import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, callback
from flask import session
from sqlalchemy import create_engine
import pandas as pd
import plotly.graph_objs as go
import datetime
import calendar

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
    html.H1([
        html.I(className="fas fa-project-diagram me-2"),
        "Project Analysis"
    ], className="mt-3 mb-4 text-center"),
    
    # Connection status
    html.Div(id="project-connection-status"),
    
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
                                dbc.Label("Select Year", className="mb-2"),
                                dcc.Dropdown(
                                    id="project-year-dropdown",
                                    options=[
                                        {'label': str(year), 'value': year} 
                                        for year in range(datetime.datetime.now().year, datetime.datetime.now().year - 5, -1)
                                    ],
                                    value=datetime.datetime.now().year,
                                    clearable=False,
                                    className="mb-3"
                                )
                            ], width=4),
                            
                            dbc.Col([
                                dbc.Label("Select Month", className="mb-2"),
                                dcc.Dropdown(
                                    id="project-month-dropdown",
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
                                    className="mb-3"
                                )
                            ], width=4),
                            
                            dbc.Col([
                                dbc.Label("Select Week", className="mb-2"),
                                dcc.Dropdown(
                                    id="project-week-dropdown",
                                    options=[],
                                    placeholder="Select week",
                                    className="mb-3"
                                )
                            ], width=4),
                            
                            dbc.Col([
                                dbc.Label("Select Project", className="mb-2"),
                                dcc.Dropdown(
                                    id="project-project-dropdown",
                                    options=[],
                                    placeholder="Select a project",
                                    className="mb-3"
                                )
                            ], width=12)
                        ]),
                        
                        dbc.Button([
                            html.I(className="fas fa-sync me-2"),
                            "Refresh Analysis"
                        ], id="refresh-project-button", color="primary", className="w-100")
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H4("Total Projects", className="card-title text-center"),
                            html.H2(id="total-projects", children="0", className="text-center text-success fw-bold"),
                            html.P("Active projects", className="text-center text-muted small")
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=12, md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H4("Total Stands", className="card-title text-center"),
                            html.H2(id="total-project-stands", children="0", className="text-center text-primary fw-bold"),
                            html.P("Across all projects", className="text-center text-muted small")
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=12, md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H4("Avg Sale Value", className="card-title text-center"),
                            html.H2(id="avg-sale-value", children="$0", className="text-center text-info fw-bold"),
                            html.P("Per stand", className="text-center text-muted small")
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=12, md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H4("Completion Rate", className="card-title text-center"),
                            html.H2(id="completion-rate", children="0%", className="text-center text-warning fw-bold"),
                            html.P("Projects completed", className="text-center text-muted small")
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=12, md=3)
        ], className="mb-4"),
        
        # Charts
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-line me-2"),
                        "Weekly Project Progress"
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="project-progress-line-chart", style={"height": "400px"})
                    ])
                ], className="mb-4")
            ], width=12, md=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-bar me-2"),
                        "Top Performing Projects"
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="top-projects-bar-chart", style={"height": "400px"})
                    ])
                ], className="mb-4")
            ], width=12, md=6)
        ])
    ], className="mt-4", fluid=True)
])

# Callback to populate week dropdown (4 weeks per month)
@callback(
    Output("project-week-dropdown", "options"),
    [Input("project-year-dropdown", "value"),
     Input("project-month-dropdown", "value")]
)
def populate_weeks(selected_year, selected_month):
    try:
        # Create 4 weeks per month
        weeks = []
        days_in_month = calendar.monthrange(selected_year, selected_month)[1]
        days_per_week = max(1, days_in_month // 4)  # Ensure at least 1 day per week
        
        for week_num in range(1, 5):  # Always 4 weeks
            start_day = (week_num - 1) * days_per_week + 1
            end_day = min(week_num * days_per_week, days_in_month)
            weeks.append({
                'label': f'Week {week_num} ({start_day}-{end_day})',
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
        
        if selected_month:
            where_conditions.append(f"MONTH(s.registration_date) = {selected_month}")
            
        if selected_week and selected_month:
            # Calculate week boundaries (4 weeks per month)
            days_in_month = calendar.monthrange(selected_year, selected_month)[1]
            days_per_week = max(1, days_in_month // 4)
            start_day = (selected_week - 1) * days_per_week + 1
            end_day = min(selected_week * days_per_week, days_in_month)
            where_conditions.append(f"DAY(s.registration_date) BETWEEN {start_day} AND {end_day}")
        
        where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Get projects with their names
        query = f"""
        SELECT DISTINCT p.id AS project_id, p.name AS project_name
        FROM Projects p
        INNER JOIN Stands s ON p.id = s.project_id
        {where_clause}
        ORDER BY p.id
        """
        df = pd.read_sql(query, engine)
        options = [{'label': f"{row['project_name']} (ID: {row['project_id']})", 'value': row['project_id']} for _, row in df.iterrows()]
        return options
    except Exception as e:
        print(f"Error loading project options: {e}")
        return []
    finally:
        if engine:
            engine.dispose()

#project analysis callback
@callback(
    [Output("project-connection-status", "children"),
     Output("total-projects", "children"),
     Output("total-project-stands", "children"),
     Output("avg-sale-value", "children"),
     Output("completion-rate", "children"),
     Output("project-progress-line-chart", "figure"),
     Output("top-projects-bar-chart", "figure")],
    [Input("refresh-project-button", "n_clicks")],
    [Input("project-year-dropdown", "value"),
     Input("project-month-dropdown", "value"),
     Input("project-week-dropdown", "value"),
     Input("project-project-dropdown", "value")]
)
def update_project_analysis(n_clicks, selected_year, selected_month, selected_week, selected_project):
    engine = get_user_db_engine()
    
    if not engine:
        not_connected_alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Not connected to database. Please connect first."
        ], color="warning")
        
        empty_fig = go.Figure()
        empty_fig.update_layout(title="No Data - Please Connect to Database")
        
        return [not_connected_alert, "0", "0", "$0", "0%", empty_fig, empty_fig]
    
    try:
        # Build WHERE clause based on all filters
        where_conditions = [f"YEAR(s.registration_date) = {selected_year}"]
        
        if selected_month:
            where_conditions.append(f"MONTH(s.registration_date) = {selected_month}")
            
        if selected_week and selected_month:
            # Calculate week boundaries (4 weeks per month)
            days_in_month = calendar.monthrange(selected_year, selected_month)[1]
            days_per_week = max(1, days_in_month // 4)
            start_day = (selected_week - 1) * days_per_week + 1
            end_day = min(selected_week * days_per_week, days_in_month)
            where_conditions.append(f"DAY(s.registration_date) BETWEEN {start_day} AND {end_day}")
        
        if selected_project:
            where_conditions.append(f"s.project_id = {selected_project}")
        
        where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Total Projects
        total_projects_query = f"""
        SELECT COUNT(DISTINCT s.project_id) AS total_projects 
        FROM Stands s
        INNER JOIN Projects p ON s.project_id = p.id
        {where_clause}
        """
        projects_df = pd.read_sql(total_projects_query, engine)
        total_projects = projects_df.iloc[0]['total_projects'] if not projects_df.empty and projects_df.iloc[0]['total_projects'] else 0
        
        # Total Stands
        total_stands_query = f"""
        SELECT COUNT(s.stand_number) AS total_stands 
        FROM Stands s
        INNER JOIN Projects p ON s.project_id = p.id
        {where_clause}
        """
        stands_df = pd.read_sql(total_stands_query, engine)
        total_stands = stands_df.iloc[0]['total_stands'] if not stands_df.empty and stands_df.iloc[0]['total_stands'] else 0
        
        # Average sale value
        avg_sale_query = f"""
        SELECT AVG(s.sale_value) AS avg_sale 
        FROM Stands s
        INNER JOIN Projects p ON s.project_id = p.id
        {where_clause}
        """
        avg_df = pd.read_sql(avg_sale_query, engine)
        avg_sale = avg_df.iloc[0]['avg_sale'] if not avg_df.empty and avg_df.iloc[0]['avg_sale'] else 0
        formatted_avg_sale = f"${avg_sale:,.2f}" if avg_sale else "$0"
        
        # Completion Rate 
        completion_query = f"""
        SELECT 
            COUNT(CASE WHEN s.available = 0 THEN 1 END) AS completed,
            COUNT(*) AS total
        FROM Stands s
        INNER JOIN Projects p ON s.project_id = p.id
        {where_clause}
        """
        completion_df = pd.read_sql(completion_query, engine)
        if not completion_df.empty and completion_df.iloc[0]['total'] > 0:
            completion_rate = (completion_df.iloc[0]['completed'] / completion_df.iloc[0]['total']) * 100
        else:
            completion_rate = 0
        formatted_completion = f"{completion_rate:.1f}%" if completion_rate else "0%"
        
        # Weekly Project Progress (based on 4-week system)
        progress_query = f"""
        SELECT 
            DAY(s.registration_date) AS day,
            COUNT(s.stand_number) AS stands_sold
        FROM Stands s
        INNER JOIN Projects p ON s.project_id = p.id
        {where_clause}
        GROUP BY DAY(s.registration_date)
        ORDER BY day
        """
        progress_df = pd.read_sql(progress_query, engine)
        
        if selected_month and selected_week and not progress_df.empty:
            # Create week labels for the selected week
            days_in_month = calendar.monthrange(selected_year, selected_month)[1]
            days_per_week = max(1, days_in_month // 4)
            start_day = (selected_week - 1) * days_per_week + 1
            end_day = min(selected_week * days_per_week, days_in_month)
            
            # Group data by week
            week_data = []
            current_week_stands = 0
            
            for day in range(start_day, end_day + 1):
                day_data = progress_df[progress_df['day'] == day]
                if not day_data.empty:
                    current_week_stands += day_data.iloc[0]['stands_sold']
            
            week_data.append({
                'week': f'Week {selected_week}',
                'stands_sold': current_week_stands
            })
            
            # If we have data for the week, create the figure
            if week_data:
                week_df = pd.DataFrame(week_data)
                line_fig = go.Figure()
                line_fig.add_trace(go.Scatter(
                    x=week_df['week'],
                    y=week_df['stands_sold'],
                    mode='lines+markers',
                    name='Stands Sold',
                    line=dict(color='#2c4bbc', width=2),
                    marker=dict(size=8)
                ))
                line_fig.update_layout(
                    title='Weekly Project Progress',
                    xaxis_title='Week',
                    yaxis_title='Stands Sold',
                    template='plotly_white'
                )
            else:
                line_fig = go.Figure()
                line_fig.update_layout(title="No Data Available")
        elif not progress_df.empty:
            # Monthly progress chart (when no specific week is selected)
            # Group by week within the month (4 weeks)
            if selected_month:
                days_in_month = calendar.monthrange(selected_year, selected_month)[1]
                days_per_week = max(1, days_in_month // 4)
                
                weekly_data = []
                for week_num in range(1, 5):
                    start_day = (week_num - 1) * days_per_week + 1
                    end_day = min(week_num * days_per_week, days_in_month)
                    
                    week_stands = progress_df[
                        (progress_df['day'] >= start_day) & 
                        (progress_df['day'] <= end_day)
                    ]['stands_sold'].sum()
                    
                    weekly_data.append({
                        'week': f'Week {week_num}',
                        'stands_sold': week_stands
                    })
                
                week_df = pd.DataFrame(weekly_data)
                line_fig = go.Figure()
                line_fig.add_trace(go.Scatter(
                    x=week_df['week'],
                    y=week_df['stands_sold'],
                    mode='lines+markers',
                    name='Stands Sold',
                    line=dict(color='#2c4bbc', width=2),
                    marker=dict(size=8)
                ))
                line_fig.update_layout(
                    title='Weekly Project Progress',
                    xaxis_title='Week',
                    yaxis_title='Stands Sold',
                    template='plotly_white'
                )
            else:
                line_fig = go.Figure()
                line_fig.update_layout(title="No Data Available")
        else:
            line_fig = go.Figure()
            line_fig.update_layout(title="No Data Available")
        
        #Top Performing Projects 
        top_projects_query = f"""
        SELECT 
            p.name AS project_name,
            p.id AS project_id,
            COUNT(s.stand_number) AS total_stands,
            SUM(s.sale_value) AS total_value
        FROM Projects p
        INNER JOIN Stands s ON p.id = s.project_id
        {where_clause}
        GROUP BY p.id, p.name
        ORDER BY total_value DESC
        LIMIT 10
        """
        top_df = pd.read_sql(top_projects_query, engine)
        
        if not top_df.empty:
            # Create combined labels with project name and ID
            project_labels = [f"{row['project_name']} (ID: {row['project_id']})" for _, row in top_df.iterrows()]
            
            bar_fig = go.Figure()
            bar_fig.add_trace(go.Bar(
                x=project_labels,
                y=top_df['total_value'],
                marker_color='lightgreen',
                text=top_df['total_stands'],
                textposition='auto',
                hovertemplate='<b>%{x}</b><br>' +
                             'Total Value: $%{y:,.2f}<br>' +
                             'Stands Sold: %{text}<br>' +
                             '<extra></extra>'
            ))
            bar_fig.update_layout(
                title='Top Performing Projects by Value',
                xaxis_title='Project',
                yaxis_title='Total Value ($)',
                template='plotly_white',
                xaxis_tickangle=-45
            )
        else:
            bar_fig = go.Figure()
            bar_fig.update_layout(title="No Data Available")
        
        # Status message
        filter_parts = [f"Year: {selected_year}"]
        if selected_month:
            month_name = calendar.month_name[selected_month]
            filter_parts.append(f"Month: {month_name}")
        if selected_week and selected_month:
            filter_parts.append(f"Week: {selected_week}")
        if selected_project:
            filter_parts.append(f"Project: {selected_project}")
        
        status = dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            f"Connected to database successfully! Showing data for {', '.join(filter_parts)}"
        ], color="success")
        
        return [status, str(total_projects), str(total_stands), formatted_avg_sale, formatted_completion, line_fig, bar_fig]
        
    except Exception as e:
        error_alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Database error: {str(e)}"
        ], color="danger")
        
        empty_fig = go.Figure()
        empty_fig.update_layout(title="Error Loading Data")
        
        return [error_alert, "0", "0", "$0", "0%", empty_fig, empty_fig]
    finally:
        if engine:
            engine.dispose()