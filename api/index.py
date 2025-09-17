from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import plotly.express as px
import plotly.graph_objs as go
import plotly.io as pio
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "defaultsecretkey")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "assetmanager1910@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "niwp phjx gjsj ohdc")

def send_email(receiver_email, asset_name, expiry_date):
    subject = f"Alert: {asset_name} is Expiring Soon"
    body = f"Dear User,\n\nYour asset '{asset_name}' is expiring on {expiry_date.date()}. Please take necessary action.\n\nBest Regards,\nIT Asset Management Team"
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file.filename != '':
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            
            # Read the CSV file
            df = pd.read_csv(file_path)
            df["Expiry Date"] = pd.to_datetime(df["Expiry Date"].str.split().str[0], errors='coerce')
            
            current_time = pd.Timestamp.now()
            expiring_assets = df[
                (df["Expiry Date"] <= (current_time + pd.Timedelta(days=30))) & 
                (df["Expiry Date"] > current_time)
            ]
            
            # Enhanced Expiry Distribution Plot
            fig = px.histogram(df, x="Expiry Date", 
                               title="Asset Expiry Distribution", 
                               color_discrete_sequence=['#2575fc'],
                               nbins=30)
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                hoverlabel=dict(bgcolor="white", font_size=12),
                font=dict(color="white")
            )

            graph_html = pio.to_html(fig, full_html=False)
            
            # Prepare additional context
            total_assets = len(df)
            
            # Count active assets (assuming 'Status' column exists)
            active_assets = len(df[df['Status'] == 'Active']) if 'Status' in df.columns else total_assets
            
            # Calculate total value (assuming 'Value' column exists)
            total_value = df['Value'].sum() if 'Value' in df.columns else 0
            
            return render_template('assets.html', 
                graph_html=graph_html, 
                expiring_assets=expiring_assets,
                total_assets=total_assets,
                active_assets=active_assets,
                total_value=total_value,
                current_time=current_time,
                filename=file.filename
            )
        
        flash("No file selected.", "warning")
    
    return render_template('upload.html')

@app.route('/assets/<filename>')
def view_assets(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = pd.read_csv(file_path)
    df["Expiry Date"] = pd.to_datetime(df["Expiry Date"].str.split().str[0], errors='coerce')
    
    current_time = pd.Timestamp.now()
    expiring_assets = df[
        (df["Expiry Date"] <= (current_time + pd.Timedelta(days=30))) & 
        (df["Expiry Date"] > current_time)
    ]
    
    # Enhanced Expiry Distribution Plot
    fig = px.histogram(df, x="Expiry Date", 
                       title="Asset Expiry Distribution", 
                       color_discrete_sequence=['#2575fc'],
                       nbins=30)
    fig.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    hoverlabel=dict(bgcolor="white", font_size=12),
    font=dict(color="white")  # Ensures all labels and text are white
 )

    graph_html = pio.to_html(fig, full_html=False)
    
    # Prepare additional context
    total_assets = len(df)
    
    # Count active assets (assuming 'Status' column exists)
    active_assets = len(df[df['Status'] == 'Active']) if 'Status' in df.columns else total_assets
    
    # Calculate total value (assuming 'Value' column exists)
    total_value = df['Value'].sum() if 'Value' in df.columns else 0
    
    return render_template('assets.html', 
        graph_html=graph_html, 
        expiring_assets=expiring_assets,
        total_assets=total_assets,
        active_assets=active_assets,
        total_value=total_value,
        current_time=current_time,
        filename=filename
    )

@app.route('/dashboard/<filename>')
def dashboard(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = pd.read_csv(file_path)
    df["Expiry Date"] = pd.to_datetime(df["Expiry Date"].str.split().str[0], errors='coerce')
    
    current_date = datetime.today()
    
    # Calculate insights
    total_assets = len(df)
    expiring_assets = df[df["Expiry Date"] <= (current_date + timedelta(days=30))]
    expiring_assets_count = len(expiring_assets)
    
    # Calculate average asset age (with fallback)
    try:
        df['Acquisition Date'] = pd.to_datetime(df['Acquisition Date'], errors='coerce')
        df['Asset Age'] = (current_date - df['Acquisition Date']).dt.days
        avg_asset_age = round(df['Asset Age'].mean(), 1)
    except Exception:
        avg_asset_age = 'N/A'
    
    # Plot 1: Asset Expiry Distribution with improved styling
    fig1 = px.histogram(df, x="Expiry Date", 
                        title="Asset Expiry Distribution",
                        color_discrete_sequence=['#4db8ff'])
    
    # Plot 2: Asset Category Distribution
    if "Category" in df.columns:
        category_counts = df["Category"].value_counts()
        fig2 = px.pie(names=category_counts.index, 
                      values=category_counts.values, 
                      title="Asset Category Distribution",
                      color_discrete_sequence=px.colors.sequential.Plasma_r)
        fig2.update_traces(textposition='inside', textinfo='percent+label')
    else:
        fig2 = go.Figure()
        fig2.add_annotation(text="No Category Data", x=0.5, y=0.5)
    
    # Plot 3: Asset Owner Distribution
    if "Owner Email" in df.columns:
        owner_counts = df["Owner Email"].value_counts()
        fig3 = px.bar(x=owner_counts.index, 
                      y=owner_counts.values, 
                      title="Assets per Owner",
                      color_discrete_sequence=['#4db8ff'])
    else:
        fig3 = go.Figure()
        fig3.add_annotation(text="No Owner Data", x=0.5, y=0.5)
    
    return render_template('dashboard.html', 
                           filename=filename,
                           graph1_html=fig1.to_json(), 
                           graph2_html=fig2.to_json(), 
                           graph3_html=fig3.to_json(),
                           total_assets=total_assets,
                           expiring_assets_count=expiring_assets_count,
                           avg_asset_age=avg_asset_age)

@app.route('/send_alerts/<filename>')
def send_alerts(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = pd.read_csv(file_path)
    df["Expiry Date"] = pd.to_datetime(df["Expiry Date"].str.split().str[0], errors='coerce')
    
    current_date = datetime.today()
    expiring_assets = df[df["Expiry Date"] <= (current_date + timedelta(days=30))]
    
    # Track email sending success
    successful_emails = 0
    failed_emails = 0
    
    for _, row in expiring_assets.iterrows():
        if send_email(row["Owner Email"], row["Asset"], row["Expiry Date"]):
            successful_emails += 1
        else:
            failed_emails += 1
    
    # Provide more detailed flash message
    if successful_emails > 0:
        flash(f"Sent {successful_emails} alert emails successfully!", "success")
    if failed_emails > 0:
        flash(f"{failed_emails} emails failed to send.", "warning")
    
    return redirect(url_for('view_assets', filename=filename))

if __name__ == '__main__':
    app.run(debug=True,port='5004')