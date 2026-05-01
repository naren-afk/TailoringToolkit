from database import db
from datetime import datetime
from sqlalchemy import func

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='customer', lazy=True, cascade='all, delete-orphan')
    measurements = db.relationship('Measurement', backref='customer', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Customer {self.name}>'

class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    dress_type = db.Column(db.String(50), nullable=False)  # saree_blouse, salwar, lehenga, kurti, gown, etc.
    
    # Common measurements
    bust = db.Column(db.Float)
    waist = db.Column(db.Float)
    hip = db.Column(db.Float)
    shoulder = db.Column(db.Float)
    arm_length = db.Column(db.Float)
    blouse_length = db.Column(db.Float)
    
    # Dress-specific measurements
    kurti_length = db.Column(db.Float)
    salwar_length = db.Column(db.Float)
    bottom_length = db.Column(db.Float)
    neck_depth = db.Column(db.Float)
    back_neck_depth = db.Column(db.Float)
    
    # Additional notes
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Measurement {self.dress_type} for {self.customer.name}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    
    # Order details
    dress_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer, default=1)
    
    # Dates
    order_date = db.Column(db.Date, nullable=False, default=func.current_date())
    delivery_date = db.Column(db.Date, nullable=False)
    
    # Pricing
    stitching_cost = db.Column(db.Float, nullable=False)
    advance_paid = db.Column(db.Float, default=0)
    balance = db.Column(db.Float, nullable=False)
    
    # Status: pending, in_progress, stitched, delivered
    status = db.Column(db.String(20), default='pending')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payments = db.relationship('Payment', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(Order, self).__init__(**kwargs)
        if not self.order_number:
            # Generate unique order number
            self.order_number = self.generate_order_number()
        # Calculate balance
        self.balance = self.stitching_cost - self.advance_paid
    
    def generate_order_number(self):
        """Generate unique order number with format: TO-YYMMDD-XXX"""
        today = datetime.now()
        date_str = today.strftime('%y%m%d')
        
        # Get count of orders today
        today_orders = Order.query.filter(
            func.date(Order.created_at) == today.date()
        ).count()
        
        return f"TO-{date_str}-{today_orders + 1:03d}"
    
    def update_balance(self):
        """Recalculate balance based on total payments"""
        total_paid = sum(payment.amount for payment in self.payments) + self.advance_paid
        self.balance = max(0, self.stitching_cost - total_paid)
    
    @property
    def is_overdue(self):
        """Check if order is overdue"""
        return self.delivery_date < datetime.now().date() and self.status != 'delivered'
    
    @property
    def status_color(self):
        """Get color class for status"""
        colors = {
            'pending': 'warning',
            'in_progress': 'info',
            'stitched': 'success',
            'delivered': 'secondary'
        }
        return colors.get(self.status, 'secondary')
    
    def __repr__(self):
        return f'<Order {self.order_number}>'

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), default='cash')  # cash, upi, card, bank_transfer
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Payment ₹{self.amount} for Order {self.order.order_number}>'
