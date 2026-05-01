from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import Customer, Measurement, Order
from database import db
from utils import DRESS_TYPES

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/')
def index():
    """List all customers with search functionality"""
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = Customer.query
    if search:
        query = query.filter(
            db.or_(
                Customer.name.contains(search),
                Customer.phone.contains(search)
            )
        )
    
    customers = query.order_by(Customer.name).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('customers/index.html', customers=customers, search=search)

@customers_bp.route('/add', methods=['GET', 'POST'])
def add():
    """Add new customer"""
    if request.method == 'POST':
        try:
            customer = Customer(
                name=request.form['name'].strip(),
                phone=request.form['phone'].strip(),
                address=request.form.get('address', '').strip()
            )
            
            # Validate required fields
            if not customer.name or not customer.phone:
                flash('Name and phone number are required.', 'error')
                return render_template('customers/add.html', dress_types=DRESS_TYPES)
            
            db.session.add(customer)
            db.session.flush()  # Get customer ID
            
            # Add measurements if provided
            for dress_type in DRESS_TYPES:
                dress_key = dress_type.lower().replace(' ', '_')
                if request.form.get(f'{dress_key}_bust'):
                    measurement = Measurement(
                        customer_id=customer.id,
                        dress_type=dress_type,
                        bust=float(request.form.get(f'{dress_key}_bust') or 0),
                        waist=float(request.form.get(f'{dress_key}_waist') or 0),
                        hip=float(request.form.get(f'{dress_key}_hip') or 0),
                        shoulder=float(request.form.get(f'{dress_key}_shoulder') or 0),
                        arm_length=float(request.form.get(f'{dress_key}_arm_length') or 0),
                        blouse_length=float(request.form.get(f'{dress_key}_blouse_length') or 0),
                        kurti_length=float(request.form.get(f'{dress_key}_kurti_length') or 0),
                        salwar_length=float(request.form.get(f'{dress_key}_salwar_length') or 0),
                        bottom_length=float(request.form.get(f'{dress_key}_bottom_length') or 0),
                        neck_depth=float(request.form.get(f'{dress_key}_neck_depth') or 0),
                        back_neck_depth=float(request.form.get(f'{dress_key}_back_neck_depth') or 0),
                        notes=request.form.get(f'{dress_key}_notes', '').strip()
                    )
                    db.session.add(measurement)
            
            db.session.commit()
            flash(f'Customer {customer.name} added successfully!', 'success')
            return redirect(url_for('customers.view', id=customer.id))
            
        except ValueError as e:
            flash('Invalid measurement values. Please enter valid numbers.', 'error')
            return render_template('customers/add.html', dress_types=DRESS_TYPES)
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding customer: {str(e)}', 'error')
            return render_template('customers/add.html', dress_types=DRESS_TYPES)
    
    return render_template('customers/add.html', dress_types=DRESS_TYPES)

@customers_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    """Edit customer details and measurements"""
    customer = Customer.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            customer.name = request.form['name'].strip()
            customer.phone = request.form['phone'].strip()
            customer.address = request.form.get('address', '').strip()
            
            # Validate required fields
            if not customer.name or not customer.phone:
                flash('Name and phone number are required.', 'error')
                return render_template('customers/edit.html', customer=customer, dress_types=DRESS_TYPES)
            
            # Update or create measurements
            for dress_type in DRESS_TYPES:
                dress_key = dress_type.lower().replace(' ', '_')
                if request.form.get(f'{dress_key}_bust'):
                    # Find existing measurement or create new
                    measurement = Measurement.query.filter_by(
                        customer_id=customer.id,
                        dress_type=dress_type
                    ).first()
                    
                    if not measurement:
                        measurement = Measurement(
                            customer_id=customer.id,
                            dress_type=dress_type
                        )
                        db.session.add(measurement)
                    
                    # Update measurement values
                    measurement.bust = float(request.form.get(f'{dress_key}_bust') or 0)
                    measurement.waist = float(request.form.get(f'{dress_key}_waist') or 0)
                    measurement.hip = float(request.form.get(f'{dress_key}_hip') or 0)
                    measurement.shoulder = float(request.form.get(f'{dress_key}_shoulder') or 0)
                    measurement.arm_length = float(request.form.get(f'{dress_key}_arm_length') or 0)
                    measurement.blouse_length = float(request.form.get(f'{dress_key}_blouse_length') or 0)
                    measurement.kurti_length = float(request.form.get(f'{dress_key}_kurti_length') or 0)
                    measurement.salwar_length = float(request.form.get(f'{dress_key}_salwar_length') or 0)
                    measurement.bottom_length = float(request.form.get(f'{dress_key}_bottom_length') or 0)
                    measurement.neck_depth = float(request.form.get(f'{dress_key}_neck_depth') or 0)
                    measurement.back_neck_depth = float(request.form.get(f'{dress_key}_back_neck_depth') or 0)
                    measurement.notes = request.form.get(f'{dress_key}_notes', '').strip()
            
            db.session.commit()
            flash(f'Customer {customer.name} updated successfully!', 'success')
            return redirect(url_for('customers.view', id=customer.id))
            
        except ValueError as e:
            flash('Invalid measurement values. Please enter valid numbers.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating customer: {str(e)}', 'error')
    
    return render_template('customers/edit.html', customer=customer, dress_types=DRESS_TYPES)

@customers_bp.route('/view/<int:id>')
def view(id):
    """View customer details, measurements, and order history"""
    customer = Customer.query.get_or_404(id)
    measurements = {m.dress_type: m for m in customer.measurements}
    orders = Order.query.filter_by(customer_id=id).order_by(Order.created_at.desc()).all()
    
    return render_template('customers/view.html', 
                         customer=customer, 
                         measurements=measurements,
                         orders=orders,
                         dress_types=DRESS_TYPES)

@customers_bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    """Delete customer and all associated data"""
    customer = Customer.query.get_or_404(id)
    
    try:
        # Check if customer has any orders
        if customer.orders:
            flash(f'Cannot delete {customer.name}. Customer has existing orders.', 'error')
            return redirect(url_for('customers.view', id=id))
        
        customer_name = customer.name
        db.session.delete(customer)
        db.session.commit()
        flash(f'Customer {customer_name} deleted successfully.', 'success')
        return redirect(url_for('customers.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting customer: {str(e)}', 'error')
        return redirect(url_for('customers.view', id=id))

@customers_bp.route('/api/search')
def api_search():
    """API endpoint for customer search (for autocomplete)"""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    customers = Customer.query.filter(
        db.or_(
            Customer.name.contains(query),
            Customer.phone.contains(query)
        )
    ).limit(10).all()
    
    results = []
    for customer in customers:
        results.append({
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone,
            'display': f'{customer.name} - {customer.phone}'
        })
    
    return jsonify(results)
