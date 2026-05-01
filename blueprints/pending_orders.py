from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Order, Customer
from database import db
from datetime import datetime, date, timedelta
from sqlalchemy import func

pending_orders_bp = Blueprint('pending_orders', __name__)

@pending_orders_bp.route('/')
def index():
    """Enhanced pending orders dashboard with sorting and filtering"""
    
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    sort_by = request.args.get('sort', 'delivery_date')
    sort_order = request.args.get('order', 'asc')
    customer_filter = request.args.get('customer', '')
    
    # Base query for non-delivered orders
    query = Order.query.filter(Order.status != 'delivered')
    
    # Apply status filter
    if status_filter == 'pending':
        query = query.filter(Order.status == 'pending')
    elif status_filter == 'in_progress':
        query = query.filter(Order.status == 'in_progress')
    elif status_filter == 'stitched':
        query = query.filter(Order.status == 'stitched')
    elif status_filter == 'overdue':
        today = date.today()
        query = query.filter(Order.delivery_date < today)
    
    # Apply customer filter
    if customer_filter:
        query = query.join(Customer).filter(
            db.or_(
                Customer.name.contains(customer_filter),
                Customer.phone.contains(customer_filter)
            )
        )
    
    # Apply sorting
    if sort_by == 'delivery_date':
        if sort_order == 'desc':
            query = query.order_by(Order.delivery_date.desc())
        else:
            query = query.order_by(Order.delivery_date.asc())
    elif sort_by == 'order_date':
        if sort_order == 'desc':
            query = query.order_by(Order.order_date.desc())
        else:
            query = query.order_by(Order.order_date.asc())
    elif sort_by == 'customer':
        query = query.join(Customer)
        if sort_order == 'desc':
            query = query.order_by(Customer.name.desc())
        else:
            query = query.order_by(Customer.name.asc())
    elif sort_by == 'status':
        if sort_order == 'desc':
            query = query.order_by(Order.status.desc())
        else:
            query = query.order_by(Order.status.asc())
    elif sort_by == 'balance':
        if sort_order == 'desc':
            query = query.order_by(Order.balance.desc())
        else:
            query = query.order_by(Order.balance.asc())
    
    # Get paginated results
    page = request.args.get('page', 1, type=int)
    per_page = 25
    orders = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Calculate summary statistics
    today = date.today()
    
    # Count by status
    status_counts = {
        'total': Order.query.filter(Order.status != 'delivered').count(),
        'pending': Order.query.filter(Order.status == 'pending').count(),
        'in_progress': Order.query.filter(Order.status == 'in_progress').count(),
        'stitched': Order.query.filter(Order.status == 'stitched').count(),
        'overdue': Order.query.filter(
            Order.delivery_date < today,
            Order.status != 'delivered'
        ).count()
    }
    
    # Calculate overdue orders by urgency
    overdue_orders = Order.query.filter(
        Order.delivery_date < today,
        Order.status != 'delivered'
    ).order_by(Order.delivery_date.asc()).all()
    
    # Categorize overdue orders
    overdue_critical = []  # > 7 days overdue
    overdue_urgent = []    # 3-7 days overdue
    overdue_recent = []    # 1-2 days overdue
    
    for order in overdue_orders:
        days_overdue = (today - order.delivery_date).days
        if days_overdue > 7:
            overdue_critical.append(order)
        elif days_overdue >= 3:
            overdue_urgent.append(order)
        else:
            overdue_recent.append(order)
    
    # Calculate financial summary
    total_pending_amount = db.session.query(func.sum(Order.balance)).filter(
        Order.status != 'delivered',
        Order.balance > 0
    ).scalar() or 0
    
    # Get orders due this week
    week_end = today.replace(day=today.day + 7) if today.day <= 24 else today.replace(month=today.month + 1, day=today.day + 7 - 31)
    due_this_week = Order.query.filter(
        Order.delivery_date.between(today, week_end),
        Order.status != 'delivered'
    ).count()
    
    return render_template('pending_orders/index.html',
                         orders=orders,
                         status_counts=status_counts,
                         overdue_critical=overdue_critical,
                         overdue_urgent=overdue_urgent,
                         overdue_recent=overdue_recent,
                         total_pending_amount=total_pending_amount,
                         due_this_week=due_this_week,
                         current_filters={
                             'status': status_filter,
                             'sort': sort_by,
                             'order': sort_order,
                             'customer': customer_filter
                         },
                         today=today)

@pending_orders_bp.route('/bulk-update', methods=['POST'])
def bulk_update():
    """Bulk update status for multiple orders"""
    try:
        order_ids = request.form.getlist('order_ids')
        new_status = request.form.get('new_status')
        
        if not order_ids:
            flash('No orders selected for update.', 'error')
            return redirect(url_for('pending_orders.index'))
        
        if new_status not in ['pending', 'in_progress', 'stitched', 'delivered']:
            flash('Invalid status selected.', 'error')
            return redirect(url_for('pending_orders.index'))
        
        # Update selected orders
        updated_count = 0
        for order_id in order_ids:
            order = Order.query.get(order_id)
            if order and order.status != 'delivered':
                previous_status = order.status
                order.status = new_status
                updated_count += 1
                
                # Send SMS notification for status change
                from utils import send_order_status_sms
                if previous_status != new_status:
                    send_order_status_sms(order, previous_status)
        
        db.session.commit()
        flash(f'Successfully updated {updated_count} orders to {new_status.title()}.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating orders: {str(e)}', 'error')
    
    return redirect(url_for('pending_orders.index'))

@pending_orders_bp.route('/mark-priority/<int:id>', methods=['POST'])
def mark_priority(id):
    """Mark order as priority (placeholder for future priority feature)"""
    order = Order.query.get_or_404(id)
    
    # This is a placeholder for future priority functionality
    # For now, we'll just add a note
    try:
        if not order.description:
            order.description = "⭐ PRIORITY ORDER"
        elif "⭐ PRIORITY" not in order.description:
            order.description = f"⭐ PRIORITY - {order.description}"
        
        db.session.commit()
        flash(f'Order {order.order_number} marked as priority!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error marking priority: {str(e)}', 'error')
    
    return redirect(url_for('pending_orders.index'))

@pending_orders_bp.route('/quick-actions/<int:id>', methods=['POST'])
def quick_actions(id):
    """Quick actions for pending orders"""
    order = Order.query.get_or_404(id)
    action = request.form.get('action')
    
    try:
        previous_status = order.status
        
        if action == 'start_work':
            order.status = 'in_progress'
            message = f'Work started on order {order.order_number}!'
        elif action == 'mark_stitched':
            order.status = 'stitched'
            message = f'Order {order.order_number} marked as stitched!'
        elif action == 'mark_delivered':
            order.status = 'delivered'
            message = f'Order {order.order_number} marked as delivered!'
        elif action == 'extend_delivery':
            # Add 2 days to delivery date
            from datetime import timedelta
            order.delivery_date = order.delivery_date + timedelta(days=2)
            message = f'Delivery date extended for order {order.order_number}!'
        else:
            flash('Invalid action selected.', 'error')
            return redirect(url_for('pending_orders.index'))
        
        db.session.commit()
        
        # Send SMS notification if status changed
        if action in ['start_work', 'mark_stitched', 'mark_delivered']:
            from utils import send_order_status_sms
            send_order_status_sms(order, previous_status)
        
        flash(message, 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error performing action: {str(e)}', 'error')
    
    return redirect(url_for('pending_orders.index'))

@pending_orders_bp.route('/delivery-calendar')
def delivery_calendar():
    """Calendar view of delivery dates"""
    from datetime import timedelta
    
    # Get date range (current month)
    today = date.today()
    start_date = today.replace(day=1)
    
    # Calculate next month start
    if today.month == 12:
        end_date = today.replace(year=today.year + 1, month=1, day=1)
    else:
        end_date = today.replace(month=today.month + 1, day=1)
    
    # Get orders for the date range
    orders = Order.query.filter(
        Order.delivery_date.between(start_date, end_date),
        Order.status != 'delivered'
    ).order_by(Order.delivery_date.asc()).all()
    
    # Group orders by date
    orders_by_date = {}
    for order in orders:
        date_key = order.delivery_date.strftime('%Y-%m-%d')
        if date_key not in orders_by_date:
            orders_by_date[date_key] = []
        orders_by_date[date_key].append(order)
    
    return render_template('pending_orders/calendar.html',
                         orders_by_date=orders_by_date,
                         start_date=start_date,
                         end_date=end_date,
                         today=today)
