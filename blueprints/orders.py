from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from models import Customer, Order, Payment, Measurement
from database import db
from utils import DRESS_TYPES, ORDER_STATUSES, PAYMENT_METHODS, generate_invoice_pdf, send_order_status_sms
from datetime import datetime, date

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/')
def index():
    """List all orders with filtering and pagination"""
    # Get filter parameters
    status = request.args.get('status', '')
    customer_id = request.args.get('customer_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Build query
    query = Order.query
    
    if status:
        query = query.filter(Order.status == status)
    
    if customer_id:
        query = query.filter(Order.customer_id == customer_id)
    
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Order.order_date >= start_date_obj)
        except ValueError:
            flash('Invalid start date format.', 'error')
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Order.order_date <= end_date_obj)
        except ValueError:
            flash('Invalid end date format.', 'error')
    
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get customers for filter dropdown
    customers = Customer.query.order_by(Customer.name).all()
    
    return render_template('orders/index.html', 
                         orders=orders, 
                         customers=customers,
                         order_statuses=ORDER_STATUSES,
                         current_filters={
                             'status': status,
                             'customer_id': customer_id,
                             'start_date': start_date,
                             'end_date': end_date
                         })

@orders_bp.route('/add', methods=['GET', 'POST'])
def add():
    """Add new order"""
    if request.method == 'POST':
        try:
            # Get customer
            customer_id = request.form.get('customer_id', type=int)
            if not customer_id:
                flash('Please select a customer.', 'error')
                return render_template('orders/add.html', 
                                     customers=Customer.query.order_by(Customer.name).all(),
                                     dress_types=DRESS_TYPES)
            
            customer = Customer.query.get(customer_id)
            if not customer:
                flash('Selected customer not found.', 'error')
                return render_template('orders/add.html', 
                                     customers=Customer.query.order_by(Customer.name).all(),
                                     dress_types=DRESS_TYPES)
            
            # Parse dates
            order_date = datetime.strptime(request.form['order_date'], '%Y-%m-%d').date()
            delivery_date = datetime.strptime(request.form['delivery_date'], '%Y-%m-%d').date()
            
            # Validate delivery date
            if delivery_date <= order_date:
                flash('Delivery date must be after order date.', 'error')
                return render_template('orders/add.html', 
                                     customers=Customer.query.order_by(Customer.name).all(),
                                     dress_types=DRESS_TYPES)
            
            # Parse monetary values
            stitching_cost = float(request.form['stitching_cost'])
            advance_paid = float(request.form.get('advance_paid', 0))
            
            if advance_paid > stitching_cost:
                flash('Advance payment cannot be greater than stitching cost.', 'error')
                return render_template('orders/add.html', 
                                     customers=Customer.query.order_by(Customer.name).all(),
                                     dress_types=DRESS_TYPES)
            
            # Create order
            order = Order(
                customer_id=customer_id,
                dress_type=request.form['dress_type'],
                description=request.form.get('description', '').strip(),
                quantity=int(request.form.get('quantity', 1)),
                order_date=order_date,
                delivery_date=delivery_date,
                stitching_cost=stitching_cost,
                advance_paid=advance_paid,
                status=request.form.get('status', 'pending')
            )
            
            db.session.add(order)
            db.session.commit()
            
            # Send welcome WhatsApp message
            from utils import send_order_welcome_message
            send_order_welcome_message(order)
            
            flash(f'Order {order.order_number} created successfully!', 'success')
            return redirect(url_for('orders.view', id=order.id))
            
        except ValueError as e:
            flash('Invalid input values. Please check your entries.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating order: {str(e)}', 'error')
    
    customers = Customer.query.order_by(Customer.name).all()
    return render_template('orders/add.html', 
                         customers=customers, 
                         dress_types=DRESS_TYPES,
                         order_statuses=ORDER_STATUSES,
                         today=date.today())

@orders_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    """Edit order details"""
    order = Order.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            previous_status = order.status
            
            # Update order details
            order.dress_type = request.form['dress_type']
            order.description = request.form.get('description', '').strip()
            order.quantity = int(request.form.get('quantity', 1))
            order.delivery_date = datetime.strptime(request.form['delivery_date'], '%Y-%m-%d').date()
            order.stitching_cost = float(request.form['stitching_cost'])
            order.advance_paid = float(request.form.get('advance_paid', 0))
            order.status = request.form.get('status', 'pending')
            
            # Validate advance payment
            if order.advance_paid > order.stitching_cost:
                flash('Advance payment cannot be greater than stitching cost.', 'error')
                return render_template('orders/edit.html', 
                                     order=order,
                                     dress_types=DRESS_TYPES,
                                     order_statuses=ORDER_STATUSES)
            
            # Update balance
            order.update_balance()
            
            db.session.commit()
            
            # Send WhatsApp notification if status changed
            if previous_status != order.status:
                from utils import send_order_status_update
                send_order_status_update(order, previous_status)
            
            flash(f'Order {order.order_number} updated successfully!', 'success')
            return redirect(url_for('orders.view', id=order.id))
            
        except ValueError as e:
            flash('Invalid input values. Please check your entries.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating order: {str(e)}', 'error')
    
    return render_template('orders/edit.html', 
                         order=order,
                         dress_types=DRESS_TYPES,
                         order_statuses=ORDER_STATUSES)

@orders_bp.route('/view/<int:id>')
def view(id):
    """View order details, payments, and customer measurements"""
    order = Order.query.get_or_404(id)
    
    # Get relevant measurements for this dress type
    measurements = Measurement.query.filter_by(
        customer_id=order.customer_id,
        dress_type=order.dress_type
    ).first()
    
    # Get all payments for this order
    payments = Payment.query.filter_by(order_id=order.id).order_by(Payment.created_at.desc()).all()
    
    return render_template('orders/view.html', 
                         order=order, 
                         measurements=measurements,
                         payments=payments,
                         payment_methods=PAYMENT_METHODS)

@orders_bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    """Delete order and associated payments"""
    order = Order.query.get_or_404(id)
    
    try:
        order_number = order.order_number
        db.session.delete(order)
        db.session.commit()
        flash(f'Order {order_number} deleted successfully.', 'success')
        return redirect(url_for('orders.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting order: {str(e)}', 'error')
        return redirect(url_for('orders.view', id=id))

@orders_bp.route('/add-payment/<int:order_id>', methods=['POST'])
def add_payment(order_id):
    """Add payment to an order"""
    order = Order.query.get_or_404(order_id)
    
    try:
        amount = float(request.form['amount'])
        payment_method = request.form['payment_method']
        notes = request.form.get('notes', '').strip()
        
        if amount <= 0:
            flash('Payment amount must be greater than zero.', 'error')
            return redirect(url_for('orders.view', id=order_id))
        
        if amount > order.balance:
            flash('Payment amount cannot exceed remaining balance.', 'error')
            return redirect(url_for('orders.view', id=order_id))
        
        # Create payment record
        payment = Payment(
            order_id=order_id,
            amount=amount,
            payment_method=payment_method,
            notes=notes
        )
        
        db.session.add(payment)
        
        # Update order balance
        order.update_balance()
        
        # If fully paid and not delivered, mark as stitched
        if order.balance == 0 and order.status == 'pending':
            order.status = 'stitched'
        
        db.session.commit()
        flash(f'Payment of ₹{amount} added successfully!', 'success')
        
    except ValueError:
        flash('Invalid payment amount.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding payment: {str(e)}', 'error')
    
    return redirect(url_for('orders.view', id=order_id))

@orders_bp.route('/generate-invoice/<int:id>')
def generate_invoice(id):
    """Generate and download PDF invoice"""
    order = Order.query.get_or_404(id)
    
    try:
        filepath = generate_invoice_pdf(order)
        if filepath:
            return send_file(filepath, as_attachment=True, download_name=f'invoice_{order.order_number}.pdf')
        else:
            flash('Error generating invoice PDF.', 'error')
            return redirect(url_for('orders.view', id=id))
    except Exception as e:
        flash(f'Error generating invoice: {str(e)}', 'error')
        return redirect(url_for('orders.view', id=id))

@orders_bp.route('/quick-status-update/<int:id>', methods=['POST'])
def quick_status_update(id):
    """Quick status update for orders"""
    order = Order.query.get_or_404(id)
    
    try:
        previous_status = order.status
        new_status = request.form['status']
        
        if new_status in ['pending', 'in_progress', 'stitched', 'delivered']:
            order.status = new_status
            db.session.commit()
            
            # Send SMS notification
            if previous_status != new_status:
                send_order_status_sms(order, previous_status)
            
            flash(f'Order {order.order_number} status updated to {new_status.title()}!', 'success')
        else:
            flash('Invalid status value.', 'error')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating status: {str(e)}', 'error')
    
    # Redirect back to the referring page or order view
    return redirect(request.referrer or url_for('orders.view', id=id))
