from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from models import Customer, Order, Payment
from database import db
from utils import export_customers_csv, export_orders_csv
from datetime import datetime, date, timedelta
from sqlalchemy import func, extract
import tempfile
import os

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
def index():
    """Reports dashboard with various report options"""
    
    # Get date range from request
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    report_type = request.args.get('report_type', 'summary')
    
    # Set default date range (current month)
    if not start_date or not end_date:
        today = date.today()
        start_date = today.replace(day=1).strftime('%Y-%m-%d')
        # Last day of month
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        end_date = end_date.strftime('%Y-%m-%d')
    
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD format.', 'error')
        return render_template('reports/index.html')
    
    # Generate report data based on type
    if report_type == 'summary':
        report_data = generate_summary_report(start_date_obj, end_date_obj)
    elif report_type == 'orders':
        report_data = generate_orders_report(start_date_obj, end_date_obj)
    elif report_type == 'payments':
        report_data = generate_payments_report(start_date_obj, end_date_obj)
    elif report_type == 'customers':
        report_data = generate_customers_report(start_date_obj, end_date_obj)
    else:
        report_data = generate_summary_report(start_date_obj, end_date_obj)
    
    return render_template('reports/index.html',
                         report_data=report_data,
                         report_type=report_type,
                         start_date=start_date,
                         end_date=end_date)

def generate_summary_report(start_date, end_date):
    """Generate summary report with key metrics"""
    
    # Total orders in period
    total_orders = Order.query.filter(
        Order.order_date.between(start_date, end_date)
    ).count()
    
    # Orders by status
    orders_by_status = db.session.query(
        Order.status,
        func.count(Order.id).label('count')
    ).filter(
        Order.order_date.between(start_date, end_date)
    ).group_by(Order.status).all()
    
    # Revenue calculation
    total_revenue = db.session.query(
        func.sum(Order.stitching_cost)
    ).filter(
        Order.order_date.between(start_date, end_date)
    ).scalar() or 0
    
    # Payments received in period
    payments_received = db.session.query(
        func.sum(Payment.amount)
    ).join(Order).filter(
        Payment.created_at.between(
            datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.max.time())
        )
    ).scalar() or 0
    
    # Add advance payments from orders
    advance_payments = db.session.query(
        func.sum(Order.advance_paid)
    ).filter(
        Order.order_date.between(start_date, end_date)
    ).scalar() or 0
    
    total_payments = payments_received + advance_payments
    
    # Pending payments
    pending_payments = db.session.query(
        func.sum(Order.balance)
    ).filter(
        Order.order_date.between(start_date, end_date),
        Order.balance > 0
    ).scalar() or 0
    
    # Top customers by order count
    top_customers = db.session.query(
        Customer.name,
        Customer.phone,
        func.count(Order.id).label('order_count'),
        func.sum(Order.stitching_cost).label('total_value')
    ).join(Order).filter(
        Order.order_date.between(start_date, end_date)
    ).group_by(Customer.id).order_by(func.count(Order.id).desc()).limit(10).all()
    
    # Popular dress types
    popular_dress_types = db.session.query(
        Order.dress_type,
        func.count(Order.id).label('count')
    ).filter(
        Order.order_date.between(start_date, end_date)
    ).group_by(Order.dress_type).order_by(func.count(Order.id).desc()).limit(10).all()
    
    # Daily order trends
    daily_orders = db.session.query(
        Order.order_date,
        func.count(Order.id).label('order_count'),
        func.sum(Order.stitching_cost).label('revenue')
    ).filter(
        Order.order_date.between(start_date, end_date)
    ).group_by(Order.order_date).order_by(Order.order_date).all()
    
    return {
        'type': 'summary',
        'period': {'start': start_date, 'end': end_date},
        'totals': {
            'orders': total_orders,
            'revenue': total_revenue,
            'payments_received': total_payments,
            'pending_payments': pending_payments
        },
        'orders_by_status': orders_by_status,
        'top_customers': top_customers,
        'popular_dress_types': popular_dress_types,
        'daily_trends': daily_orders
    }

def generate_orders_report(start_date, end_date):
    """Generate detailed orders report"""
    
    orders = Order.query.filter(
        Order.order_date.between(start_date, end_date)
    ).order_by(Order.order_date.desc()).all()
    
    # Summary statistics
    total_orders = len(orders)
    total_value = sum(order.stitching_cost for order in orders)
    total_advance = sum(order.advance_paid for order in orders)
    total_balance = sum(order.balance for order in orders)
    
    return {
        'type': 'orders',
        'period': {'start': start_date, 'end': end_date},
        'orders': orders,
        'summary': {
            'total_orders': total_orders,
            'total_value': total_value,
            'total_advance': total_advance,
            'total_balance': total_balance
        }
    }

def generate_payments_report(start_date, end_date):
    """Generate payments report"""
    
    # Get all payments in the period
    payments = db.session.query(
        Payment, Order, Customer
    ).join(Order).join(Customer).filter(
        Payment.created_at.between(
            datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.max.time())
        )
    ).order_by(Payment.created_at.desc()).all()
    
    # Get advance payments from orders
    advance_payments = db.session.query(
        Order, Customer
    ).join(Customer).filter(
        Order.order_date.between(start_date, end_date),
        Order.advance_paid > 0
    ).all()
    
    # Payment method breakdown
    payment_methods = db.session.query(
        Payment.payment_method,
        func.count(Payment.id).label('count'),
        func.sum(Payment.amount).label('total')
    ).filter(
        Payment.created_at.between(
            datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.max.time())
        )
    ).group_by(Payment.payment_method).all()
    
    # Calculate totals
    total_payments = sum(p[0].amount for p in payments)
    total_advance = sum(o.advance_paid for o, c in advance_payments)
    
    return {
        'type': 'payments',
        'period': {'start': start_date, 'end': end_date},
        'payments': payments,
        'advance_payments': advance_payments,
        'payment_methods': payment_methods,
        'totals': {
            'payments': total_payments,
            'advance': total_advance,
            'total': total_payments + total_advance
        }
    }

def generate_customers_report(start_date, end_date):
    """Generate customers report"""
    
    # Get customers with orders in the period
    customers_with_orders = db.session.query(
        Customer,
        func.count(Order.id).label('order_count'),
        func.sum(Order.stitching_cost).label('total_value'),
        func.sum(Order.balance).label('pending_balance'),
        func.max(Order.order_date).label('last_order_date')
    ).outerjoin(Order).filter(
        db.or_(
            Order.order_date.between(start_date, end_date),
            Order.order_date.is_(None)
        )
    ).group_by(Customer.id).having(
        func.count(Order.id) > 0
    ).order_by(func.sum(Order.stitching_cost).desc()).all()
    
    # New customers in period
    new_customers = Customer.query.filter(
        Customer.created_at.between(
            datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.max.time())
        )
    ).all()
    
    return {
        'type': 'customers',
        'period': {'start': start_date, 'end': end_date},
        'customers_with_orders': customers_with_orders,
        'new_customers': new_customers,
        'summary': {
            'active_customers': len(customers_with_orders),
            'new_customers': len(new_customers)
        }
    }

@reports_bp.route('/export/customers')
def export_customers():
    """Export customers data to CSV"""
    try:
        filepath = export_customers_csv()
        if filepath:
            return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))
        else:
            flash('Error generating customers export.', 'error')
            return redirect(url_for('reports.index'))
    except Exception as e:
        flash(f'Error exporting customers: {str(e)}', 'error')
        return redirect(url_for('reports.index'))

@reports_bp.route('/export/orders')
def export_orders():
    """Export orders data to CSV"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        
        filepath = export_orders_csv(start_date_obj, end_date_obj)
        if filepath:
            return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))
        else:
            flash('Error generating orders export.', 'error')
            return redirect(url_for('reports.index'))
    except Exception as e:
        flash(f'Error exporting orders: {str(e)}', 'error')
        return redirect(url_for('reports.index'))

@reports_bp.route('/api/chart-data')
def chart_data():
    """API endpoint for chart data"""
    chart_type = request.args.get('type', 'daily_revenue')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid date format'}), 400
    
    if chart_type == 'daily_revenue':
        data = db.session.query(
            Order.order_date,
            func.sum(Order.stitching_cost).label('revenue')
        ).filter(
            Order.order_date.between(start_date_obj, end_date_obj)
        ).group_by(Order.order_date).order_by(Order.order_date).all()
        
        return jsonify({
            'labels': [d.order_date.strftime('%Y-%m-%d') for d, r in data],
            'values': [float(r) for d, r in data]
        })
    
    elif chart_type == 'status_distribution':
        data = db.session.query(
            Order.status,
            func.count(Order.id).label('count')
        ).filter(
            Order.order_date.between(start_date_obj, end_date_obj)
        ).group_by(Order.status).all()
        
        return jsonify({
            'labels': [status.title() for status, count in data],
            'values': [int(count) for status, count in data]
        })
    
    elif chart_type == 'dress_types':
        data = db.session.query(
            Order.dress_type,
            func.count(Order.id).label('count')
        ).filter(
            Order.order_date.between(start_date_obj, end_date_obj)
        ).group_by(Order.dress_type).order_by(func.count(Order.id).desc()).limit(10).all()
        
        return jsonify({
            'labels': [dress_type for dress_type, count in data],
            'values': [int(count) for dress_type, count in data]
        })
    
    return jsonify({'error': 'Invalid chart type'}), 400

@reports_bp.route('/quick-reports')
def quick_reports():
    """Quick report buttons for common periods"""
    report_period = request.args.get('period', 'today')
    
    today = date.today()
    
    if report_period == 'today':
        start_date = end_date = today
    elif report_period == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif report_period == 'month':
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    elif report_period == 'quarter':
        quarter = (today.month - 1) // 3
        start_date = today.replace(month=quarter * 3 + 1, day=1)
        end_date = today.replace(month=(quarter + 1) * 3, day=1) - timedelta(days=1)
    else:
        start_date = end_date = today
    
    return redirect(url_for('reports.index', 
                          start_date=start_date.strftime('%Y-%m-%d'),
                          end_date=end_date.strftime('%Y-%m-%d'),
                          report_type='summary'))
