import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, callback, ctx, State
from flask import session
from sqlalchemy import create_engine
import pandas as pd
import plotly.graph_objs as go
import datetime
import calendar

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
    
    dbc.Container([
        # Filter Section - Similar to Dashboard Layout
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Button([
                        html.I(className="fas fa-filter me-1"),
                        "Show Filters"
                    ], id="sales-filter-toggle-btn", color="primary", size="sm", className="btn-sm"),
                ], className="d-flex align-items-center justify-content-end mb-3")
            ], width=12)
        ]),
        
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
                                    id="sales-time-filter-radio",
                                    options=[
                                        {"label": "Daily", "value": "daily"},
                                        {"label": "Weekly", "value": "weekly"},
                                        {"label": "Monthly", "value": "monthly"},
                                        {"label": "Yearly", "value": "yearly"}
                                    ],
                                    value="yearly",
                                    inline=True,
                                    className="modern-radio-group",
                                    inputClassName="me-1",
                                    labelClassName="d-inline-block me-2 mb-1"
                                )
                            ])
                        ], width=12, md=6, className="mb-3 mb-md-0"),
                        
                        # Year Filter
                        dbc.Col([
                            html.Div([
                                html.Small([
                                    html.I(className="fas fa-calendar-alt me-1"),
                                    "Select Year"
                                ], className="text-muted mb-1 d-block fw-bold"),
                                dcc.Dropdown(
                                    id="sales-year-dropdown",
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
                                    id="sales-month-dropdown",
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
                    ], className="g-3 align-items-end mb-3"),
                    
                    dbc.Row([
                        # Week Filter
                        dbc.Col([
                            html.Div([
                                html.Small([
                                    html.I(className="fas fa-calendar-week me-1"),
                                    "Select Week"
                                ], className="text-muted mb-1 d-block fw-bold"),
                                dcc.Dropdown(
                                    id="sales-week-dropdown",
                                    options=[],
                                    placeholder="Select week",
                                    className="modern-dropdown"
                                )
                            ])
                        ], width=12, md=4, className="mb-3 mb-md-0"),
                        
                        # Day Filter
                        dbc.Col([
                            html.Div([
                                html.Small([
                                    html.I(className="fas fa-calendar-day me-1"),
                                    "Select Day"
                                ], className="text-muted mb-1 d-block fw-bold"),
                                dcc.Dropdown(
                                    id="sales-day-dropdown",
                                    options=[{'label': str(day), 'value': day} for day in range(1, 32)],
                                    value=datetime.datetime.now().day,
                                    clearable=False,
                                    className="modern-dropdown"
                                )
                            ])
                        ], width=12, md=4, className="mb-3 mb-md-0"),
                        
                        # Refresh Button
                        dbc.Col([
                            html.Div([
                                dbc.Button([
                                    html.I(className="fas fa-sync me-2"),
                                    "Refresh Analysis"
                                ], id="refresh-sales-button", color="primary", className="w-100")
                            ], className="d-flex align-items-end")
                        ], width=12, md=4)
                    ], className="g-3 align-items-end")
                ], style={"minHeight": "380px", "paddingBottom": "20px"})
            ], className="shadow-sm mb-4")
        ], id="sales-filter-collapse", is_open=False),
        
        # Metric Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-dollar-sign fa-lg text-success"),
                            ], className="d-flex justify-content-center mb-2"),
                            html.H4("Total Sales", className="card-title text-center mb-1"),
                            html.H2(id="total-sales", children="$0.00", className="text-center text-success fw-bold mb-1"),
                            html.Small("Combined sales value", className="text-center text-muted d-block")
                        ], className="text-center")
                    ])
                ], className="shadow-lg h-100", style={"borderLeft": "4px solid #28a745"})
            ], width=12, md=6, lg=3, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-map-marker-alt fa-lg text-primary"),
                            ], className="d-flex justify-content-center mb-2"),
                            html.H4("Total Stands Sold", className="card-title text-center mb-1"),
                            html.H2(id="total-stands-sold", children="0 stands", className="text-center text-primary fw-bold mb-1"),
                            html.Small("Number of stands sold", className="text-center text-muted d-block")
                        ], className="text-center")
                    ])
                ], className="shadow-lg h-100", style={"borderLeft": "4px solid #007bff"})
            ], width=12, md=6, lg=3, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-calculator fa-lg text-warning"),
                            ], className="d-flex justify-content-center mb-2"),
                            html.H4("Average Sale Value", className="card-title text-center mb-1"),
                            html.H2(id="average-sale-value", children="$0.00", className="text-center text-warning fw-bold mb-1"),
                            html.Small("Per stand average", className="text-center text-muted d-block")
                        ], className="text-center")
                    ])
                ], className="shadow-lg h-100", style={"borderLeft": "4px solid #ffc107"})
            ], width=12, md=6, lg=3, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-user-tie fa-lg text-info"),
                            ], className="d-flex justify-content-center mb-2"),
                            html.H4("Top Agent", className="card-title text-center mb-1"),
                            html.H2(id="top-agent", children="N/A", className="text-center text-info fw-bold mb-1"),
                            html.Small("Highest performing agent", className="text-center text-muted d-block")
                        ], className="text-center")
                    ])
                ], className="shadow-lg h-100", style={"borderLeft": "4px solid #17a2b8"})
            ], width=12, md=6, lg=3, className="mb-3"),
        ], className="mb-4"),
        
        # Charts Row
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
                ], className="mb-4 shadow")
            ], width=12, lg=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-pie me-2"),
                        "Sales by Agent"
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="agent-sales-chart", style={"height": "400px"})
                    ])
                ], className="mb-4 shadow")
            ], width=12, lg=6)
        ]),
        
        # Sales Targets vs Achieved Chart
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-bullseye me-2"),
                        "Sales Targets vs Achieved by Project"
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="targets-vs-achieved-chart", style={"height": "500px"})
                    ])
                ], className="mb-4 shadow")
            ], width=12)
        ])
    ], className="mt-4", fluid=True, style={"paddingTop": "20px"})
])

# Callback to toggle filter section
@callback(
    [Output("sales-filter-collapse", "is_open"),
     Output("sales-filter-toggle-btn", "children")],
    Input("sales-filter-toggle-btn", "n_clicks"),
    State("sales-filter-collapse", "is_open"),
    prevent_initial_call=False
)
def toggle_sales_filter_collapse(n_clicks, is_open):
    if n_clicks:
        new_state = not is_open
        button_text = [html.I(className="fas fa-filter me-1"), "Hide Filters"] if new_state else [html.I(className="fas fa-filter me-1"), "Show Filters"]
        return new_state, button_text
    return is_open, [html.I(className="fas fa-filter me-1"), "Show Filters"]

# Callback to populate week dropdown based on year and month (4 weeks per month)
@callback(
    [Output("sales-week-dropdown", "options"),
     Output("sales-day-dropdown", "options")],
    [Input("sales-year-dropdown", "value"),
     Input("sales-month-dropdown", "value")]
)
def populate_weeks_and_days(selected_year, selected_month):
    if selected_month == 0:  # All months
        return [], [{'label': str(day), 'value': day} for day in range(1, 32)]
    
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
        
        # Get days in the selected month
        days = [{'label': str(day), 'value': day} for day in range(1, days_in_month + 1)]
        
        return weeks, days
    except Exception as e:
        print(f"Error populating weeks and days: {e}")
        return [], [{'label': str(day), 'value': day} for day in range(1, 32)]

# Callback to control dropdown visibility based on time filter
@callback(
    [Output("sales-month-dropdown", "style"),
     Output("sales-week-dropdown", "style"),
     Output("sales-day-dropdown", "style")],
    Input("sales-time-filter-radio", "value")
)
def toggle_dropdowns_visibility(time_filter):
    month_style = {"display": "block"} if time_filter in ["monthly", "weekly", "daily"] else {"display": "none"}
    week_style = {"display": "block"} if time_filter == "weekly" else {"display": "none"}
    day_style = {"display": "block"} if time_filter == "daily" else {"display": "none"}
    
    # Apply default styling
    base_style = {"display": "inline-block", "width": "100%"}
    month_final = {**base_style, **month_style}
    week_final = {**base_style, **week_style}
    day_final = {**base_style, **day_style}
    
    return month_final, week_final, day_final

# Function to get target period based on time filter
def get_target_period_info(time_filter, selected_year, selected_month, selected_week):
    """Get target period information for matching with targets"""
    target_info = {
        'target_type': 'yearly',
        'target_year': selected_year,
        'target_month': None,
        'target_week': None
    }
    
    if time_filter == "monthly":
        target_info['target_type'] = 'monthly'
        target_info['target_month'] = selected_month if selected_month != 0 else None
    elif time_filter == "weekly":
        target_info['target_type'] = 'weekly'
        target_info['target_week'] = selected_week
        target_info['target_month'] = selected_month if selected_month != 0 else None
    elif time_filter == "daily":
        # For daily, we'll match with weekly targets
        target_info['target_type'] = 'weekly'
        target_info['target_week'] = selected_week
        target_info['target_month'] = selected_month if selected_month != 0 else None
        
    return target_info

# Function to get targets for projects
def get_project_targets(engine, target_type, target_year, target_month=None, target_week=None):
    """Get project targets from database"""
    try:
        # Get project-specific targets
        project_targets_query = """
        SELECT 
            pt.project_id,
            p.name as project_name,
            pt.sales_target,
            pt.stands_target
        FROM aibesinsights_project_targets pt
        LEFT JOIN Projects p ON pt.project_id = p.id
        WHERE pt.target_type = :target_type 
        AND pt.target_year = :target_year
        AND (:target_month IS NULL OR pt.target_month = :target_month)
        AND (:target_week IS NULL OR pt.target_week = :target_week)
        """
        
        params = {
            'target_type': target_type,
            'target_year': target_year,
            'target_month': target_month,
            'target_week': target_week
        }
        
        project_targets_df = pd.read_sql(project_targets_query, engine, params=params)
        return project_targets_df
    except Exception as e:
        print(f"Error getting project targets: {e}")
        return pd.DataFrame()

#sales analysis callback
@callback(
    [Output("total-sales", "children"),
     Output("total-stands-sold", "children"),
     Output("average-sale-value", "children"),
     Output("top-agent", "children"),
     Output("project-sales-chart", "figure"),
     Output("agent-sales-chart", "figure"),
     Output("targets-vs-achieved-chart", "figure")],
    [Input("refresh-sales-button", "n_clicks")],
    [Input("sales-time-filter-radio", "value"),
     Input("sales-year-dropdown", "value"),
     Input("sales-month-dropdown", "value"),
     Input("sales-day-dropdown", "value"),
     Input("sales-week-dropdown", "value")]
)
def update_sales_analysis(n_clicks, time_filter, selected_year, selected_month, selected_day, selected_week):
    engine = get_user_db_engine()
    
    if not engine:
        empty_fig = go.Figure()
        empty_fig.update_layout(title="No Data - Please Connect to Database")
        
        return ["$0.00", "0 stands", "$0.00", "N/A", empty_fig, empty_fig, empty_fig]
    
    try:
        # Build WHERE clause based on time filter
        if time_filter == "daily":
            # For daily, use the selected day
            if selected_month != 0:
                date_condition = f"DATE(ca.registration_date) = '{selected_year}-{selected_month:02d}-{selected_day:02d}'"
            else:
                date_condition = f"YEAR(ca.registration_date) = {selected_year} AND DAY(ca.registration_date) = {selected_day}"
        elif time_filter == "weekly":
            if selected_week and selected_month != 0:
                # Calculate week boundaries (4 weeks per month)
                days_in_month = calendar.monthrange(selected_year, selected_month)[1]
                days_per_week = max(1, days_in_month // 4)
                start_day = (selected_week - 1) * days_per_week + 1
                end_day = min(selected_week * days_per_week, days_in_month)
                date_condition = f"DAY(ca.registration_date) BETWEEN {start_day} AND {end_day} AND MONTH(ca.registration_date) = {selected_month} AND YEAR(ca.registration_date) = {selected_year}"
            elif selected_month != 0:
                date_condition = f"YEAR(ca.registration_date) = {selected_year} AND MONTH(ca.registration_date) = {selected_month}"
            else:
                date_condition = f"YEAR(ca.registration_date) = {selected_year}"
        elif time_filter == "monthly":
            if selected_month != 0:
                date_condition = f"YEAR(ca.registration_date) = {selected_year} AND MONTH(ca.registration_date) = {selected_month}"
            else:
                date_condition = f"YEAR(ca.registration_date) = {selected_year}"
        else:  # yearly
            date_condition = f"YEAR(ca.registration_date) = {selected_year}"
        
        # Add condition to exclude deleted records
        where_clause = f"WHERE {date_condition} AND ca.deleted = 0"
        
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
                marker_color='#007bff',
                text=[f"{stands:,}" for stands in project_df['stands_sold']],
                textposition='auto',
                yaxis='y'
            ))
            
            project_fig.add_trace(go.Scatter(
                name='Sales Amount',
                x=project_df['project_name'],
                y=project_df['total_sales'],
                mode='lines+markers',
                line=dict(color='#28a745', width=3),
                marker=dict(size=8),
                text=[f"${sales:,.0f}" for sales in project_df['total_sales']],
                textposition='top center',
                yaxis='y2'
            ))
            
            project_fig.update_layout(
                title=f"Project Sales Comparison ({time_filter.title()})",
                xaxis_title="Project",
                yaxis_title="Stands Sold",
                yaxis2=dict(
                    title="Sales Amount ($)",
                    overlaying='y',
                    side='right'
                ),
                xaxis_tickangle=-45,
                hovermode='closest',
                barmode='group',
                template='plotly_white'
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
                marker=dict(colors=['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1', '#20c997', '#fd7e14']),
                hovertemplate='<b>%{label}</b><br>' +
                             'Sales: $%{value:,.0f}<br>' +
                             'Stands: %{customdata}<br>' +
                             '(%{percent})<extra></extra>',
                customdata=agent_df['stands_sold']
            )])
            agent_fig.update_layout(
                title=f"Sales by Agent ({time_filter.title()})",
                showlegend=True,
                template='plotly_white'
            )
        else:
            agent_fig = go.Figure()
            agent_fig.update_layout(title="No Agent Data Available")
        
        # TARGETS VS ACHIEVED CHART
        # Get target period information
        target_info = get_target_period_info(time_filter, selected_year, selected_month, selected_week)
        
        # Get project targets
        project_targets_df = get_project_targets(
            engine, 
            target_info['target_type'], 
            target_info['target_year'], 
            target_info['target_month'], 
            target_info['target_week']
        )
        
        # Get actual sales data by project for the same period
        actual_sales_query = f"""
        SELECT 
            p.id AS project_id,
            p.name AS project_name,
            COUNT(*) AS stands_sold,
            SUM(ca.stand_value) AS total_sales
        FROM customer_accounts ca
        INNER JOIN Projects p ON ca.project_id = p.id
        {where_clause}
        GROUP BY p.id, p.name
        ORDER BY p.name
        """
        actual_sales_df = pd.read_sql(actual_sales_query, engine)
        
        if not actual_sales_df.empty:
            # Merge actual sales with targets
            if not project_targets_df.empty:
                merged_df = pd.merge(
                    actual_sales_df, 
                    project_targets_df[['project_id', 'sales_target', 'stands_target']], 
                    on='project_id', 
                    how='left'
                )
            else:
                # If no targets set, create empty target columns
                merged_df = actual_sales_df.copy()
                merged_df['sales_target'] = None
                merged_df['stands_target'] = None
            
            # Create targets vs achieved chart
            targets_fig = go.Figure()
            
            # Add actual sales bars
            targets_fig.add_trace(go.Bar(
                name='Actual Sales ($)',
                x=merged_df['project_name'],
                y=merged_df['total_sales'],
                marker_color='#28a745',
                text=[f"${sales:,.0f}" for sales in merged_df['total_sales']],
                textposition='auto'
            ))
            
            # Add sales targets (if available)
            if 'sales_target' in merged_df.columns and not merged_df['sales_target'].isnull().all():
                targets_fig.add_trace(go.Bar(
                    name='Sales Target ($)',
                    x=merged_df['project_name'],
                    y=merged_df['sales_target'],
                    marker_color='#ffc107',
                    text=[f"${target:,.0f}" if pd.notnull(target) else "No Target" for target in merged_df['sales_target']],
                    textposition='auto'
                ))
            
            # Add achievement percentage as line chart on secondary axis
            if 'sales_target' in merged_df.columns:
                achievement_pct = []
                for _, row in merged_df.iterrows():
                    if pd.notnull(row['sales_target']) and row['sales_target'] > 0:
                        pct = (row['total_sales'] / row['sales_target']) * 100
                        achievement_pct.append(pct)
                    else:
                        achievement_pct.append(None)
                
                targets_fig.add_trace(go.Scatter(
                    name='Achievement %',
                    x=merged_df['project_name'],
                    y=achievement_pct,
                    mode='lines+markers',
                    line=dict(color='#007bff', width=3),
                    marker=dict(size=8),
                    yaxis='y2',
                    text=[f"{pct:.1f}%" if pd.notnull(pct) else "N/A" for pct in achievement_pct],
                    textposition='top center'
                ))
            
            targets_fig.update_layout(
                title=f"Sales Targets vs Achieved by Project ({time_filter.title()}, {selected_year}" + 
                      (f"-{selected_month}" if selected_month != 0 and time_filter in ['monthly', 'weekly', 'daily'] else "") + ")",
                xaxis_title="Project",
                yaxis_title="Amount ($)",
                yaxis2=dict(
                    title="Achievement %",
                    overlaying='y',
                    side='right',
                    range=[0, 150]  # Set range for percentage axis
                ),
                barmode='group',
                xaxis_tickangle=-45,
                template='plotly_white',
                hovermode='x unified'
            )
        else:
            targets_fig = go.Figure()
            targets_fig.update_layout(title="No Data Available for Targets Comparison")
        
        return [formatted_total_sales, formatted_total_stands, formatted_average_sale, top_agent_name, project_fig, agent_fig, targets_fig]
        
    except Exception as e:
        print(f"Error in update_sales_analysis: {e}")
        empty_fig = go.Figure()
        empty_fig.update_layout(title="Error Loading Data")
        
        return ["$0.00", "0 stands", "$0.00", "N/A", empty_fig, empty_fig, empty_fig]
    finally:
        if engine:
            engine.dispose()