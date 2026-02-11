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
        html.I(className="fas fa-chart-line me-2"),
        "Sales Analysis"
    ], className="mt-3 mb-4 text-center"),
    
    # Connection status indicator
    html.Div(id="sales-analysis-connection-status"),
    
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
                                dbc.Label("Time Range", className="mb-2"),
                                dbc.ButtonGroup([
                                    dbc.Button("Daily", id="sales-time-daily", color="secondary", outline=True),
                                    dbc.Button("Weekly", id="sales-time-weekly", color="secondary", outline=True),
                                    dbc.Button("Monthly", id="sales-time-monthly", color="secondary", outline=True),
                                    dbc.Button("Yearly", id="sales-time-yearly", color="secondary", outline=True, active=True)
                                ], id="sales-analysis-time-toggle", className="mb-3")
                            ], width=12),
                            
                            dbc.Col([
                                dbc.Label("Select Year", className="mb-2"),
                                dcc.Dropdown(
                                    id="sales-year-dropdown",
                                    options=[
                                        {'label': str(year), 'value': year} 
                                        for year in range(datetime.datetime.now().year, datetime.datetime.now().year - 5, -1)
                                    ],
                                    value=datetime.datetime.now().year,
                                    clearable=False,
                                    className="mb-2"
                                )
                            ], width=4),
                            
                            dbc.Col([
                                dbc.Label("Select Month", className="mb-2"),
                                dcc.Dropdown(
                                    id="sales-month-dropdown",
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
                            ], width=4),
                            
                            dbc.Col([
                                dbc.Label("Select Day", className="mb-2"),
                                dcc.Dropdown(
                                    id="sales-day-dropdown",
                                    options=[{'label': str(day), 'value': day} for day in range(1, 32)],
                                    value=datetime.datetime.now().day,
                                    clearable=False,
                                    className="mb-2"
                                )
                            ], width=4),
                            
                            dbc.Col([
                                dbc.Label("Select Week", className="mb-2"),
                                dcc.Dropdown(
                                    id="sales-week-dropdown",
                                    options=[],
                                    placeholder="Select week",
                                    className="mb-2"
                                )
                            ], width=4),
                        ]),
                        
                        dbc.Button([
                            html.I(className="fas fa-sync me-2"),
                            "Refresh Analysis"
                        ], id="refresh-sales-button", color="primary", className="w-100")
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
                            html.H4("Total Sales", className="card-title text-center"),
                            html.H2(id="total-sales", children="$0.00", className="text-center text-success fw-bold"),
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=6, md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H4("Total Stands Sold", className="card-title text-center"),
                            html.H2(id="total-stands-sold", children="0 stands", className="text-center text-primary fw-bold"),
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=6, md=3),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H4("Average Sale Value", className="card-title text-center"),
                            html.H2(id="average-sale-value", children="$0.00", className="text-center text-warning fw-bold"),
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=6, md=3),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H4("Top Agent", className="card-title text-center"),
                            html.H2(id="top-agent", children="N/A", className="text-center text-info fw-bold"),
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=6, md=3)
        ], className="mb-4"),
        
        # Charts Row 1
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-bar me-2"),
                        "Project Sales Comparison"
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="project-sales-chart", style={"height": "400px"})
                    ])
                ], className="mb-4")
            ], width=12, md=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-pie me-2"),
                        "Sales by Agent"
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="agent-sales-chart", style={"height": "400px"})
                    ])
                ], className="mb-4")
            ], width=12, md=6)
        ]),
        
        # Charts Row 2
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-line me-2"),
                        "Sales Trend Over Time"
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="sales-trend-chart", style={"height": "400px"})
                    ])
                ], className="mb-4")
            ], width=12)
        ])
    ], className="mt-4", fluid=True)
])

# Callback to manage toggle button states
@callback(
    [Output("sales-time-daily", "active"),
     Output("sales-time-weekly", "active"),
     Output("sales-time-monthly", "active"),
     Output("sales-time-yearly", "active")],
    [Input("sales-time-daily", "n_clicks"),
     Input("sales-time-weekly", "n_clicks"),
     Input("sales-time-monthly", "n_clicks"),
     Input("sales-time-yearly", "n_clicks")],
    prevent_initial_call=False
)
def update_toggle_buttons(daily_clicks, weekly_clicks, monthly_clicks, yearly_clicks):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        # Default to yearly
        return False, False, False, True
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "sales-time-daily":
        return True, False, False, False
    elif button_id == "sales-time-weekly":
        return False, True, False, False
    elif button_id == "sales-time-monthly":
        return False, False, True, False
    elif button_id == "sales-time-yearly":
        return False, False, False, True
    
    # Default fallback
    return False, False, False, True

# Callback to get active time filter
@callback(
    Output("sales-active-time-filter", "children"),
    [Input("sales-time-daily", "active"),
     Input("sales-time-weekly", "active"),
     Input("sales-time-monthly", "active"),
     Input("sales-time-yearly", "active")],
    prevent_initial_call=False
)
def get_active_time_filter(daily_active, weekly_active, monthly_active, yearly_active):
    if daily_active:
        return "daily"
    elif weekly_active:
        return "weekly"
    elif monthly_active:
        return "monthly"
    elif yearly_active:
        return "yearly"
    else:
        return "yearly"  # default

# Hidden div to store active time filter
layout.children.insert(1, html.Div(id="sales-active-time-filter", style={"display": "none"}))

# Callback to populate week dropdown based on year and month
@callback(
    [Output("sales-week-dropdown", "options"),
     Output("sales-day-dropdown", "options")],
    [Input("sales-year-dropdown", "value"),
     Input("sales-month-dropdown", "value")]
)
def populate_weeks_and_days(selected_year, selected_month):
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
        
        # Get days in the selected month
        days_in_month = calendar.monthrange(selected_year, selected_month)[1]
        days = [{'label': str(day), 'value': day} for day in range(1, days_in_month + 1)]
        
        return weeks, days
    except Exception as e:
        print(f"Error populating weeks and days: {e}")
        return [], [{'label': str(day), 'value': day} for day in range(1, 32)]

#sales analysis callback
@callback(
    [Output("sales-analysis-connection-status", "children"),
     Output("total-sales", "children"),
     Output("total-stands-sold", "children"),
     Output("average-sale-value", "children"),
     Output("top-agent", "children"),
     Output("project-sales-chart", "figure"),
     Output("agent-sales-chart", "figure"),
     Output("sales-trend-chart", "figure")],
    [Input("refresh-sales-button", "n_clicks")],
    [Input("sales-active-time-filter", "children"),
     Input("sales-year-dropdown", "value"),
     Input("sales-month-dropdown", "value"),
     Input("sales-day-dropdown", "value"),
     Input("sales-week-dropdown", "value")]
)
def update_sales_analysis(n_clicks, active_time_filter, selected_year, selected_month, selected_day, selected_week):
    engine = get_user_db_engine()
    
    if not engine:
        not_connected_alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Not connected to database. Please connect first."
        ], color="warning")
        
        empty_fig = go.Figure()
        empty_fig.update_layout(title="No Data - Please Connect to Database")
        
        return [not_connected_alert, "$0.00", "0 stands", "$0.00", "N/A", empty_fig, empty_fig, empty_fig]
    
    try:
        # Build WHERE clause based on time filter
        if active_time_filter == "daily":
            # For daily, use the selected day
            date_condition = f"DATE(ca.registration_date) = '{selected_year}-{selected_month:02d}-{selected_day:02d}'"
        elif active_time_filter == "weekly":
            if selected_week:
                # Use a simpler approach for weekly filtering
                start_date = datetime.date(selected_year, selected_month, 1)
                # Calculate approximate week start and end dates
                week_start = start_date + datetime.timedelta(weeks=selected_week-1)
                week_end = week_start + datetime.timedelta(days=6)
                date_condition = f"DATE(ca.registration_date) BETWEEN '{week_start}' AND '{week_end}'"
            else:
                date_condition = f"YEAR(ca.registration_date) = {selected_year} AND MONTH(ca.registration_date) = {selected_month}"
        elif active_time_filter == "monthly":
            date_condition = f"YEAR(ca.registration_date) = {selected_year} AND MONTH(ca.registration_date) = {selected_month}"
        else:  # yearly
            date_condition = f"YEAR(ca.registration_date) = {selected_year}"
        
        where_clause = f"WHERE {date_condition}"
        
        # TOTAL SALES
        total_sales_query = f"""
        SELECT SUM(ca.stand_value) AS total_sales, COUNT(*) AS total_stands 
        FROM customer_accounts ca
        {where_clause}
        """
        total_df = pd.read_sql(total_sales_query, engine)
        total_sales = total_df.iloc[0]['total_sales'] if not total_df.empty and not pd.isna(total_df.iloc[0]['total_sales']) else 0
        total_stands = total_df.iloc[0]['total_stands'] if not total_df.empty and not pd.isna(total_df.iloc[0]['total_stands']) else 0
        formatted_total_sales = f"${total_sales:,.2f}" if total_sales else "$0.00"
        formatted_total_stands = f"{total_stands:,} stands" if total_stands else "0 stands"
        average_sale_value = total_sales / total_stands if total_stands > 0 else 0
        formatted_average_sale = f"${average_sale_value:,.2f}" if average_sale_value else "$0.00"
        
        # TOP AGENT - Using customer_accounts table (excluding null agent names)
        top_agent_query = f"""
        SELECT 
            ca.agent_name,
            COUNT(*) AS stands_sold,
            SUM(ca.stand_value) AS total_sales
        FROM customer_accounts ca
        {where_clause} AND ca.agent_name IS NOT NULL AND ca.agent_name != ''
        GROUP BY ca.agent_name
        ORDER BY total_sales DESC
        LIMIT 1
        """
        top_agent_df = pd.read_sql(top_agent_query, engine)
        top_agent_name = top_agent_df.iloc[0]['agent_name'] if not top_agent_df.empty and top_agent_df.iloc[0]['agent_name'] else "N/A"
        
        # PROJECT SALES COMPARISON CHART - Using customer_accounts table
        project_sales_query = f"""
        SELECT 
            p.name AS project_name,
            COUNT(*) AS stands_sold,
            SUM(ca.stand_value) AS total_sales
        FROM customer_accounts ca
        INNER JOIN Projects p ON ca.project_id = p.id
        {where_clause}
        GROUP BY p.id, p.name
        ORDER BY total_sales DESC
        """
        project_df = pd.read_sql(project_sales_query, engine)
        
        if not project_df.empty:
            # Create grouped bar chart for project comparison
            project_fig = go.Figure()
            
            project_fig.add_trace(go.Bar(
                name='Stands Sold',
                x=project_df['project_name'],
                y=project_df['stands_sold'],
                marker_color='lightblue',
                text=[f"{stands:,}" for stands in project_df['stands_sold']],
                textposition='auto',
                yaxis='y'
            ))
            
            project_fig.add_trace(go.Scatter(
                name='Sales Amount',
                x=project_df['project_name'],
                y=project_df['total_sales'],
                mode='lines+markers',
                line=dict(color='red', width=3),
                marker=dict(size=8),
                text=[f"${sales:,.0f}" for sales in project_df['total_sales']],
                textposition='top center',
                yaxis='y2'
            ))
            
            project_fig.update_layout(
                title=f"Project Sales Comparison ({active_time_filter.title()})",
                xaxis_title="Project",
                yaxis_title="Stands Sold",
                yaxis2=dict(
                    title="Sales Amount ($)",
                    overlaying='y',
                    side='right'
                ),
                xaxis_tickangle=-45,
                hovermode='closest',
                barmode='group'
            )
        else:
            project_fig = go.Figure()
            project_fig.update_layout(title="No Project Data Available")
        
        # AGENT SALES CHART - Using customer_accounts table (excluding null agent names)
        agent_sales_query = f"""
        SELECT 
            ca.agent_name,
            COUNT(*) AS stands_sold,
            SUM(ca.stand_value) AS total_sales
        FROM customer_accounts ca
        {where_clause} AND ca.agent_name IS NOT NULL AND ca.agent_name != ''
        GROUP BY ca.agent_name
        ORDER BY total_sales DESC
        LIMIT 10
        """
        agent_df = pd.read_sql(agent_sales_query, engine)
        
        if not agent_df.empty:
            agent_fig = go.Figure(data=[go.Pie(
                labels=agent_df['agent_name'],
                values=agent_df['total_sales'],
                hole=0.4,
                hovertemplate='<b>%{label}</b><br>' +
                             'Sales: $%{value:,.0f}<br>' +
                             'Stands: %{customdata}<br>' +
                             '(%{percent})<extra></extra>',
                customdata=agent_df['stands_sold']
            )])
            agent_fig.update_layout(
                title=f"Sales by Agent ({active_time_filter.title()})",
                showlegend=True
            )
        else:
            agent_fig = go.Figure()
            agent_fig.update_layout(title="No Agent Data Available")
        
        # SALES TREND CHART - Using customer_accounts table
        if active_time_filter == "daily":
            trend_group_by = "DATE(ca.registration_date)"
            trend_label = "Date"
        elif active_time_filter == "weekly":
            trend_group_by = "YEARWEEK(ca.registration_date)"
            trend_label = "Week"
        elif active_time_filter == "monthly":
            trend_group_by = "DATE_FORMAT(ca.registration_date, '%%Y-%%m')"
            trend_label = "Month"
        else:  # yearly
            trend_group_by = "YEAR(ca.registration_date)"
            trend_label = "Year"
        
        trend_query = f"""
        SELECT 
            {trend_group_by} AS period,
            COUNT(*) AS stands_sold,
            SUM(ca.stand_value) AS total_sales
        FROM customer_accounts ca
        {where_clause}
        GROUP BY period
        ORDER BY period
        """
        trend_df = pd.read_sql(trend_query, engine)
        
        if not trend_df.empty:
            trend_fig = go.Figure()
            
            trend_fig.add_trace(go.Scatter(
                x=trend_df['period'],
                y=trend_df['total_sales'],
                mode='lines+markers',
                name='Sales Amount',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8),
                text=[f"${sales:,.0f}" for sales in trend_df['total_sales']],
                textposition='top center'
            ))
            
            trend_fig.update_layout(
                title=f"Sales Trend Over Time ({active_time_filter.title()})",
                xaxis_title=trend_label,
                yaxis_title="Sales Amount ($)",
                hovermode='x unified'
            )
        else:
            trend_fig = go.Figure()
            trend_fig.update_layout(title="No Trend Data Available")
        
        # Time filter label for status message
        time_labels = {
            "daily": f"Daily ({selected_year}-{selected_month:02d}-{selected_day:02d})",
            "weekly": f"Weekly (Month: {selected_month}" + (f", Week: {selected_week}" if selected_week else "") + ")",
            "monthly": f"Monthly ({datetime.date(1900, selected_month, 1).strftime('%B')})",
            "yearly": "Yearly"
        }
        time_label = time_labels.get(active_time_filter, "Period")
        
        status = dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            f"Connected to database successfully! Showing {time_label} data for Year: {selected_year}"
        ], color="success")
        
        return [status, formatted_total_sales, formatted_total_stands, formatted_average_sale, top_agent_name, project_fig, agent_fig, trend_fig]
        
    except Exception as e:
        error_alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Database error: {str(e)}"
        ], color="danger")
        
        empty_fig = go.Figure()
        empty_fig.update_layout(title="Error Loading Data")
        
        return [error_alert, "$0.00", "0 stands", "$0.00", "N/A", empty_fig, empty_fig, empty_fig]
    finally:
        if engine:
            engine.dispose()