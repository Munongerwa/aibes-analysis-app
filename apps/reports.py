# reports.py (complete updated version with adjusted table sizing)
import os
import sqlite3
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  
import io
from sqlalchemy import create_engine, text
import pandas as pd
from reportlab.platypus import PageBreak
import qrcode
from urllib.parse import quote
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import ssl
import hashlib
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self, db_connection_string=None):
        self.db_connection_string = db_connection_string
        self.user_id = self._generate_user_id(db_connection_string) if db_connection_string else "default_user"
        self.reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_reports")
        self.ensure_reports_directory()
        
    def _generate_user_id(self, db_connection_string):
        """Generate a unique user ID based on database connection string"""
        if db_connection_string:
            # Create a hash of the connection string to identify the user/database
            return hashlib.md5(db_connection_string.encode()).hexdigest()[:16]
        return "default_user"
    
    def ensure_reports_directory(self):
        """Create reports directory if it doesn't exist"""
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
    
    def get_user_reports_db_path(self):
        """Get the path to the user-specific reports database"""
        return os.path.join(self.reports_dir, f"reports_{self.user_id}.db")
    
    def get_company_info(self):
        """Get company information from settings"""
        try:
            if not self.db_connection_string:
                return {
                    'company_name': 'AIBES DATA ANALYSIS',
                    'logo_path': None
                }
            
            engine = create_engine(self.db_connection_string)
            query = "SELECT company_name, logo_path FROM aibesinsights_company_settings WHERE id = 1"
            result = pd.read_sql(query, engine)
            engine.dispose()
            
            if not result.empty:
                row = result.iloc[0]
                return {
                    'company_name': row['company_name'] or 'AIBES DATA ANALYSIS',
                    'logo_path': row['logo_path']
                }
            else:
                return {
                    'company_name': 'AIBES DATA ANALYSIS',
                    'logo_path': None
                }
        except Exception as e:
            print(f"Error getting company info: {e}")
            return {
                'company_name': 'AIBES DATA ANALYSIS',
                'logo_path': None
            }
    
    def get_email_settings(self):
        """Get email configuration from settings"""
        try:
            if not self.db_connection_string:
                return None
                
            engine = create_engine(self.db_connection_string)
            query = """
            SELECT smtp_server, smtp_port, email_username, email_password, 
                   sender_email, sender_name 
            FROM aibesinsights_email_settings WHERE id = 1
            """
            result = pd.read_sql(query, engine)
            engine.dispose()
            
            if not result.empty:
                row = result.iloc[0]
                return {
                    'smtp_server': row['smtp_server'] or 'smtp.gmail.com',
                    'smtp_port': row['smtp_port'] or 587,
                    'username': row['email_username'],
                    'password': row['email_password'],
                    'sender_email': row['sender_email'],
                    'sender_name': row['sender_name'] or 'AIBES Reports System'
                }
            return None
        except Exception as e:
            print(f"Error getting email settings: {e}")
            return None
    
    def get_project_targets(self, project_id, start_date, end_date, report_type):
        """Get project-specific targets for the specified period"""
        try:
            if not self.db_connection_string:
                return {'sales_target': 0, 'stands_target': 0}
            
            engine = create_engine(self.db_connection_string)
            
            # Determine target type and conditions based on report period
            if report_type == "yearly":
                target_type = "yearly"
                target_year = start_date.year
                conditions = f"project_id = {project_id} AND target_type = '{target_type}' AND target_year = {target_year}"
            elif report_type == "monthly":
                target_type = "monthly"
                target_year = start_date.year
                target_month = start_date.month
                conditions = f"project_id = {project_id} AND target_type = '{target_type}' AND target_year = {target_year} AND target_month = {target_month}"
            elif report_type == "weekly":
                target_type = "weekly"
                target_year = start_date.year
                # Calculate week number
                week_number = start_date.isocalendar()[1]
                conditions = f"project_id = {project_id} AND target_type = '{target_type}' AND target_year = {target_year} AND target_week = {week_number}"
            else:
                # For custom/daily, return zeros
                engine.dispose()
                return {'sales_target': 0, 'stands_target': 0}
            
            query = f"""
            SELECT sales_target, stands_target
            FROM aibesinsights_project_targets
            WHERE {conditions}
            """
            
            result = pd.read_sql(query, engine)
            engine.dispose()
            
            if not result.empty and len(result) > 0:
                sales_target = result.iloc[0]['sales_target'] if not pd.isna(result.iloc[0]['sales_target']) else 0
                stands_target = result.iloc[0]['stands_target'] if not pd.isna(result.iloc[0]['stands_target']) else 0
                return {
                    'sales_target': sales_target,
                    'stands_target': stands_target
                }
            else:
                return {
                    'sales_target': 0,
                    'stands_target': 0
                }
        except Exception as e:
            print(f"Error getting project targets: {e}")
            return {
                'sales_target': 0,
                'stands_target': 0
            }
    
    def get_period_targets(self, start_date, end_date, report_type):
        """Get overall targets for the specified period from the connected database"""
        try:
            if not self.db_connection_string:
                return {'sales_target': 0, 'stands_target': 0}
            
            engine = create_engine(self.db_connection_string)
            
            # Determine target type and conditions based on report period
            if report_type == "yearly":
                target_type = "yearly"
                target_year = start_date.year
                conditions = f"target_type = '{target_type}' AND target_year = {target_year}"
            elif report_type == "monthly":
                target_type = "monthly"
                target_year = start_date.year
                target_month = start_date.month
                conditions = f"target_type = '{target_type}' AND target_year = {target_year} AND target_month = {target_month}"
            elif report_type == "weekly":
                target_type = "weekly"
                target_year = start_date.year
                # Calculate week number
                week_number = start_date.isocalendar()[1]
                conditions = f"target_type = '{target_type}' AND target_year = {target_year} AND target_week = {week_number}"
            else:
                # For custom/daily, return zeros
                engine.dispose()
                return {'sales_target': 0, 'stands_target': 0}
            
            query = f"""
            SELECT SUM(sales_target) as total_sales_target, SUM(stands_target) as total_stands_target
            FROM aibesinsights_targets
            WHERE {conditions}
            """
            
            result = pd.read_sql(query, engine)
            engine.dispose()
            
            if not result.empty and len(result) > 0:
                sales_target = result.iloc[0]['total_sales_target'] if not pd.isna(result.iloc[0]['total_sales_target']) else 0
                stands_target = result.iloc[0]['total_stands_target'] if not pd.isna(result.iloc[0]['total_stands_target']) else 0
                return {
                    'sales_target': sales_target,
                    'stands_target': stands_target
                }
            else:
                return {
                    'sales_target': 0,
                    'stands_target': 0
                }
        except Exception as e:
            print(f"Error getting targets: {e}")
            return {
                'sales_target': 0,
                'stands_target': 0
            }
    
    def get_custom_data(self, start_date, end_date, report_type="custom"):
        """Fetch data for custom date range with project names instead of IDs"""
        if not self.db_connection_string:
            return {}
            
        try:
            engine = create_engine(self.db_connection_string)
            
            # Format dates for SQL
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            date_condition = f"DATE(registration_date) BETWEEN '{start_date_str}' AND '{end_date_str}'"
            transaction_date_condition = f"DATE(transaction_date) BETWEEN '{start_date_str}' AND '{end_date_str}'"
            
            # Get project-based data using project_id joined with Projects table to get project names
            project_data_query = f"""
SELECT 
    p.name AS project_name,
    p.id AS project_id,
    COUNT(s.stand_number) AS stands_sold,
    SUM(s.sale_value) AS stands_value,
    COUNT(CASE WHEN s.available = 1 AND s.to_sale = 1 THEN 1 END) AS stands_available,
    COUNT(CASE WHEN s.available = 1 AND s.to_sale = 0 THEN 1 END) AS stands_reserved
FROM Projects p
INNER JOIN Stands s ON p.id = s.project_id
WHERE {date_condition}
GROUP BY p.id, p.name
ORDER BY stands_value DESC
            """
            project_df = pd.read_sql(project_data_query, engine)
            
            # Add total_stands column for project status chart
            if not project_df.empty:
                project_df['total_stands'] = project_df['stands_sold'] + project_df['stands_available'] + project_df['stands_reserved']
            
            # Get agent sales data
            agent_data_query = f"""
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
            agent_df = pd.read_sql(agent_data_query, engine)
            
            # Get overall summary
            summary_query = f"""
            SELECT 
                COUNT(stand_number) AS total_stands_sold,
                SUM(sale_value) AS total_stand_value,
                COUNT(CASE WHEN available = 0 THEN stand_number END) AS total_stands_sold_count,
                COUNT(CASE WHEN available = 1 AND to_sale = 1 THEN stand_number END) AS total_stands_available,
                COUNT(CASE WHEN available = 1 AND to_sale = 0 THEN stand_number END) AS total_stands_reserved
            FROM Stands
            WHERE {date_condition}
            """
            summary_df = pd.read_sql(summary_query, engine)
            
            #Total deposit
            total_deposit_query = f"""
            SELECT SUM(deposit_amount) AS total_deposit
            FROM customer_accounts
            WHERE {date_condition}
            """
            deposit_df = pd.read_sql(total_deposit_query, engine)
            total_deposit = deposit_df.iloc[0]['total_deposit'] if not deposit_df.empty and not pd.isna(deposit_df.iloc[0]['total_deposit']) else 0
            
            # Total installment
            total_installment_query = f"""
            SELECT SUM(amount) AS total_installment
            FROM customer_account_invoices
            WHERE {transaction_date_condition} AND description = 'Instalment' AND deleted = 0
            """
            installment_df = pd.read_sql(total_installment_query, engine)
            total_installment = installment_df.iloc[0]['total_installment'] if not installment_df.empty and not pd.isna(installment_df.iloc[0]['total_installment']) else 0
            
            engine.dispose()
            
            return {
                'project_data': project_df,
                'agent_data': agent_df,
                'summary': {
                    'total_stand_value': summary_df.iloc[0]['total_stand_value'] if not summary_df.empty and not pd.isna(summary_df.iloc[0]['total_stand_value']) else 0,
                    'total_stands_sold': summary_df.iloc[0]['total_stands_sold_count'] if not summary_df.empty and not pd.isna(summary_df.iloc[0]['total_stands_sold_count']) else 0,
                    'total_stands_available': summary_df.iloc[0]['total_stands_available'] if not summary_df.empty and not pd.isna(summary_df.iloc[0]['total_stands_available']) else 0,
                    'total_stands_reserved': summary_df.iloc[0]['total_stands_reserved'] if not summary_df.empty and not pd.isna(summary_df.iloc[0]['total_stands_reserved']) else 0,
                    'total_deposit': total_deposit,
                    'total_installment': total_installment
                },
                'start_date': start_date,
                'end_date': end_date,
                'report_type': report_type
            }
        except Exception as e:
            print(f"Error fetching custom data: {e}")
            return {}
    
    def create_project_comparison_chart(self, project_df, title="Project Comparison"):
        """Create a comparison chart showing stands sold vs sales value for each project"""
        try:
            if project_df.empty:
                return None
            
            # Create comparison chart
            fig, ax1 = plt.subplots(figsize=(12, 6))
            
            # Create project labels
            project_labels = project_df['project_name'].tolist()
            
            # Plot stands sold (bar chart)
            bars = ax1.bar(range(len(project_labels)), project_df['stands_sold'], 
                          color="#073c5d", alpha=0.7, label='Stands Sold', width=0.6)
            ax1.set_xlabel('Projects', fontsize=12)
            ax1.set_ylabel('Stands Sold', color="#850b5c", fontsize=12)
            ax1.tick_params(axis='y', labelcolor="#850b5c")
            
            # Add value labels on bars
            for i, (bar, value) in enumerate(zip(bars, project_df['stands_sold'])):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                        str(int(value)), ha='center', va='bottom', fontweight='bold', 
                        color="#850b5c")
            
            # Create second y-axis for sales value (line plot)
            ax2 = ax1.twinx()
            line = ax2.plot(range(len(project_labels)), project_df['stands_value'], 
                           color="#e2c419", marker='o', linewidth=3, markersize=8, 
                           label='Sales Value ($)')
            ax2.set_ylabel('Sales Value ($)', color="#0a7981", fontsize=12)
            ax2.tick_params(axis='y', labelcolor="#0a7981")
            
            # Format sales values on line points
            for i, (x, y) in enumerate(zip(range(len(project_labels)), project_df['stands_value'])):
                ax2.text(x, y + (y * 0.05), f'${y:,.0f}', ha='center', va='bottom', 
                        fontweight='bold', color="#0a7981")
            
            # Set x-axis labels
            ax1.set_xticks(range(len(project_labels)))
            ax1.set_xticklabels(project_labels, rotation=45, ha='right')
            
            # Title and legend
            plt.title(title, fontsize=14, pad=20)
            ax1.grid(True, alpha=0.3, axis='y')
            
            # Improve styling
            ax1.spines['top'].set_visible(False)
            ax2.spines['top'].set_visible(False)
            ax1.set_ylim(0, project_df['stands_sold'].max() * 1.3)
            ax2.set_ylim(0, project_df['stands_value'].max() * 1.3)
            
            # Add legend
            bars_legend = plt.Rectangle((0,0),1,1, fc="#073c5d", alpha=0.7)
            line_legend = plt.Line2D([0], [0], color="#e2c419", linewidth=3, marker='o')
            ax1.legend([bars_legend, line_legend], ['Stands Sold', 'Sales Value ($)'], 
                      loc='upper left')
            
            # Adjust layout
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=300, facecolor='white')
            img_buffer.seek(0)
            plt.close(fig)
            
            return img_buffer
        except Exception as e:
            print(f"Error creating project comparison chart: {e}")
            return None
    
    def create_agent_sales_chart(self, agent_df, title="Agent Sales Performance"):
        """Create a horizontal stacked bar chart showing agent sales by project"""
        try:
            if agent_df.empty:
                return None
            
            # Aggregate data by agent for total sales
            agent_summary = agent_df.groupby('agent_name').agg({
                'stands_sold': 'sum',
                'total_sales': 'sum'
            }).reset_index()
            agent_summary = agent_summary.sort_values('total_sales', ascending=True).head(15)  # Top 15 agents
            
            if agent_summary.empty:
                return None
            
            # Create horizontal bar chart
            fig, ax = plt.subplots(figsize=(12, max(6, len(agent_summary) * 0.5)))  # Dynamic height
            
            y_pos = range(len(agent_summary))
            bars = ax.barh(y_pos, agent_summary['total_sales'], 
                          color='#007bff', height=0.7, alpha=0.8)
            
            # Add value labels on bars
            for i, (bar, value) in enumerate(zip(bars, agent_summary['total_sales'])):
                ax.text(bar.get_width() + (bar.get_width() * 0.01), bar.get_y() + bar.get_height()/2,
                       f'${value:,.0f}\n({agent_summary.iloc[i]["stands_sold"]} stands)',
                       ha='left', va='center', fontweight='bold', fontsize=9)
            
            # Styling
            ax.set_yticks(y_pos)
            ax.set_yticklabels(agent_summary['agent_name'])
            ax.set_xlabel('Total Sales ($)', fontsize=12)
            ax.set_title(title, fontsize=14, pad=20)
            ax.grid(True, alpha=0.3, axis='x')
            
            # Remove top and right spines
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=300, facecolor='white')
            img_buffer.seek(0)
            plt.close(fig)
            
            return img_buffer
        except Exception as e:
            print(f"Error creating agent sales chart: {e}")
            return None
    
    def create_stands_vs_target_chart(self, project_df, title="Stands Sold vs Target by Project"):
        """Create a bar chart comparing stands sold vs target for each project"""
        try:
            if project_df.empty:
                return None
            
            # Create comparison chart for stands
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Create project labels
            project_labels = project_df['project_name'].tolist()
            x_pos = range(len(project_labels))
            
            # Plot actual stands sold and targets side by side
            width = 0.35
            bars1 = ax.bar([x - width/2 for x in x_pos], project_df['stands_sold'], 
                          width, label='Actual Stands Sold', color='#073c5d', alpha=0.8)
            bars2 = ax.bar([x + width/2 for x in x_pos], project_df['target_stands'], 
                          width, label='Target Stands', color='#e2c419', alpha=0.8)
            
            # Add value labels on bars
            for i, (bar, value) in enumerate(zip(bars1, project_df['stands_sold'])):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                        str(int(value)), ha='center', va='bottom', fontweight='bold')
            
            for i, (bar, value) in enumerate(zip(bars2, project_df['target_stands'])):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                        str(int(value)), ha='center', va='bottom', fontweight='bold')
            
            # Styling
            ax.set_xlabel('Projects', fontsize=12)
            ax.set_ylabel('Number of Stands', fontsize=12)
            ax.set_title(title, fontsize=14, pad=20)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(project_labels, rotation=45, ha='right')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
            
            # Remove top and right spines
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=300, facecolor='white')
            img_buffer.seek(0)
            plt.close(fig)
            
            return img_buffer
        except Exception as e:
            print(f"Error creating stands vs target chart: {e}")
            return None
    
    def create_value_vs_target_chart(self, project_df, title="Sales Value vs Target by Project"):
        """Create a bar chart comparing sales value vs target for each project"""
        try:
            if project_df.empty:
                return None
            
            # Create comparison chart for sales value
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Create project labels
            project_labels = project_df['project_name'].tolist()
            x_pos = range(len(project_labels))
            
            # Plot actual sales value and targets side by side
            width = 0.35
            bars1 = ax.bar([x - width/2 for x in x_pos], project_df['stands_value'], 
                          width, label='Actual Sales Value', color='#0a7981', alpha=0.8)
            bars2 = ax.bar([x + width/2 for x in x_pos], project_df['target_value'], 
                          width, label='Target Sales Value', color='#ff6b6b', alpha=0.8)
            
            # Add value labels on bars
            for i, (bar, value) in enumerate(zip(bars1, project_df['stands_value'])):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (bar.get_height() * 0.01), 
                        f'${value:,.0f}', ha='center', va='bottom', fontweight='bold')
            
            for i, (bar, value) in enumerate(zip(bars2, project_df['target_value'])):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (bar.get_height() * 0.01), 
                        f'${value:,.0f}', ha='center', va='bottom', fontweight='bold')
            
            # Styling
            ax.set_xlabel('Projects', fontsize=12)
            ax.set_ylabel('Sales Value ($)', fontsize=12)
            ax.set_title(title, fontsize=14, pad=20)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(project_labels, rotation=45, ha='right')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
            
            # Remove top and right spines
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=300, facecolor='white')
            img_buffer.seek(0)
            plt.close(fig)
            
            return img_buffer
        except Exception as e:
            print(f"Error creating value vs target chart: {e}")
            return None
    
    def send_report_via_email(self, filepath, recipient_emails, subject=None, message=None):
        """Send report via email"""
        try:
            # Getting email settings
            email_settings = self.get_email_settings()
            if not email_settings:
                return False, "Email settings not configured. Please configure email settings in the Settings page."
            
            # Checking required fields
            if not email_settings.get('username') or not email_settings.get('password'):
                return False, "Email username and password not configured."
            
            if not email_settings.get('sender_email'):
                return False, "Sender email address not configured."
            
            if not recipient_emails:
                return False, "No recipient emails provided"
            
            # Default values
            if not subject:
                subject = f"Sales Report - {os.path.basename(filepath)}"
            
            if not message:
                message = "<p>Please find the attached sales report.</p>"
            
            # Message creation
            msg = MIMEMultipart()
            msg['From'] = f"{email_settings['sender_name']} <{email_settings['sender_email']}>"
            msg['To'] = ", ".join(recipient_emails) if isinstance(recipient_emails, list) else recipient_emails
            msg['Subject'] = subject
            
            # Adding html body
            html_body = f"""
            <html>
                <body>
                    <h2>Sales Report</h2>
                    <p>{message}</p>
                    <hr>
                    <p><em>This is an automated message from {email_settings['sender_name']}</em></p>
                </body>
            </html>
            """
            msg.attach(MIMEText(html_body, 'html'))
            
            # Adding attachment
            if os.path.exists(filepath):
                with open(filepath, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(filepath)}'
                )
                msg.attach(part)
            else:
                return False, f"Report file not found: {filepath}"
            
            # Sending email
            try:
                context = ssl.create_default_context()
                with smtplib.SMTP(email_settings['smtp_server'], email_settings['smtp_port']) as server:
                    server.starttls(context=context)
                    server.login(email_settings['username'], email_settings['password'])
                    server.send_message(msg)
                
                return True, "Report sent successfully"
            except smtplib.SMTPAuthenticationError:
                return False, "Email authentication failed. Please check your username and password."
            except smtplib.SMTPRecipientsRefused:
                return False, "All recipient addresses were refused. Please check the email addresses."
            except smtplib.SMTPServerDisconnected:
                return False, "SMTP server disconnected. Please check your SMTP settings."
            except Exception as e:
                return False, f"Failed to send email: {str(e)}"
                
        except Exception as e:
            print(f"Error sending email: {e}")
            return False, f"Failed to send email: {str(e)}"
    
    def delete_report_from_db(self, filename):
        """Delete a report from the connected database"""
        try:
            if not self.db_connection_string:
                return False, "Database not connected"
                
            engine = create_engine(self.db_connection_string)
            
            # Delete report from database
            delete_query = text("""
            DELETE FROM aibesanalytics_reports 
            WHERE filename = :filename
            """)
            
            with engine.connect() as conn:
                trans = conn.begin()
                try:
                    result = conn.execute(delete_query, {'filename': filename})
                    rows_affected = result.rowcount
                    trans.commit()
                    
                    if rows_affected > 0:
                        logger.info(f"Report {filename} has been deleted from the database aibesanalytics_reports table")
                        return True, "Report deleted successfully from database"
                    else:
                        return False, "Report not found in database"
                except Exception as e:
                    trans.rollback()
                    raise e
            
            engine.dispose()
        except Exception as e:
            print(f"Error deleting report from database: {e}")
            return False, f"Failed to delete report from database: {str(e)}"
    
    def delete_report(self, filename):
        """Delete a report file and its database record"""
        try:
            # Validation of the filename parameter
            if not filename:
                return False, "No filename provided"
            
            # Delete the report file
            filepath = os.path.join(self.reports_dir, filename)
            file_deleted = False
            
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    file_deleted = True
                    logger.info(f"Report file {filename} has been deleted from filesystem")
                except Exception as e:
                    return False, f"Failed to delete report file: {str(e)}"
            else:
                # File doesn't exist but will still remove the record
                file_deleted = True
                logger.info(f"Report file {filename} not found in filesystem, proceeding with database deletion")
            
            # Delete report from database
            db_deleted, db_message = self.delete_report_from_db(filename)
            
            if file_deleted and db_deleted:
                return True, "Report deleted successfully from both filesystem and database"
            elif file_deleted:
                return True, f"Report file deleted successfully. Database deletion message: {db_message}"
            else:
                return False, "Failed to delete report"
                
        except Exception as e:
            print(f"Error deleting report: {e}")
            return False, f"Failed to delete report: {str(e)}"
    
    def create_cover_page(self, company_info, report_type, start_date, end_date):
        """Create a stylish cover page for the report"""
        from reportlab.platypus import Spacer, PageBreak
        from reportlab.lib.units import inch
        
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles for cover page
        title_style = ParagraphStyle(
            'CoverTitle',
            parent=styles['Heading1'],
            fontSize=40,
            spaceAfter=30,
            alignment=1,
            textColor=colors.HexColor("#0F1013"),
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CoverSubtitle',
            parent=styles['Heading2'],
            fontSize=25,
            spaceAfter=25,
            alignment=1,
            textColor=colors.HexColor("#0D70E1"),
            fontName='Helvetica'
        )
        
        info_style = ParagraphStyle(
            'CoverInfo',
            parent=styles['Normal'],
            fontSize=14,
            spaceAfter=15,
            alignment=1,
            textColor=colors.HexColor("#333333"),
            fontName='Helvetica'
        )
        
        date_style = ParagraphStyle(
            'CoverDate',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=10,
            alignment=1,
            textColor=colors.HexColor("#666666"),
            fontName='Helvetica'
        )
        
        # Add some initial spacing
        story.append(Spacer(1, 2*inch))
        
        # Add company logo if available
        if company_info['logo_path'] and os.path.exists(company_info['logo_path']):
            try:
                # Position logo at top-left corner
                logo_img = Image(company_info['logo_path'], width=1.5*inch, height=0.75*inch)
                story.append(logo_img)
                story.append(Spacer(1, 0.5*inch))
            except Exception as e:
                print(f"Warning: Could not load company logo: {e}")
        
        # Add company name in the center
        story.append(Paragraph(company_info['company_name'], title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Add report title
        story.append(Paragraph("SALES AND LAND-BANK REPORT", subtitle_style))
        story.append(Spacer(1, 0.5*inch))
        
        # Add report type
        report_type_text = report_type.title()
        story.append(Paragraph(f"Report Type: {report_type_text}", info_style))
        
        # Add period range
        period_text = f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        story.append(Paragraph(period_text, info_style))
        
        # Add generation timestamp
        generated_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        story.append(Paragraph(f"Generated on: {generated_time}", date_style))
        
        # Add decorative line
        story.append(Spacer(1, 0.8*inch))
        story.append(Paragraph("—" * 50, ParagraphStyle('Line', alignment=1, textColor=colors.HexColor("#cccccc"))))
        
        # Add company slogan or additional info
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("AIBES Analysis Data-Driven Insights for Better Decision Making", 
                              ParagraphStyle('Slogan', alignment=1, fontSize=10, 
                                           textColor=colors.HexColor("#888888"))))
        
        story.append(PageBreak())
        return story
    
    def generate_pdf_report(self, start_date, end_date, report_type="custom"):
        """Generate PDF report for custom date range with company branding - returns filepath or None"""
        try:
            filepath, error = self._generate_pdf_report_internal(start_date, end_date, report_type)
            if error:
                print(f"Report generation error: {error}")
                return None
            return filepath
        except Exception as e:
            print(f"Error in generate_pdf_report: {e}")
            return None
    
    def _generate_pdf_report_internal(self, start_date, end_date, report_type="custom"):
        """Internal method that generates PDF report and returns (filepath, error)"""
        try:
            # Get data
            data = self.get_custom_data(start_date, end_date, report_type)
            if not data:
                return None, "No data available for the selected period"
            
            # Get overall targets for the period
            overall_targets = self.get_period_targets(start_date, end_date, report_type)
            
            # Get company info
            company_info = self.get_company_info()
            
            # Generate filename with user ID to ensure uniqueness
            filename = f"report_{self.user_id}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_{report_type}.pdf"
            filepath = os.path.join(self.reports_dir, filename)
            
            # PDF document
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Add cover page
            cover_story = self.create_cover_page(company_info, report_type, start_date, end_date)
            story.extend(cover_story)
            
            # Custom styles for content pages
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=1, 
                textColor=colors.HexColor("#0F1013")
            )
            
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=20,
                textColor=colors.HexColor("#2C78BE")
            )
            
            # Content Header
            story.append(Paragraph(company_info['company_name'], title_style))
            story.append(Paragraph("Sales Report", styles['Heading2']))
            story.append(Spacer(1, 20))
            
            # Report metadata
            meta_style = styles['Normal']
            story.append(Paragraph(f"<b>Report Type:</b> {report_type.title()}", meta_style))
            story.append(Paragraph(f"<b>Period:</b> {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}", meta_style))
            story.append(Paragraph(f"<b>Generated on:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", meta_style))
            story.append(Spacer(1, 30))
            
            # Overall Summary table with targets
            summary_data = data['summary']
            actual_sales = summary_data['total_stand_value'] or 0
            actual_stands = summary_data['total_stands_sold'] or 0
            target_sales = overall_targets['sales_target'] or 0
            target_stands = overall_targets['stands_target'] or 0
            
            sales_variance = actual_sales - target_sales
            stands_variance = actual_stands - target_stands
            
            # Format variances with proper signs (no colors)
            if sales_variance >= 0:
                sales_variance_text = f"+${sales_variance:,.2f}"
            else:
                sales_variance_text = f"-${abs(sales_variance):,.2f}"
                
            if stands_variance >= 0:
                stands_variance_text = f"+{stands_variance:,}"
            else:
                stands_variance_text = f"-{abs(stands_variance):,}"
            
            summary_table_data = [
                ['Metric', 'Actual', 'Target', 'Variance'],
                ['Total Stand Value', 
                 f"${actual_sales:,.2f}", 
                 f"${target_sales:,.2f}",
                 sales_variance_text],
                ['Total Stands Sold', 
                 str(actual_stands), 
                 str(target_stands),
                 stands_variance_text],
                ['Total Stands Available', str(summary_data['total_stands_available'] or 0), 'N/A', 'N/A'],
                ['Total Stands Reserved', str(summary_data['total_stands_reserved'] or 0), 'N/A', 'N/A'],
                ['Total Deposit', f"${summary_data['total_deposit'] or 0:,.2f}", 'N/A', 'N/A'],
                ['Total Installment', f"${summary_data['total_installment'] or 0:,.2f}", 'N/A', 'N/A']
            ]
            
            summary_table = Table(summary_table_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F3559")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            
            story.append(Paragraph("Summary with Targets", subtitle_style))
            story.append(summary_table)
            story.append(Spacer(1, 30))
            
            # Project-wise Analysis - Separated into two tables
            if not data['project_data'].empty:
                # Add target information to project data
                project_data_with_targets = data['project_data'].copy()
                target_stands_list = []
                target_value_list = []
                
                for _, row in project_data_with_targets.iterrows():
                    project_id = row['project_id']
                    project_targets = self.get_project_targets(project_id, start_date, end_date, report_type)
                    target_stands_list.append(project_targets['stands_target'] or 0)
                    target_value_list.append(project_targets['sales_target'] or 0)
                
                project_data_with_targets['target_stands'] = target_stands_list
                project_data_with_targets['target_value'] = target_value_list
                
                # Table 1: Stands Sold vs Target
                story.append(Paragraph("Stands Sold vs Target by Project", subtitle_style))
                
                stands_table_data = [['Project Name', 'Stands Sold', 'Target Stands', 'Variance']]
                
                for _, row in project_data_with_targets.iterrows():
                    actual_stands = int(row['stands_sold']) if pd.notna(row['stands_sold']) else 0
                    target_stands = int(row['target_stands']) if pd.notna(row['target_stands']) else 0
                    stands_variance = actual_stands - target_stands
                    
                    # Format variance without colors
                    if stands_variance >= 0:
                        stands_variance_text = f"+{stands_variance:,}"
                    else:
                        stands_variance_text = f"-{abs(stands_variance):,}"
                    
                    stands_table_data.append([
                        str(row['project_name']) if pd.notna(row['project_name']) else 'Unknown Project',
                        str(actual_stands),
                        str(target_stands),
                        stands_variance_text
                    ])
                
                # Add totals row
                if len(project_data_with_targets) > 1:
                    total_actual_stands = project_data_with_targets['stands_sold'].sum()
                    total_target_stands = project_data_with_targets['target_stands'].sum()
                    total_stands_variance = total_actual_stands - total_target_stands
                    
                    # Format total variance without colors
                    if total_stands_variance >= 0:
                        total_stands_variance_text = f"+{total_stands_variance:,}"
                    else:
                        total_stands_variance_text = f"-{abs(total_stands_variance):,}"
                    
                    stands_table_data.append([
                        'TOTAL', 
                        str(int(total_actual_stands)),
                        str(int(total_target_stands)),
                        total_stands_variance_text
                    ])
                
                stands_table = Table(stands_table_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
                
                # Define base table styles
                stands_table_styles = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F3559")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -2), 9),
                ]

                # Conditionally add bold/colored footer only if multiple rows exist
                if len(project_data_with_targets) > 1:
                    stands_table_styles.extend([
                        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#e9ecef"))
                    ])

                stands_table.setStyle(TableStyle(stands_table_styles))
                
                story.append(stands_table)
                story.append(Spacer(1, 20))
                
                # Stands vs Target Bar Chart
                stands_chart_img = self.create_stands_vs_target_chart(project_data_with_targets, 
                                                                   f"Stands Sold vs Target ({report_type.title()})")
                if stands_chart_img:
                    story.append(Paragraph("Stands Sold vs Target Chart", subtitle_style))
                    story.append(Spacer(1, 12))
                    img_buffer = io.BytesIO(stands_chart_img.getvalue())
                    story.append(Image(img_buffer, width=7*inch, height=4*inch))
                    story.append(Spacer(1, 30))
                
                # Table 2: Sales Value vs Target
                story.append(Paragraph("Sales Value vs Target by Project", subtitle_style))
                
                value_table_data = [['Project Name', 'Actual Value ($)', 'Target Value ($)', 'Variance']]
                
                for _, row in project_data_with_targets.iterrows():
                    actual_value = row['stands_value'] if pd.notna(row['stands_value']) else 0
                    target_value = row['target_value'] if pd.notna(row['target_value']) else 0
                    value_variance = actual_value - target_value
                    
                    # Format variance without colors
                    if value_variance >= 0:
                        value_variance_text = f"+${value_variance:,.2f}"
                    else:
                        value_variance_text = f"-${abs(value_variance):,.2f}"
                    
                    value_table_data.append([
                        str(row['project_name']) if pd.notna(row['project_name']) else 'Unknown Project',
                        f"${actual_value:,.2f}",
                        f"${target_value:,.2f}",
                        value_variance_text
                    ])
                
                # Add totals row
                if len(project_data_with_targets) > 1:
                    total_actual_value = project_data_with_targets['stands_value'].sum()
                    total_target_value = project_data_with_targets['target_value'].sum()
                    total_value_variance = total_actual_value - total_target_value
                    
                    # Format total variance without colors
                    if total_value_variance >= 0:
                        total_value_variance_text = f"+${total_value_variance:,.2f}"
                    else:
                        total_value_variance_text = f"-${abs(total_value_variance):,.2f}"
                    
                    value_table_data.append([
                        'TOTAL', 
                        f"${total_actual_value:,.2f}",
                        f"${total_target_value:,.2f}",
                        total_value_variance_text
                    ])
                
                value_table = Table(value_table_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
                
                # Define base table styles
                value_table_styles = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F3559")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -2), 9),
                ]

                # Conditionally add bold/colored footer only if multiple rows exist
                if len(project_data_with_targets) > 1:
                    value_table_styles.extend([
                        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#e9ecef"))
                    ])

                value_table.setStyle(TableStyle(value_table_styles))
                
                story.append(value_table)
                story.append(Spacer(1, 20))
                
                # Value vs Target Bar Chart
                value_chart_img = self.create_value_vs_target_chart(project_data_with_targets, 
                                                                 f"Sales Value vs Target ({report_type.title()})")
                if value_chart_img:
                    story.append(Paragraph("Sales Value vs Target Chart", subtitle_style))
                    story.append(Spacer(1, 12))
                    img_buffer2 = io.BytesIO(value_chart_img.getvalue())
                    story.append(Image(img_buffer2, width=7*inch, height=4*inch))
                    story.append(Spacer(1, 30))
                
                # Table 3: Stands Status (Sold, Reserved, Available)
                story.append(Paragraph("Stand Status by Project", subtitle_style))
                
                status_table_data = [['Project Name', 'Stands Sold', 'Stands Reserved', 'Stands Available', 'Total Stands']]
                
                for _, row in project_data_with_targets.iterrows():
                    stands_sold = int(row['stands_sold']) if pd.notna(row['stands_sold']) else 0
                    stands_reserved = int(row['stands_reserved']) if pd.notna(row['stands_reserved']) else 0
                    stands_available = int(row['stands_available']) if pd.notna(row['stands_available']) else 0
                    total_stands = stands_sold + stands_reserved + stands_available
                    
                    status_table_data.append([
                        str(row['project_name']) if pd.notna(row['project_name']) else 'Unknown Project',
                        str(stands_sold),
                        str(stands_reserved),
                        str(stands_available),
                        str(total_stands)
                    ])
                
                # Add totals row
                if len(project_data_with_targets) > 1:
                    total_sold = project_data_with_targets['stands_sold'].sum()
                    total_reserved = project_data_with_targets['stands_reserved'].sum()
                    total_available = project_data_with_targets['stands_available'].sum()
                    total_all = total_sold + total_reserved + total_available
                    
                    status_table_data.append([
                        'TOTAL', 
                        str(int(total_sold)),
                        str(int(total_reserved)),
                        str(int(total_available)),
                        str(int(total_all))
                    ])
                
                status_table = Table(status_table_data, colWidths=[1.8*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.1*inch])
                
                # Define base table styles
                status_table_styles = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F3559")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -2), 9),
                ]

                # Conditionally add bold/colored footer only if multiple rows exist
                if len(project_data_with_targets) > 1:
                    status_table_styles.extend([
                        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#e9ecef"))
                    ])

                status_table.setStyle(TableStyle(status_table_styles))
                
                story.append(status_table)
                story.append(Spacer(1, 30))
            
            # Agent Sales table - Adjusted sizing to fit page
            if not data['agent_data'].empty:
                story.append(Paragraph("Agent Sales Performance", subtitle_style))
                
                # Pivot the data to show projects as columns
                # First, get all unique projects for the selected period
                all_projects = data['agent_data']['project_name'].unique()
                
                # Pivot the data
                pivot_df = data['agent_data'].pivot_table(
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
                agent_sales_totals = data['agent_data'].groupby('agent_name')['total_sales'].sum().reset_index()
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
                
                # Create table data for PDF with adjusted column widths
                table_data = [display_columns]
                for _, row in pivot_df_display.iterrows():
                    table_row = [str(row[col]) for col in display_columns]
                    table_data.append(table_row)
                
                # Calculate column widths dynamically based on number of projects
                num_projects = len(project_columns)
                if num_projects <= 3:
                    # Few projects - wider columns
                    agent_col_width = 1.2 * inch
                    project_col_width = 1.0 * inch
                    total_cols_width = 0.9 * inch
                elif num_projects <= 6:
                    # Medium number of projects
                    agent_col_width = 1.0 * inch
                    project_col_width = 0.7 * inch
                    total_cols_width = 0.8 * inch
                else:
                    # Many projects - narrower columns
                    agent_col_width = 0.9 * inch
                    project_col_width = 0.5 * inch
                    total_cols_width = 0.7 * inch
                
                # Create column widths array
                col_widths = [agent_col_width]  # Agent Name column
                col_widths.extend([project_col_width] * num_projects)  # Project columns
                col_widths.extend([total_cols_width, total_cols_width])  # Total Stands and Total Sales columns
                
                # Ensure we don't exceed page width (A4 width is ~8.5 inches)
                total_width = sum(col_widths)
                if total_width > 7.5 * inch:  # Leave some margin
                    # Scale down all columns proportionally
                    scale_factor = (7.5 * inch) / total_width
                    col_widths = [width * scale_factor for width in col_widths]
                
                # Create agent table with adjusted sizing
                agent_table = Table(table_data, colWidths=col_widths, repeatRows=1)
                agent_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F3559")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),  # Reduced font size for header
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 7),  # Reduced font size for data
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                    ('LEFTPADDING', (0, 0), (-1, -1), 3),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
                ]))
                
                story.append(agent_table)
                story.append(Spacer(1, 30))
            
            # Project comparison chart - MAIN CHART
            project_comparison_img = self.create_project_comparison_chart(data['project_data'], 
                                                                        f"Project Comparison - Stands Sold vs Sales Value ({report_type.title()})")
            if project_comparison_img:
                story.append(Paragraph("Project Sales Comparison", subtitle_style))
                story.append(Spacer(1, 12))
                
                # chart image
                img_buffer = io.BytesIO(project_comparison_img.getvalue())
                story.append(Image(img_buffer, width=7*inch, height=4*inch))
                story.append(Spacer(1, 30))
            
            # Agent sales chart
            if not data['agent_data'].empty:
                agent_chart_img = self.create_agent_sales_chart(data['agent_data'], 
                                                              f"Agent Sales Performance ({report_type.title()})")
                if agent_chart_img:
                    story.append(Paragraph("Agent Sales Performance Chart", subtitle_style))
                    story.append(Spacer(1, 12))
                    
                    # chart image
                    img_buffer3 = io.BytesIO(agent_chart_img.getvalue())
                    story.append(Image(img_buffer3, width=7*inch, height=4*inch))
                    story.append(PageBreak())
            
            # Build PDF
            try:
                doc.build(story)
            except Exception as e:
                print(f"Error building PDF: {e}")
                return None, f"Failed to build PDF: {str(e)}"
            
            # Store report info in connected database
            try:
                self.store_report_info_db(filename, start_date, end_date, report_type, summary_data)
                logger.info(f"Report {filename} has been saved in the database aibesanalytics_reports table")
            except Exception as e:
                print(f"Warning: Could not store report info in database: {e}")
            
            return filepath, None
        except Exception as e:
            print(f"Error generating PDF report: {e}")
            return None, f"Failed to generate report: {str(e)}"
    
    def store_report_info_db(self, filename, start_date, end_date, report_type, summary_data):
        """Store report information in the connected database"""
        try:
            if not self.db_connection_string:
                return
                
            engine = create_engine(self.db_connection_string)
            
            # Create table if not exists
            create_table_query = text("""
            CREATE TABLE IF NOT EXISTS aibesanalytics_reports (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                filename VARCHAR(255),
                start_date DATE,
                end_date DATE,
                report_type VARCHAR(50),
                generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_stand_value DECIMAL(15,2),
                total_stands_sold INTEGER,
                total_stands_available INTEGER,
                total_stands_reserved INTEGER,
                total_deposit DECIMAL(15,2),
                total_installment DECIMAL(15,2)
            )
            """)
            
            with engine.connect() as conn:
                trans = conn.begin()
                try:
                    conn.execute(create_table_query)
                    trans.commit()
                except Exception as e:
                    trans.rollback()
                    print(f"Warning: Could not create reports table: {e}")
            
            # Insert report info
            insert_query = text("""
            INSERT INTO aibesanalytics_reports 
            (filename, start_date, end_date, report_type, total_stand_value, total_stands_sold, 
             total_stands_available, total_stands_reserved, total_deposit, total_installment)
            VALUES (:filename, :start_date, :end_date, :report_type, :total_stand_value, :total_stands_sold, 
                    :total_stands_available, :total_stands_reserved, :total_deposit, :total_installment)
            """)
            
            with engine.connect() as conn:
                trans = conn.begin()
                try:
                    conn.execute(insert_query, {
                        'filename': filename,
                        'start_date': start_date.strftime('%Y-%m-%d'),
                        'end_date': end_date.strftime('%Y-%m-%d'),
                        'report_type': report_type,
                        'total_stand_value': float(summary_data['total_stand_value']) if summary_data['total_stand_value'] else 0,
                        'total_stands_sold': int(summary_data['total_stands_sold']) if summary_data['total_stands_sold'] else 0,
                        'total_stands_available': int(summary_data['total_stands_available']) if summary_data['total_stands_available'] else 0,
                        'total_stands_reserved': int(summary_data['total_stands_reserved']) if summary_data['total_stands_reserved'] else 0,
                        'total_deposit': float(summary_data['total_deposit']) if summary_data['total_deposit'] else 0,
                        'total_installment': float(summary_data['total_installment']) if summary_data['total_installment'] else 0
                    })
                    trans.commit()
                except Exception as e:
                    trans.rollback()
                    raise e
            
            engine.dispose()
        except Exception as e:
            print(f"Error storing report info in database: {e}")
            raise e
    
    def get_generated_reports(self):
        """Get list of generated reports from the connected database"""
        try:
            if not self.db_connection_string:
                return []
                
            engine = create_engine(self.db_connection_string)
            
            # First, ensure the table exists
            create_table_query = text("""
            CREATE TABLE IF NOT EXISTS aibesanalytics_reports (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                filename VARCHAR(255),
                start_date DATE,
                end_date DATE,
                report_type VARCHAR(50),
                generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_stand_value DECIMAL(15,2),
                total_stands_sold INTEGER,
                total_stands_available INTEGER,
                total_stands_reserved INTEGER,
                total_deposit DECIMAL(15,2),
                total_installment DECIMAL(15,2)
            )
            """)
            
            try:
                with engine.connect() as conn:
                    trans = conn.begin()
                    try:
                        conn.execute(create_table_query)
                        trans.commit()
                    except Exception as e:
                        trans.rollback()
                        print(f"Warning: Could not ensure reports table exists: {e}")
            except Exception as e:
                print(f"Warning: Could not connect to create reports table: {e}")
            
            # Query for reports
            query = text("""
            SELECT filename, start_date, end_date, report_type, generated_date, 
                   total_stand_value, total_stands_sold, total_stands_available, total_stands_reserved
            FROM aibesanalytics_reports
            ORDER BY generated_date DESC
            LIMIT 60
            """)
            
            result = pd.read_sql(query, engine)
            engine.dispose()
            
            if result.empty:
                return []
            
            reports = []
            for _, row in result.iterrows():
                # Handle timestamp conversion properly
                generated_date_str = str(row['generated_date'])
                if ' ' in generated_date_str:
                    generated_date_clean = generated_date_str.split()[0]
                else:
                    generated_date_clean = generated_date_str
                    
                reports.append({
                    'filename': row['filename'], 
                    'start_date': str(row['start_date']),
                    'end_date': str(row['end_date']),
                    'report_type': row['report_type'],
                    'date': generated_date_clean,
                    'total_stand_value': float(row['total_stand_value']) if not pd.isna(row['total_stand_value']) else 0,
                    'total_stands_sold': int(row['total_stands_sold']) if not pd.isna(row['total_stands_sold']) else 0,
                    'total_stands_available': int(row['total_stands_available']) if not pd.isna(row['total_stands_available']) else 0,
                    'total_stands_reserved': int(row['total_stands_reserved']) if not pd.isna(row['total_stands_reserved']) else 0
                })
            
            return reports
        except Exception as e:
            print(f"Error fetching reports: {e}")
            return []

# Global report generator instance
report_generator = None

def initialize_report_generator(db_connection_string):
    """Initialize the global report generator with user isolation"""
    global report_generator
    report_generator = ReportGenerator(db_connection_string)
    return report_generator

def get_report_generator():
    """Get the global report generator instance"""
    global report_generator
    return report_generator