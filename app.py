import os
import logging
from flask import Flask, render_template, redirect, url_for, flash
from database import db
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime, timedelta
import schedule
import threading
import time

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-for-tailoring-shop")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///tailoring.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Import models and blueprints
from models import Customer, Order, Payment, Measurement
from blueprints.customers import customers_bp
from blueprints.orders import orders_bp
from blueprints.reports import reports_bp
from blueprints.pending_orders import pending_orders_bp
from blueprints.settings import settings_bp
from utils import create_backup, ensure_backup_directory

# Register blueprints
app.register_blueprint(customers_bp, url_prefix='/customers')
app.register_blueprint(orders_bp, url_prefix='/orders')
app.register_blueprint(reports_bp, url_prefix='/reports')
app.register_blueprint(pending_orders_bp, url_prefix='/pending-orders')
app.register_blueprint(settings_bp, url_prefix='/settings')

# Create tables and start backup scheduler
with app.app_context():
    db.create_all()
    ensure_backup_directory()

# Schedule daily backups
def backup_scheduler():
    schedule.every().day.at("02:00").do(create_backup)
    while True:
        schedule.run_pending()
        time.sleep(3600)  # Check every hour

# Start backup scheduler in background thread
backup_thread = threading.Thread(target=backup_scheduler, daemon=True)
backup_thread.start()

@app.route('/')
def dashboard():
    """Dashboard with key metrics and recent activity"""
    # Get recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Get pending orders count
    pending_count = Order.query.filter(Order.status.in_(['pending', 'in_progress', 'stitched'])).count()
    
    # Get overdue orders (past delivery date and not delivered)
    today = datetime.now().date()
    overdue_orders = Order.query.filter(
        Order.delivery_date < today,
        Order.status != 'delivered'
    ).all()
    
    # Calculate monthly revenue
    current_month_start = datetime.now().replace(day=1)
    monthly_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
        Payment.created_at >= current_month_start
    ).scalar() or 0
    
    # Calculate total pending payments
    pending_payments = db.session.query(db.func.sum(Order.balance)).filter(
        Order.balance > 0
    ).scalar() or 0
    
    # Get total customers
    total_customers = Customer.query.count()
    
    return render_template('index.html',
                         recent_orders=recent_orders,
                         pending_count=pending_count,
                         overdue_orders=overdue_orders,
                         monthly_revenue=monthly_revenue,
                         pending_payments=pending_payments,
                         total_customers=total_customers,
                         current_time=datetime.now())

@app.route('/install')
def install():
    """Installation instructions for PWA"""
    return render_template('install.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
