import os
import shutil
import csv
from datetime import datetime, date
from flask import current_app
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from models import Customer, Order, Payment
from database import db
from sqlalchemy import func

# Dress types for measurements
DRESS_TYPES = [
    'saree_blouse',
    'salwar_kameez', 
    'lehenga_choli',
    'kurti',
    'gown',
    'churidar',
    'palazzo_set',
    'anarkali',
    'sharara',
    'ghagra',
    'dupatta_alteration',
    'other'
]

def ensure_backup_directory():
    """Ensure backup directory exists"""
    backup_dir = os.path.join(os.getcwd(), 'backups')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    return backup_dir

def create_backup():
    """Create daily backup of the database"""
    try:
        backup_dir = ensure_backup_directory()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'tailoring_backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Get database path
        db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # Copy database file
        shutil.copy2(db_path, backup_path)
        
        # Keep only last 30 backups
        cleanup_old_backups(backup_dir, days_to_keep=30)
        
        current_app.logger.info(f'Database backup created: {backup_filename}')
        return True
    except Exception as e:
        current_app.logger.error(f'Backup failed: {str(e)}')
        return False

def cleanup_old_backups(backup_dir, days_to_keep=30):
    """Remove backups older than specified days"""
    try:
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
        
        for filename in os.listdir(backup_dir):
            if filename.startswith('tailoring_backup_') and filename.endswith('.db'):
                file_path = os.path.join(backup_dir, filename)
                if os.path.getctime(file_path) < cutoff_time:
                    os.remove(file_path)
                    current_app.logger.info(f'Removed old backup: {filename}')
    except Exception as e:
        current_app.logger.error(f'Cleanup failed: {str(e)}')

def export_customers_csv():
    """Export all customers to CSV"""
    try:
        customers = Customer.query.all()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'customers_export_{timestamp}.csv'
        filepath = os.path.join('exports', filename)
        
        # Ensure exports directory exists
        os.makedirs('exports', exist_ok=True)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['ID', 'Name', 'Phone', 'Address', 'Total Orders', 'Created Date']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for customer in customers:
                writer.writerow({
                    'ID': customer.id,
                    'Name': customer.name,
                    'Phone': customer.phone,
                    'Address': customer.address or '',
                    'Total Orders': len(customer.orders),
                    'Created Date': customer.created_at.strftime('%Y-%m-%d')
                })
        
        return filepath
    except Exception as e:
        current_app.logger.error(f'Customer export failed: {str(e)}')
        return None

def export_orders_csv(start_date=None, end_date=None):
    """Export orders to CSV with optional date filtering"""
    try:
        query = Order.query
        
        if start_date and end_date:
            query = query.filter(Order.order_date.between(start_date, end_date))
        
        orders = query.all()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'orders_export_{timestamp}.csv'
        filepath = os.path.join('exports', filename)
        
        # Ensure exports directory exists
        os.makedirs('exports', exist_ok=True)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Order Number', 'Customer Name', 'Phone', 'Dress Type', 
                         'Order Date', 'Delivery Date', 'Cost', 'Advance', 'Balance', 'Status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for order in orders:
                writer.writerow({
                    'Order Number': order.order_number,
                    'Customer Name': order.customer.name,
                    'Phone': order.customer.phone,
                    'Dress Type': order.dress_type,
                    'Order Date': order.order_date.strftime('%Y-%m-%d'),
                    'Delivery Date': order.delivery_date.strftime('%Y-%m-%d'),
                    'Cost': order.stitching_cost,
                    'Advance': order.advance_paid,
                    'Balance': order.balance,
                    'Status': order.status.title()
                })
        
        return filepath
    except Exception as e:
        current_app.logger.error(f'Orders export failed: {str(e)}')
        return None

def generate_invoice_pdf(order):
    """Generate PDF invoice for an order"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'invoice_{order.order_number}_{timestamp}.pdf'
        filepath = os.path.join('invoices', filename)
        
        # Ensure invoices directory exists
        os.makedirs('invoices', exist_ok=True)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        elements.append(Paragraph("TAILORING INVOICE", title_style))
        elements.append(Spacer(1, 20))
        
        # Shop details (placeholder)
        shop_style = ParagraphStyle(
            'ShopStyle',
            parent=styles['Normal'],
            fontSize=12,
            alignment=1
        )
        elements.append(Paragraph("Your Tailoring Shop Name", shop_style))
        elements.append(Paragraph("Shop Address Line 1", shop_style))
        elements.append(Paragraph("Shop Address Line 2", shop_style))
        elements.append(Paragraph("Phone: +91-XXXXXXXXXX", shop_style))
        elements.append(Spacer(1, 30))
        
        # Invoice details
        invoice_data = [
            ['Invoice Number:', order.order_number],
            ['Customer Name:', order.customer.name],
            ['Phone Number:', order.customer.phone],
            ['Order Date:', order.order_date.strftime('%d/%m/%Y')],
            ['Delivery Date:', order.delivery_date.strftime('%d/%m/%Y')],
            ['Status:', order.status.title()]
        ]
        
        invoice_table = Table(invoice_data, colWidths=[2*inch, 3*inch])
        invoice_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(invoice_table)
        elements.append(Spacer(1, 30))
        
        # Order details
        order_data = [
            ['Description', 'Quantity', 'Rate', 'Amount'],
            [f'{order.dress_type} - {order.description or "Custom Stitching"}', 
             str(order.quantity), f'₹{order.stitching_cost}', f'₹{order.stitching_cost}']
        ]
        
        order_table = Table(order_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
        order_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(order_table)
        elements.append(Spacer(1, 20))
        
        # Payment summary
        payment_data = [
            ['Total Amount:', f'₹{order.stitching_cost}'],
            ['Advance Paid:', f'₹{order.advance_paid}'],
            ['Balance Due:', f'₹{order.balance}']
        ]
        
        payment_table = Table(payment_data, colWidths=[3*inch, 2*inch])
        payment_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, -1), (-1, -1), 2, colors.black),
        ]))
        elements.append(payment_table)
        
        # Footer
        elements.append(Spacer(1, 50))
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1
        )
        elements.append(Paragraph("Thank you for your business!", footer_style))
        
        doc.build(elements)
        return filepath
    except Exception as e:
        current_app.logger.error(f'Invoice generation failed: {str(e)}')
        return None

def send_whatsapp_message(phone_number, message):
    """Send WhatsApp message using Meta's WhatsApp Business API"""
    import os
    import requests
    import json
    
    try:
        # Get Meta WhatsApp credentials from environment variables
        access_token = os.environ.get('WHATSAPP_ACCESS_TOKEN')
        phone_number_id = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
        
        if not all([access_token, phone_number_id]):
            current_app.logger.warning('Meta WhatsApp API credentials not configured. Message not sent.')
            return False
        
        # Format phone number (remove + and any non-digits)
        formatted_phone = ''.join(filter(str.isdigit, phone_number))
        if not formatted_phone.startswith('91') and len(formatted_phone) == 10:
            # Assume Indian number if no country code
            formatted_phone = f'91{formatted_phone}'
        
        # Meta WhatsApp API endpoint
        url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": formatted_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message
            }
        }
        
        # Send WhatsApp message
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()
        
        if response.status_code == 200 and 'messages' in response_data:
            message_id = response_data['messages'][0]['id']
            current_app.logger.info(f'WhatsApp message sent to {formatted_phone}. Message ID: {message_id}')
            return True
        else:
            error_msg = response_data.get('error', {}).get('message', 'Unknown error')
            current_app.logger.error(f'Failed to send WhatsApp message: {error_msg}')
            return False
        
    except Exception as e:
        current_app.logger.error(f'Failed to send WhatsApp message to {phone_number}: {str(e)}')
        return False

def send_order_welcome_message(order):
    """Send welcome message when new order is created"""
    if not order.customer.phone:
        return
    
    message = f"""🙏 Thank you {order.customer.name}!

Your order has been received successfully.

📝 *Order Details:*
• Order ID: {order.order_number}
• Dress Type: {order.dress_type}
• Quantity: {order.quantity}
• Total Amount: ₹{order.stitching_cost}
• Advance Paid: ₹{order.advance_paid}
• Balance Due: ₹{order.balance}
• Expected Delivery: {order.delivery_date.strftime('%d/%m/%Y')}

We will keep you updated on your order progress. Thank you for choosing us! 🪡✨"""
    
    send_whatsapp_message(order.customer.phone, message)

def send_order_status_update(order, previous_status=None):
    """Send WhatsApp notification for order status changes"""
    if not order.customer.phone:
        return
    
    status_messages = {
        'pending': f"""📋 Hi {order.customer.name}!

Your order {order.order_number} has been received and is in our queue.

Expected delivery: {order.delivery_date.strftime('%d/%m/%Y')}
We'll notify you when work begins! 🪡""",

        'in_progress': f"""🪡 Good news {order.customer.name}!

Work has started on your order {order.order_number}.

Our skilled tailors are carefully crafting your {order.dress_type}.
Expected completion: {order.delivery_date.strftime('%d/%m/%Y')}

We'll update you once it's ready! ✨""",

        'stitched': f"""✅ Wonderful news {order.customer.name}!

Your order {order.order_number} is ready for pickup! 🎉

Please visit our shop at your convenience to collect your beautiful {order.dress_type}.

Balance due: ₹{order.balance}

Thank you for your patience! 💖""",

        'delivered': f"""🙏 Thank you {order.customer.name}!

Your order {order.order_number} has been successfully delivered.

We hope you absolutely love your new {order.dress_type}! 

Please share your feedback with us. We look forward to serving you again! ⭐✨"""
    }
    
    if order.status in status_messages:
        message = status_messages[order.status]
        send_whatsapp_message(order.customer.phone, message)

def send_order_reminder(order):
    """Send pickup reminder for stitched orders"""
    if not order.customer.phone or order.status != 'stitched':
        return
    
    days_ready = (date.today() - order.updated_at.date()).days
    
    message = f"""⏰ Gentle reminder {order.customer.name}!

Your order {order.order_number} has been ready for pickup for {days_ready} days.

Please collect your {order.dress_type} at your earliest convenience.
Balance due: ₹{order.balance}

We look forward to seeing you! 🪡💖"""
    
    send_whatsapp_message(order.customer.phone, message)

def send_overdue_reminders():
    """Send reminders for overdue orders"""
    from models import Order
    
    # Find orders that are overdue (delivery date passed but not delivered)
    overdue_orders = Order.query.filter(
        Order.delivery_date < date.today(),
        Order.status != 'delivered'
    ).all()
    
    for order in overdue_orders:
        days_overdue = (date.today() - order.delivery_date).days
        
        if order.status == 'stitched':
            # Send pickup reminder for ready orders
            message = f"""🔔 Urgent pickup reminder {order.customer.name}!

Your order {order.order_number} has been ready for {days_overdue} days past the delivery date.

Please collect your {order.dress_type} as soon as possible.
Balance due: ₹{order.balance}

We appreciate your prompt response! 🪡"""
            
        else:
            # Apologize for delay in stitching
            message = f"""🙏 Sincere apologies {order.customer.name}!

Your order {order.order_number} is running {days_overdue} days behind schedule.

We are working diligently to complete your {order.dress_type} and will update you shortly.

Thank you for your patience and understanding! 🪡✨"""
        
        send_whatsapp_message(order.customer.phone, message)

def send_daily_business_summary():
    """Send daily business summary to shop owner"""
    from models import Order, Customer, Payment
    
    today = date.today()
    
    # Today's statistics
    new_orders_today = Order.query.filter(Order.order_date == today).count()
    completed_today = Order.query.filter(
        Order.status == 'delivered',
        db.func.date(Order.updated_at) == today
    ).count()
    
    payments_today = db.session.query(db.func.sum(Payment.amount)).filter(
        db.func.date(Payment.created_at) == today
    ).scalar() or 0
    
    pending_orders = Order.query.filter(Order.status != 'delivered').count()
    overdue_orders = Order.query.filter(
        Order.delivery_date < today,
        Order.status != 'delivered'
    ).count()
    
    message = f"""📊 Daily Business Summary - {today.strftime('%d/%m/%Y')}

🆕 New Orders: {new_orders_today}
✅ Completed Orders: {completed_today}
💰 Payments Received: ₹{payments_today}
⏳ Pending Orders: {pending_orders}
⚠️ Overdue Orders: {overdue_orders}

{'🎉 Great day!' if new_orders_today > 0 or completed_today > 0 else '📈 Keep up the excellent work!'}"""
    
    # This would be sent to shop owner's number
    # shop_owner_number = os.environ.get('SHOP_OWNER_PHONE')
    # if shop_owner_number:
    #     send_whatsapp_message(shop_owner_number, message)
    
    current_app.logger.info(f"Daily summary generated: {message}")

def send_birthday_wishes():
    """Send birthday wishes to customers (if birth dates are stored)"""
    # This feature would require adding birth_date field to Customer model
    # Placeholder for future enhancement
    pass

def send_festival_greetings():
    """Send festival greetings to customers"""
    # This could be triggered manually for festivals
    from models import Customer
    
    customers = Customer.query.all()
    
    message = """🎉✨ Festival Greetings from [Shop Name]! ✨🎉

Wishing you and your family a very happy festival season!

May this festive time bring you joy, prosperity, and beautiful moments to cherish.

We're here to make your celebrations even more special with our latest collection! 🪡👗

Thank you for being a valued customer! 🙏"""
    
    for customer in customers:
        if customer.phone:
            send_whatsapp_message(customer.phone, message)

def get_customer_loyalty_stats(customer):
    """Get loyalty statistics for a customer"""
    from models import Order
    
    total_orders = Order.query.filter_by(customer_id=customer.id).count()
    total_spent = db.session.query(db.func.sum(Order.stitching_cost)).filter_by(customer_id=customer.id).scalar() or 0
    
    # Determine loyalty tier
    if total_orders >= 10:
        tier = "Gold Customer 🥇"
    elif total_orders >= 5:
        tier = "Silver Customer 🥈"
    elif total_orders >= 2:
        tier = "Bronze Customer 🥉"
    else:
        tier = "New Customer ⭐"
    
    return {
        'total_orders': total_orders,
        'total_spent': total_spent,
        'tier': tier
    }

def send_loyalty_appreciation(customer):
    """Send appreciation message to loyal customers"""
    stats = get_customer_loyalty_stats(customer)
    
    if stats['total_orders'] >= 5:
        message = f"""🏆 Dear {customer.name},

Thank you for being our {stats['tier']}!

You have placed {stats['total_orders']} orders with us and we truly appreciate your continued trust.

As a token of our appreciation, enjoy 5% off on your next order! 

We look forward to serving you again! 🪡✨"""
        
        send_whatsapp_message(customer.phone, message)

# Legacy functions for backward compatibility  
def send_sms_placeholder(phone_number, message):
    """Legacy function - redirects to WhatsApp"""
    send_whatsapp_message(phone_number, message)

def send_order_status_sms(order, previous_status=None):
    """Legacy function - redirects to WhatsApp"""
    send_order_status_update(order, previous_status)

# Common dress types for dropdowns
DRESS_TYPES = [
    'Saree Blouse',
    'Salwar Kameez',
    'Lehenga',
    'Kurti',
    'Gown',
    'Churidar',
    'Palazzo Set',
    'Anarkali',
    'Sharara',
    'Indo-Western',
    'Other'
]

# Order status options
ORDER_STATUSES = [
    ('pending', 'Order Placed'),
    ('in_progress', 'Stitching in Progress'),
    ('stitched', 'Stitched (Ready for Pickup)'),
    ('delivered', 'Delivered to Customer')
]

# Payment methods
PAYMENT_METHODS = [
    ('cash', 'Cash'),
    ('upi', 'UPI'),
    ('card', 'Card'),
    ('bank_transfer', 'Bank Transfer')
]
