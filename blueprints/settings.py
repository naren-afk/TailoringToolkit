from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import Customer, Order
from database import db
from utils import (send_whatsapp_message, send_overdue_reminders, 
                   send_festival_greetings, send_daily_business_summary,
                   get_customer_loyalty_stats, send_loyalty_appreciation)
import os
from datetime import date, timedelta

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/')
def index():
    """Settings dashboard"""
    # Check if Meta WhatsApp API credentials are configured
    whatsapp_configured = all([
        os.environ.get('WHATSAPP_ACCESS_TOKEN'),
        os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
    ])
    
    # Get some statistics
    total_customers = Customer.query.count()
    total_orders = Order.query.count()
    overdue_orders = Order.query.filter(
        Order.delivery_date < date.today(),
        Order.status != 'delivered'
    ).count()
    
    return render_template('settings/index.html',
                         whatsapp_configured=whatsapp_configured,
                         total_customers=total_customers,
                         total_orders=total_orders,
                         overdue_orders=overdue_orders)

@settings_bp.route('/messaging')
def messaging():
    """Messaging settings and controls"""
    # Check if Meta WhatsApp API credentials are configured
    whatsapp_configured = all([
        os.environ.get('WHATSAPP_ACCESS_TOKEN'),
        os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
    ])
    
    # Get overdue orders count
    overdue_orders = Order.query.filter(
        Order.delivery_date < date.today(),
        Order.status != 'delivered'
    ).count()
    
    # Get stitched orders count (ready for pickup)
    stitched_orders = Order.query.filter(Order.status == 'stitched').count()
    
    return render_template('settings/messaging.html',
                         whatsapp_configured=whatsapp_configured,
                         overdue_orders=overdue_orders,
                         stitched_orders=stitched_orders)

@settings_bp.route('/send-overdue-reminders', methods=['POST'])
def send_overdue_reminders_action():
    """Send reminders for all overdue orders"""
    try:
        send_overdue_reminders()
        flash('Overdue reminders sent successfully!', 'success')
    except Exception as e:
        flash(f'Error sending reminders: {str(e)}', 'error')
    
    return redirect(url_for('settings.messaging'))

@settings_bp.route('/send-festival-greetings', methods=['POST'])
def send_festival_greetings_action():
    """Send festival greetings to all customers"""
    try:
        send_festival_greetings()
        flash('Festival greetings sent to all customers!', 'success')
    except Exception as e:
        flash(f'Error sending greetings: {str(e)}', 'error')
    
    return redirect(url_for('settings.messaging'))

@settings_bp.route('/send-daily-summary', methods=['POST'])
def send_daily_summary_action():
    """Generate and send daily business summary"""
    try:
        send_daily_business_summary()
        flash('Daily business summary generated successfully!', 'success')
    except Exception as e:
        flash(f'Error generating summary: {str(e)}', 'error')
    
    return redirect(url_for('settings.messaging'))

@settings_bp.route('/test-message', methods=['POST'])
def test_message():
    """Send a test WhatsApp message"""
    phone_number = request.form.get('phone_number')
    message = request.form.get('message')
    
    if not phone_number or not message:
        flash('Phone number and message are required.', 'error')
        return redirect(url_for('settings.messaging'))
    
    try:
        success = send_whatsapp_message(phone_number, message)
        if success:
            flash('Test message sent successfully!', 'success')
        else:
            flash('Failed to send test message. Please check your Twilio configuration.', 'error')
    except Exception as e:
        flash(f'Error sending test message: {str(e)}', 'error')
    
    return redirect(url_for('settings.messaging'))

@settings_bp.route('/customer-loyalty')
def customer_loyalty():
    """View customer loyalty statistics"""
    customers = Customer.query.all()
    
    # Get loyalty stats for each customer
    customer_stats = []
    for customer in customers:
        stats = get_customer_loyalty_stats(customer)
        customer_stats.append({
            'customer': customer,
            'stats': stats
        })
    
    # Sort by total orders descending
    customer_stats.sort(key=lambda x: x['stats']['total_orders'], reverse=True)
    
    return render_template('settings/customer_loyalty.html', customer_stats=customer_stats)

@settings_bp.route('/send-loyalty-message/<int:customer_id>', methods=['POST'])
def send_loyalty_message(customer_id):
    """Send loyalty appreciation message to a specific customer"""
    customer = Customer.query.get_or_404(customer_id)
    
    try:
        send_loyalty_appreciation(customer)
        flash(f'Loyalty appreciation message sent to {customer.name}!', 'success')
    except Exception as e:
        flash(f'Error sending loyalty message: {str(e)}', 'error')
    
    return redirect(url_for('settings.customer_loyalty'))

@settings_bp.route('/backup-settings')
def backup_settings():
    """Backup and data management settings"""
    from utils import ensure_backup_directory
    import glob
    
    backup_dir = ensure_backup_directory()
    
    # Get list of backup files
    backup_files = glob.glob(os.path.join(backup_dir, 'tailoring_backup_*.db'))
    backup_files.sort(reverse=True)  # Most recent first
    
    # Get file info
    backup_info = []
    for filepath in backup_files[:10]:  # Show only last 10 backups
        filename = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)
        file_date = os.path.getmtime(filepath)
        
        backup_info.append({
            'filename': filename,
            'size': file_size,
            'date': file_date
        })
    
    return render_template('settings/backup.html', backup_info=backup_info)

@settings_bp.route('/create-backup', methods=['POST'])
def create_backup_action():
    """Create a manual backup"""
    try:
        from utils import create_backup
        success = create_backup()
        if success:
            flash('Backup created successfully!', 'success')
        else:
            flash('Backup creation failed. Please check the logs.', 'error')
    except Exception as e:
        flash(f'Error creating backup: {str(e)}', 'error')
    
    return redirect(url_for('settings.backup_settings'))

@settings_bp.route('/bulk-message')
def bulk_message():
    """Send bulk messages to customers"""
    customers = Customer.query.all()
    return render_template('settings/bulk_message.html', customers=customers)

@settings_bp.route('/send-bulk-message', methods=['POST'])
def send_bulk_message_action():
    """Send bulk message to selected customers"""
    message = request.form.get('message')
    customer_ids = request.form.getlist('customer_ids')
    
    if not message or not customer_ids:
        flash('Message and at least one customer must be selected.', 'error')
        return redirect(url_for('settings.bulk_message'))
    
    try:
        sent_count = 0
        for customer_id in customer_ids:
            customer = Customer.query.get(customer_id)
            if customer and customer.phone:
                success = send_whatsapp_message(customer.phone, message)
                if success:
                    sent_count += 1
        
        flash(f'Bulk message sent to {sent_count} customers successfully!', 'success')
    except Exception as e:
        flash(f'Error sending bulk message: {str(e)}', 'error')
    
    return redirect(url_for('settings.bulk_message'))