# Tailoring Shop Management System

A comprehensive Progressive Web Application (PWA) designed specifically for women's tailoring businesses in India. This Flask-based application provides complete management of customers, orders, measurements, billing, and reporting with offline capabilities.

## 🌟 Features

### 📋 Core Functionality
- **Customer Management**: Add, edit, and manage customer information with detailed measurements
- **Order Tracking**: Complete order lifecycle management from placement to delivery
- **Pending Orders Dashboard**: Enhanced tracking with sorting, filtering, and urgency indicators
- **Measurements**: Store detailed measurements for multiple dress types (saree blouse, salwar, lehenga, kurti, gown, etc.)
- **Billing & Invoicing**: Generate professional PDF invoices and track payments
- **Reports & Analytics**: Comprehensive reporting with date range filtering and export options

### 🎯 Enhanced Order Management
- **Status Tracking**: Order placed → Stitching in progress → Stitched (ready) → Delivered
- **Overdue Alerts**: Automatic identification and highlighting of overdue orders
- **Quick Actions**: Bulk status updates and priority marking
- **Payment Tracking**: Multiple payment entries per order with different methods
- **Delivery Calendar**: Visual calendar view of scheduled deliveries

### 📱 Progressive Web App (PWA)
- **Installable**: Add to home screen on mobile and desktop
- **Offline Support**: Works without internet connection
- **Service Worker**: Background sync and caching
- **Responsive Design**: Mobile-friendly interface with Bootstrap 5

### 🔧 Technical Features
- **Automatic Backups**: Daily database backups to `/backups/` folder
- **Data Export**: CSV export for customers and orders
- **Print Support**: Print-optimized invoices and reports
- **Search & Filter**: Advanced filtering and search capabilities
- **Real-time Validation**: Client-side form validation with feedback

## 🛠 Technology Stack

### Backend
- **Flask**: Web framework with Blueprint architecture
- **SQLAlchemy**: Database ORM with SQLite
- **ReportLab**: PDF generation for invoices
- **Schedule**: Automated backup scheduling

### Frontend
- **Bootstrap 5**: Responsive UI framework
- **Vanilla JavaScript**: Enhanced interactivity
- **Chart.js**: Data visualization for reports
- **Service Worker**: PWA functionality

### Database
- **SQLite**: Local database with automatic backups
- **Models**: Customer, Order, Payment, Measurement

## � Deployment

The application is ready for deployment on various cloud platforms. Here are the recommended options:

### Quick Deployment Options

#### 1. **Railway** (Recommended - Free tier available)
- Connect your GitHub repository
- Automatic deployment on code changes
- Built-in database support
- Free tier: 512MB RAM, 1GB storage

#### 2. **Render** (Free tier available)
- Deploy directly from GitHub
- Automatic SSL certificates
- Free tier: 750 hours/month
- Persistent disk storage available

#### 3. **Heroku** (Free tier available)
- Classic choice for Flask apps
- Easy scaling options
- Free tier: 550-1000 hours/month

#### 4. **PythonAnywhere** (Python-focused)
- Specialized for Python web apps
- Beginner-friendly
- Paid plans start at $5/month

### Deployment Steps

1. **Push to GitHub** (required for most platforms)
2. **Choose a platform** from above
3. **Connect your repository**
4. **Set environment variables** (if needed):
   - `DATABASE_URL` (optional, defaults to SQLite)
   - `SESSION_SECRET` (recommended for production)
5. **Deploy!**

### Environment Variables

```bash
# Optional: Database URL (defaults to SQLite)
DATABASE_URL=sqlite:///tailoring.db

# Recommended: Secure session secret
SESSION_SECRET=your-secure-random-secret-here
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python main.py
```

The app will be available at `http://localhost:5000`

