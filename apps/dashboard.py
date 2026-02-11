import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, callback, State, no_update
from flask import session
from sqlalchemy import create_engine
import pandas as pd
from .reports import initialize_report_generator, get_report_generator
import plotly.graph_objs as go
import datetime
import json
import os
from apps.reports import initialize_report_generator, get_report_generator
import dash


# Conditional ML import
try:
    from sklearn.linear_model import LinearRegression
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = True
import numpy as np

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

# Function to create forecast data
def create_forecast(df_monthly, months_ahead=3):
    if df_monthly.empty or len(df_monthly) < 2:
        # Return empty dataframe with same structure
        return pd.DataFrame(columns=['month', 'total_stands_sold', 'type'])
    
    try:
        #use scikit-learn if available
        if ML_AVAILABLE:
            # Preparation of the data for linear regression
            df_monthly = df_monthly.sort_values('month')
            X = np.array(df_monthly['month']).reshape(-1, 1)
            y = df_monthly['total_stands_sold'].values
            
            # data validation
            if len(y) < 2 or np.all(y == 0):
                return simple_forecast(df_monthly, months_ahead)
            
            # Fit linear model
            model = LinearRegression()
            model.fit(X, y)
            
            # Predict next months
            last_month = df_monthly['month'].max()
            future_months = [last_month + i for i in range(1, months_ahead + 1)]
            future_X = np.array(future_months).reshape(-1, 1)
            predictions = model.predict(future_X)
            
            # no negative predictions
            predictions = np.maximum(predictions, 0)
            
            # forecast dataframe
            forecast_df = pd.DataFrame({
                'month': future_months,
                'total_stands_sold': predictions,
                'type': 'forecast'
            })
        else:
            #simple forecasting if ML not available
            return simple_forecast(df_monthly, months_ahead)
            
        #actual data
        df_monthly['type'] = 'actual'
        result_df = pd.concat([df_monthly[['month', 'total_stands_sold', 'type']], forecast_df], ignore_index=True)
        
        return result_df
    except Exception as e:
        print(f"Forecast error: {e}")
        # Fallback to simple forecast
        return simple_forecast(df_monthly, months_ahead)

def simple_forecast(df_monthly, months_ahead=3):
    """Simple forecasting without ML dependencies"""
    if df_monthly.empty:
        return pd.DataFrame(columns=['month', 'total_stands_sold', 'type'])
    
    # Sort by month
    df_monthly = df_monthly.sort_values('month')
    
    # Simple average of last 3 months or all available
    recent_data = df_monthly['total_stands_sold'].tail(min(3, len(df_monthly)))
    avg_value = recent_data.mean() if not recent_data.empty else 0
    
    #forecast data
    last_month = df_monthly['month'].max()
    
    forecast_data = []
    for i in range(1, months_ahead + 1):
        forecast_data.append({
            'month': last_month + i,
            'total_stands_sold': max(0, avg_value),  #no non-negative
            'type': 'forecast'
        })
    
    #actual data
    df_monthly['type'] = 'actual'
    result_df = pd.concat([df_monthly[['month', 'total_stands_sold', 'type']], 
                          pd.DataFrame(forecast_data)], ignore_index=True)
    
    return result_df

# Layout
layout = html.Div([
    #storing report data
    html.Div(id="report-data-store", style={"display": "none"}),
    
    #Connection status indicator
    html.Div(id="dashboard-connection-status"),
    
    # Modern Filters Section
    dbc.Container([
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    # Time Range Filter
                    dbc.Col([
                        html.Div([
                            html.Small([
                                html.I(className="fas fa-clock me-1"),
                                "Time Range"
                            ], className="text-muted mb-1 d-block"),
                            dcc.RadioItems(
                                id="time-filter-radio",
                                options=[
                                    {"label": "Today", "value": "daily"},
                                    {"label": "Last 7 Days", "value": "weekly"},
                                    {"label": "This Year", "value": "yearly"}
                                ] + ([{"label": "Forecast", "value": "forecast"}] if ML_AVAILABLE else []),
                                value="yearly",
                                inline=True,
                                className="modern-radio-group"
                            )
                        ], className="mb-3")
                    ], width=12, lg=8),
                    
                    # Year Filter (conditionally shown)
                    dbc.Col([
                        html.Div([
                            html.Small([
                                html.I(className="fas fa-calendar-alt me-1"),
                                "Select Year"
                            ], className="text-muted mb-1 d-block"),
                            dcc.Dropdown(
                                id="year-dropdown",
                                options=[
                                    {'label': str(year), 'value': year} 
                                    for year in range(datetime.datetime.now().year, datetime.datetime.now().year - 5, -1)
                                ],
                                value=datetime.datetime.now().year,
                                clearable=False,
                                className="modern-dropdown"
                            )
                        ], id="year-filter-container", className="mb-3")
                    ], width=12, lg=4)
                ])
            ])
        ], className="shadow-sm mb-4 modern-filter-card"),
        
        # Manual Report Status
        html.Div(id="manual-report-status", className="mb-3"),
        
        # Metrics Cards Row
        dbc.Row([
            # Total Stand Value Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-dollar-sign fa-2x text-success"),
                            ], className="d-flex justify-content-center mb-3"),
                            html.H4("Total Stand Value", className="card-title text-center"),
                            html.H2(id="total-stand-value", children="$0", className="text-center text-success fw-bold"),
                            html.P(id="stand-value-period", children="Period: --", className="text-center text-muted small"),
                            html.Div(id="stand-value-yoy", className="text-center mt-2")
                        ], className="text-center")
                    ])
                ], className="shadow-sm h-100")
            ], width=12, md=6, lg=3),
            
            # Number of stands sold 
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-house fa-2x text-primary"),
                            ], className="d-flex justify-content-center mb-3"),
                            html.H4("Stands Sold", className="card-title text-center"),
                            html.H2(id="stands-sold-value", children="0", className="text-center text-primary fw-bold"),
                            html.P(id="stands-sold-period", children="Period: --", className="text-center text-muted small"),
                            html.Div(id="stands-sold-yoy", className="text-center mt-2")
                        ], className="text-center")
                    ])
                ], className="shadow-sm h-100")
            ], width=12, md=6, lg=3),
            
            # Total deposit card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-money-bill-wave fa-2x text-info"),
                            ], className="d-flex justify-content-center mb-3"),
                            html.H4("Total Deposit", className="card-title text-center"),
                            html.H2(id="total-deposit-value", children="$0", className="text-center text-info fw-bold"),
                            html.P(id="deposit-period", children="Period: --", className="text-center text-muted small"),
                            html.Div(id="deposit-yoy", className="text-center mt-2")
                        ], className="text-center")
                    ])
                ], className="shadow-sm h-100")
            ], width=12, md=6, lg=3),
            
            # Total installment card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-file-invoice-dollar fa-2x text-warning"),
                            ], className="d-flex justify-content-center mb-3"),
                            html.H4("Total Installment", className="card-title text-center"),
                            html.H2(id="total-installment-value", children="$0", className="text-center text-warning fw-bold"),
                            html.P(id="installment-period", children="Period: --", className="text-center text-muted small"),
                            html.Div(id="installment-yoy", className="text-center mt-2")
                        ], className="text-center")
                    ])
                ], className="shadow-sm h-100")
            ], width=12, md=6, lg=3),
        ], className="mb-4 g-3"),
        
        # Graphs Row
        dbc.Row([
            # Pie chart 
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-pie me-2"),
                        "Payment Distribution"
                    ], className="fw-bold"),
                    dbc.CardBody([
                        dcc.Graph(id="deposits-installments-pie", config={'displayModeBar': False})
                    ])
                ], className="shadow-sm h-100")
            ], width=12, lg=6, className="mb-4"),
            # Area Chart 
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        
                        html.Span(id="chart-title")
                    ], className="fw-bold"),
                    dbc.CardBody([
                        dcc.Graph(id="stands-sold-area", config={'displayModeBar': False})
                    ])
                ], className="shadow-sm h-100")
            ], width=12, lg=6, className="mb-4")
        ], className="g-4"),
        
        # Project Performance Bar Chart
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-bar me-2"),
                        "Project Performance - Stands Sold"
                    ], className="fw-bold"),
                    dbc.CardBody([
                        dcc.Graph(id="project-performance-bar", config={'displayModeBar': True})
                    ])
                ], className="shadow-sm h-100")
            ], width=12, className="mb-4")
        ], className="g-4")
    ], className="mt-4", fluid=True)
], className="bg-light min-vh-100 py-4")

# Callback to control dropdown visibility
@callback(
    Output("year-filter-container", "className"),
    Input("time-filter-radio", "value")
)
def toggle_year_filter(time_filter):
    base_classes = "mb-3"
    if time_filter in ["yearly", "forecast"]:
        return base_classes
    return "d-none " + base_classes

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
    return [html.I(className="fas fa-chart-line me-2"), title_map.get(time_filter, "Stands Sales Trend")]

# Project Performance Bar Chart Callback
@callback(
    Output("project-performance-bar", "figure"),
    [Input("time-filter-radio", "value"),
     Input("year-dropdown", "value")],
    prevent_initial_call=False
)   
def update_project_performance_chart(time_filter, selected_year):
    engine = get_user_db_engine()
    
    if not engine:
        # Return empty figure when not connected
        empty_fig = go.Figure()
        empty_fig.update_layout(
            title="Project Performance - Connect to Database to View Data",
            height=400,
            xaxis_title="Project",
            yaxis_title="Stands Sold",
            margin=dict(l=40, r=20, t=50, b=40)
        )
        return empty_fig
    
    try:
        # WHERE clause based on time filter
        if time_filter == "daily":
            date_condition = "DATE(s.registration_date) = CURDATE()"
        elif time_filter == "weekly":
            date_condition = "s.registration_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        else:  # yearly or forecast
            date_condition = f"YEAR(s.registration_date) = {selected_year}"
        
        # Stands sold by project with project names
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
        LIMIT 20  -- Show top 20 projects
        """
        
        project_df = pd.read_sql(project_query, engine)
        
        if project_df.empty:
            # No data found
            empty_fig = go.Figure()
            empty_fig.update_layout(
                title=f"Project Performance - No Data for Selected Period",
                height=400,
                xaxis_title="Project",
                yaxis_title="Stands Sold",
                margin=dict(l=40, r=20, t=50, b=40)
            )
            return empty_fig
        
        # Create combined labels for better readability
        project_df['project_label'] = project_df['project_name']
        
        # Bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=project_df['project_label'],
                y=project_df['stands_sold'],
                marker_color="#079b38",
                text=project_df['stands_sold'],
                textposition='auto',
                hovertemplate='<b>%{x}</b><br>' +
                             'Stands Sold: %{y}<br>' +
                             'Stands Value: $%{customdata[0]:,.2f}<br>' +
                             'Stands Available: %{customdata[1]}<br>' +
                             '<extra></extra>',
                customdata=project_df[['stands_value', 'stands_available']].values
            )
        ])
        
        # Layout
        fig.update_layout(
            title=f"Project Performance - Stands Sold ({time_filter.title()})",
            xaxis_title="Project",
            yaxis_title="Stands Sold",
            height=400,
            margin=dict(l=40, r=20, t=50, b=80),  # Increased bottom margin for rotated labels
            hovermode='closest'
        )
        
        # Rotate x-axis labels for better readability
        fig.update_xaxes(tickangle=45, tickfont=dict(size=10))
        
        # Grid
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        return fig
        
    except Exception as e:
        print(f"Error generating project performance chart: {e}")
        error_fig = go.Figure()
        error_fig.update_layout(
            title="Error Loading Project Performance Data",
            height=400,
            margin=dict(l=40, r=20, t=50, b=40)
        )
        return error_fig

# Main dashboard callback 
@callback(
    [Output("dashboard-connection-status", "children"),
     Output("total-stand-value", "children"),
     Output("stands-sold-value", "children"),
     Output("total-deposit-value", "children"),
     Output("total-installment-value", "children"),
     Output("stand-value-period", "children"),
     Output("stands-sold-period", "children"),
     Output("deposit-period", "children"),
     Output("installment-period", "children"),
     Output("deposits-installments-pie", "figure"),
     Output("stands-sold-area", "figure"),
     Output("stand-value-yoy", "children"),
     Output("stands-sold-yoy", "children"),
     Output("deposit-yoy", "children"),
     Output("installment-yoy", "children"),
     Output("report-data-store", "children")],  # Stored as JSON string
    [Input("time-filter-radio", "value"),
     Input("year-dropdown", "value")],
    prevent_initial_call=False
)
def update_dashboard_metrics(time_filter, selected_year):
    engine = get_user_db_engine()
    
    # Period mapping
    period_label_map = {
        "daily": "Today",
        "weekly": "Last 7 Days",
        "yearly": f"Year: {selected_year}",
        "forecast": f"Forecast for {selected_year}" if ML_AVAILABLE else f"Year: {selected_year}"
    }
    
    period_text = period_label_map.get(time_filter, "Period: --")
    
    if not engine:
        # Return default values when not connected
        not_connected_alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Not connected to database. Please connect first."
        ], color="warning")
        
        # Empty figures
        empty_fig = go.Figure()
        empty_fig.update_layout(
            title="No Data - Please Connect to Database",
            height=350,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        # Default YoY comparison values
        default_yoy = html.Span([
            html.I(className="fas fa-minus-circle me-1 text-muted"),
            "N/A"
        ], className="text-muted small")
        
        # Return empty JSON string for report data
        return [not_connected_alert, "$0", "0", "$0", "$0", 
                period_text, period_text, period_text, period_text,
                empty_fig, empty_fig,
                default_yoy, default_yoy, default_yoy, default_yoy, "{}"]
    
    try:
        #WHERE clause based on time filter
        if time_filter == "daily":
            date_condition = "DATE(registration_date) = CURDATE()"
            transaction_date_condition = "DATE(transaction_date) = CURDATE()"
        elif time_filter == "weekly":
            date_condition = "registration_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
            transaction_date_condition = "transaction_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        else:  # yearly or forecast
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
            WHERE {date_condition}
            """
            stands_sold_df = pd.read_sql(stands_sold_query, engine)
            current_stands_sold = stands_sold_df.iloc[0]['total_stands_sold'] if not stands_sold_df.empty and not pd.isna(stands_sold_df.iloc[0]['total_stands_sold']) else 0
        except Exception as e:
            print(f"Stands sold query error: {e}")
            current_stands_sold = 0
        formatted_stands_sold = str(current_stands_sold) if current_stands_sold else "0"
        
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
        formatted_deposit = f"${current_deposit:,.2f}" if current_deposit else "$0"
        
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
        formatted_installment = f"${current_installment:,.2f}" if current_installment else "$0"
        
        # Store data for report (as JSON string)
        report_data = {
            'total_stand_value': formatted_stand_value,
            'stands_sold': formatted_stands_sold,
            'total_deposit': formatted_deposit,
            'total_installment': formatted_installment,
            'period_text': period_text
        }
        report_data_json = json.dumps(report_data)
        
        # Connection status
        status = dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            f"Connected to database successfully! Showing data for {period_label_map[time_filter]}"
        ], color="success")
        
        # YoY Comparison (only for yearly view)
        def calculate_yoy_change(current, previous):
            if previous == 0:
                if current == 0:
                    return html.Span([
                        html.I(className="fas fa-minus-circle me-1 text-muted"),
                        "0% (No change)"
                    ], className="text-muted small")
                else:
                    return html.Span([
                        html.I(className="fas fa-arrow-up me-1 text-success"),
                        f"+∞% (Prev: $0)"
                    ], className="text-success small")
            else:
                change = ((current - previous) / previous) * 100
                if change > 0:
                    icon_class = "fas fa-arrow-up me-1 text-success"
                    text_class = "text-success small"
                elif change < 0:
                    icon_class = "fas fa-arrow-down me-1 text-danger"
                    text_class = "text-danger small"
                else:
                    icon_class = "fas fa-minus-circle me-1 text-muted"
                    text_class = "text-muted small"
                
                return html.Span([
                    html.I(className=icon_class),
                    f"{change:+.1f}% (Prev: ${previous:,.0f})"
                ], className=text_class)
        
        # Only calculate YoY for yearly view
        if time_filter == "yearly":
            previous_year = selected_year - 1
            
            # Get previous year values
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
                WHERE YEAR(registration_date) = {previous_year}
                """
                prev_sold_df = pd.read_sql(prev_sold_query, engine)
                previous_stands_sold = prev_sold_df.iloc[0]['total_stands_sold'] if not prev_sold_df.empty and not pd.isna(prev_sold_df.iloc[0]['total_stands_sold']) else 0
            except:
                previous_stands_sold = 0
                
            try:
                prev_deposit_query = f"""
                SELECT SUM(deposit_amount) AS total_deposit
                FROM customer_accounts
                WHERE YEAR(registration_date) = {previous_year} AND deleted = 0
                """
                prev_deposit_df = pd.read_sql(prev_deposit_query, engine)
                previous_deposit = prev_deposit_df.iloc[0]['total_deposit'] if not prev_deposit_df.empty and not pd.isna(prev_deposit_df.iloc[0]['total_deposit']) else 0
            except:
                previous_deposit = 0
                
            try:
                prev_installment_query = f"""
                SELECT SUM(amount) AS total_installment
                FROM customer_account_invoices
                WHERE YEAR(transaction_date) = {previous_year} AND description = 'Instalment' AND deleted = 0
                """
                prev_installment_df = pd.read_sql(prev_installment_query, engine)
                previous_installment = prev_installment_df.iloc[0]['total_installment'] if not prev_installment_df.empty and not pd.isna(prev_installment_df.iloc[0]['total_installment']) else 0
            except:
                previous_installment = 0
            
            stand_value_yoy = calculate_yoy_change(current_stand_value, previous_stand_value)
            stands_sold_yoy = calculate_yoy_change(current_stands_sold, previous_stands_sold)
            deposit_yoy = calculate_yoy_change(current_deposit, previous_deposit)
            installment_yoy = calculate_yoy_change(current_installment, previous_installment)
        else:
            # Default YoY for non-yearly views
            default_yoy = html.Span([
                html.I(className="fas fa-minus-circle me-1 text-muted"),
                "N/A"
            ], className="text-muted small")
            stand_value_yoy = stands_sold_yoy = deposit_yoy = installment_yoy = default_yoy
        
        #Deposits vs Installments
        pie_data = [current_deposit, current_installment]
        pie_labels = ["Deposits", "Installments"]
        pie_colors = ["#28a745", '#ffc107']
        
        if sum(pie_data) > 0:
            pie_fig = go.Figure(data=[go.Pie(
                labels=pie_labels, 
                values=pie_data, 
                hole=.4,
                marker=dict(colors=pie_colors),
                textinfo='percent+label',
                hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<br>(%{percent})",
                textposition='inside'
            )])
            pie_fig.update_layout(
                title_text=f'Payment Distribution<br>({period_label_map[time_filter]})',
                height=350,
                margin=dict(l=20, r=20, t=50, b=20),
                showlegend=False
            )
        else:
            pie_fig = go.Figure()
            pie_fig.update_layout(
                title=f"No Payment Data Available<br>({period_label_map[time_filter]})",
                height=350,
                margin=dict(l=20, r=20, t=50, b=20)
            )
        
        # Stands Sold Trend(area graph)
        try:
            if time_filter == "yearly" or time_filter == "forecast":
                # trend for the selected year (monthly breakdown)
                trend_query = f"""
                SELECT 
                    MONTH(registration_date) AS month,
                    COUNT(stand_number) AS total_stands_sold
                FROM Stands
                WHERE YEAR(registration_date) = {selected_year}
                GROUP BY MONTH(registration_date)
                ORDER BY month
                """
                trend_df = pd.read_sql(trend_query, engine)
                
                #complete month series
                all_months = pd.DataFrame({'month': range(1, 13)})
                trend_df = all_months.merge(trend_df, on='month', how='left').fillna(0)
                
                if time_filter == "forecast" and ML_AVAILABLE and not trend_df.empty:
                    #forecast data
                    forecast_df = create_forecast(trend_df, months_ahead=3)
                    
                    if not forecast_df.empty and len(forecast_df[forecast_df['type'] == 'forecast']) > 0:
                        # Plotting actual and forecast data
                        area_fig = go.Figure()
                        
                        # Actual data
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
                        
                        # Forecast data
                        forecast_points_df = forecast_df[forecast_df['type'] == 'forecast']
                        if not forecast_points_df.empty and not actual_df.empty:
                            #last actual point to connect smoothly
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
                            
                            #confidence interval (simplified)
                            upper_bound = [y * 1.1 for y in forecast_y]
                            lower_bound = [max(0, y * 0.9) for y in forecast_y]
                            area_fig.add_trace(go.Scatter(
                                x=forecast_x + forecast_x[::-1],
                                y=upper_bound + lower_bound[::-1],
                                fill='toself',
                                fillcolor='rgba(255,193,7,0.2)',
                                line=dict(color='rgba(255,255,255,0)'),
                                hoverinfo="skip",
                                showlegend=False,
                                name='Confidence Interval'
                            ))
                        
                        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        extended_month_names = month_names + [f"Pred {i+1}" for i in range(3)]
                        
                        # Set up x-axis
                        max_month = max(forecast_df['month']) if not forecast_df.empty else 12
                        area_fig.update_layout(
                            xaxis=dict(
                                tickmode='array',
                                tickvals=list(range(1, min(max_month + 1, 16))),
                                ticktext=extended_month_names[:min(max_month, 15)]
                            )
                        )
                    else:
                        # Fallback to regular chart if forecast fails
                        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        x_data = [month_names[m-1] if 1 <= m <= 12 else f"Month {m}" for m in trend_df['month']]
                        y_data = trend_df['total_stands_sold'].tolist()
                        
                        area_fig = go.Figure()
                        area_fig.add_trace(go.Scatter(
                            x=x_data,
                            y=y_data,
                            mode='lines+markers',
                            fill='tozeroy',
                            name='Stands Sold',
                            line=dict(color="#007bff", width=3),
                            marker=dict(size=6)
                        ))
                else:
                    # Regular yearly view
                    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    x_data = [month_names[m-1] if 1 <= m <= 12 else f"Month {m}" for m in trend_df['month']]
                    y_data = trend_df['total_stands_sold'].tolist()
                    
                    area_fig = go.Figure()
                    area_fig.add_trace(go.Scatter(
                        x=x_data,
                        y=y_data,
                        mode='lines+markers',
                        fill='tozeroy',
                        name='Stands Sold',
                        line=dict(color="#007bff", width=3),
                        marker=dict(size=6)
                    ))
                
                area_fig.update_layout(
                    title=f"{'Monthly Forecast' if time_filter == 'forecast' and ML_AVAILABLE else 'Monthly Trend'} ({selected_year})",
                    xaxis_title='Month',
                    yaxis_title='Stands Sold',
                    template='plotly_white',
                    height=350,
                    margin=dict(l=40, r=20, t=50, b=40)
                )
                
            elif time_filter == "weekly":
                #daily trend for last 7 days
                trend_query = """
                SELECT 
                    DATE(registration_date) AS day,
                    COUNT(stand_number) AS total_stands_sold
                FROM Stands
                WHERE registration_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                GROUP BY DATE(registration_date)
                ORDER BY day
                """
                trend_df = pd.read_sql(trend_query, engine)
                
                #last 7 days
                end_date = datetime.date.today()
                start_date = end_date - datetime.timedelta(days=6)
                date_range = pd.date_range(start=start_date, end=end_date, freq='D')
                date_df = pd.DataFrame({'day': date_range.date})
                trend_df['day'] = pd.to_datetime(trend_df['day']).dt.date
                trend_df = date_df.merge(trend_df, left_on='day', right_on='day', how='left').fillna(0)
                
                x_data = [d.strftime('%a') for d in trend_df['day']]
                y_data = trend_df['total_stands_sold'].tolist()
                
                area_fig = go.Figure()
                area_fig.add_trace(go.Scatter(
                    x=x_data,
                    y=y_data,
                    mode='lines+markers',
                    fill='tozeroy',
                    name='Stands Sold',
                    line=dict(color="#007bff", width=3),
                    marker=dict(size=6)
                ))
                area_fig.update_layout(
                    title='Daily Stands Sales Trend (Last 7 Days)',
                    xaxis_title='Day',
                    yaxis_title='Stands Sold',
                    template='plotly_white',
                    height=350,
                    margin=dict(l=40, r=20, t=50, b=40)
                )
                
            else:  # daily
                # hourly trend for today
                trend_query = """
                SELECT 
                    HOUR(registration_date) AS hour,
                    COUNT(stand_number) AS total_stands_sold
                FROM Stands
                WHERE DATE(registration_date) = CURDATE()
                GROUP BY HOUR(registration_date)
                ORDER BY hour
                """
                trend_df = pd.read_sql(trend_query, engine)
                
                # Generate 24 hours
                all_hours = pd.DataFrame({'hour': range(24)})
                trend_df = all_hours.merge(trend_df, on='hour', how='left').fillna(0)
                x_data = [f"{h}:00" for h in trend_df['hour']]
                y_data = trend_df['total_stands_sold'].tolist()
                
                area_fig = go.Figure()
                area_fig.add_trace(go.Scatter(
                    x=x_data,
                    y=y_data,
                    mode='lines+markers',
                    fill='tozeroy',
                    name='Stands Sold',
                    line=dict(color="#001020", width=3),
                    marker=dict(size=6)
                ))
                area_fig.update_layout(
                    title='Hourly Stands Sales Trend (Today)',
                    xaxis_title='Hour',
                    yaxis_title='Stands Sold',
                    template='plotly_white',
                    height=350,
                    margin=dict(l=40, r=20, t=50, b=40)
                )
                
        except Exception as e:
            print(f"Chart generation error: {e}")
            area_fig = go.Figure()
            area_fig.update_layout(
                title='Error Loading Trend Data',
                height=350,
                margin=dict(l=40, r=20, t=50, b=40)
            )

        return [status, formatted_stand_value, formatted_stands_sold, formatted_deposit, 
                formatted_installment, period_text, period_text,
                period_text, period_text,
                pie_fig, area_fig,
                stand_value_yoy, stands_sold_yoy, deposit_yoy, installment_yoy, report_data_json]
        
    except Exception as e:
        print(f"Main callback error: {e}")
        error_alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Database error: {str(e)}"
        ], color="danger")
        
        # Empty figures for error case
        empty_fig = go.Figure()
        empty_fig.update_layout(
            title="Error Loading Data",
            height=350,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        # Default YoY comparison values
        default_yoy = html.Span([
            html.I(className="fas fa-minus-circle me-1 text-muted"),
            "N/A"
        ], className="text-muted small")
        
        return [error_alert, "$0", "0", "$0", "$0", 
                period_text, period_text, period_text, period_text,
                empty_fig, empty_fig,
                default_yoy, default_yoy, default_yoy, default_yoy, "{}"]
    finally:
        if engine:
            try:
                engine.dispose()
            except:
                pass