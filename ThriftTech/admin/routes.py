from flask import render_template, request, redirect, url_for, flash, session
from . import admin_bp
from models.product import Product
from models.user import User
from database import get_db_connection
from services.reports import ReportService
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('user.login'))
        return f(*args, **kwargs)
    return decorated_function

# Allowed tech categories (case-insensitive)
ALLOWED_CATEGORIES = {
    'electronics',
    'smartphones',
    'laptops',
    'tablets',
    'cameras',
    'gaming console',
    'audio equipment',
    # rentals that are still tech-related
    'camera rental',
    'laptop rental',
    'audio rental',
    'av rental',
    'vr rental',
    'drone rental',
    'gaming rental',
}

# the dashboard route
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard with reports"""
    reports = {
        'products_sold': ReportService.get_product_sales_count(),
        'users_today': ReportService.get_users_registered_today(),
        'total_revenue': ReportService.get_total_revenue(),
        'orders_today': ReportService.get_orders_today(),
        'products_on_hand': ReportService.get_products_on_hand(),
        'top_categories': ReportService.get_top_selling_categories(),
        'low_stock': ReportService.get_low_stock_products()
    }
    return render_template('admin/dashboard.html', reports=reports)
    """Admin dashboard with statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # get statistics
    cursor.execute("SELECT COUNT(*) FROM Products")
    total_products = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM Users WHERE Role = 'customer'")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM Orders")
    total_orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(TotalAmount) FROM Orders WHERE Status = 'completed'")
    total_revenue = cursor.fetchone()[0] or 0
    
    conn.close()
    
    stats = {
        'total_products': total_products,
        'total_users': total_users,
        'total_orders': total_orders,
        'total_revenue': total_revenue
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/products')
@admin_required
def admin_products():
    """Manage products page"""
    products = Product.get_all()
    # Show only tech categories, per requirement
    products = [p for p in products if (p.get('Category') or '').lower() in ALLOWED_CATEGORIES]
    return render_template('admin/products.html', products=products)

@admin_bp.route('/product/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    """Add new product"""
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = float(request.form['price'])
        category = request.form['category']
        photo = request.form['photo']
        # optional daily rate for rentals
        dr_raw = (request.form.get('daily_rate') or '').strip()
        daily_rate = float(dr_raw) if dr_raw else None

        # Enforce tech-only categories
        if (category or '').lower() not in ALLOWED_CATEGORIES:
            flash('Only tech-related categories are allowed.', 'error')
            return redirect(url_for('admin.add_product'))
        
        product = Product(
            title=title,
            description=description,
            price=price,
            category=category,
            photo=photo,
            seller_id=session['user_id'],
            daily_rate=daily_rate,
        )
        product.save()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin.admin_products'))
    
    return render_template('admin/add_product.html')

@admin_bp.route('/product/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    """Edit product"""
    product = Product.get_by_id(product_id)
    if not product:
        flash('Product not found.', 'error')
        return redirect(url_for('admin.admin_products'))
    
    if request.method == 'POST':
        # Enforce tech-only categories
        if (request.form['category'] or '').lower() not in ALLOWED_CATEGORIES:
            flash('Only tech-related categories are allowed.', 'error')
            return redirect(url_for('admin.edit_product', product_id=product_id))
        dr_raw = (request.form.get('daily_rate') or '').strip()
        daily_rate = float(dr_raw) if dr_raw else None
        product_obj = Product(
            product_id=product_id,
            title=request.form['title'],
            description=request.form['description'],
            price=float(request.form['price']),
            category=request.form['category'],
            photo=request.form['photo'],
            status=request.form.get('status', product.get('Status', 'available')),
            daily_rate=daily_rate,
        )
        product_obj.save()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin.admin_products'))
    
    return render_template('admin/edit_product.html', product=product)

@admin_bp.route('/product/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    """Delete product"""
    ok, msg = Product.delete(product_id)
    flash(msg, 'success' if ok else 'error')
    return redirect(url_for('admin.admin_products'))

@admin_bp.route('/users') 
@admin_required
def manage_users():
    """Manage users page"""
    users = User.get_all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/reports')
@admin_required
def reports():
    """Reports page"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # get various reports
    cursor.execute("""
        SELECT Category, COUNT(*) as ProductCount 
        FROM Products 
        GROUP BY Category
    """)
    products_by_category = cursor.fetchall()
    
    cursor.execute("""
        SELECT CAST(CreatedAt as DATE) as OrderDate, COUNT(*) as OrderCount
        FROM Invoices
        GROUP BY CAST(CreatedAt as DATE)
        ORDER BY OrderDate DESC
    """)
    orders_by_date = cursor.fetchall()
    
    cursor.execute("""
        SELECT CAST(RegistrationDate as DATE) as RegDate, COUNT(*) as UserCount
        FROM Users 
        WHERE Role = 'customer'
        GROUP BY CAST(RegistrationDate as DATE)
        ORDER BY RegDate DESC
    """)
    users_by_date = cursor.fetchall()
    
    cursor.execute("""
        SELECT p.Title, SUM(oi.Quantity) as TotalSold
        FROM Products p
        JOIN OrderItems oi ON p.ProductId = oi.ProductId
        JOIN Orders o ON oi.OrderId = o.OrderId
        WHERE o.Status = 'completed'
        GROUP BY p.ProductId, p.Title
        ORDER BY TotalSold DESC
    """)
    top_products = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin/reports.html', 
                         products_by_category=products_by_category,
                         orders_by_date=orders_by_date,
                         users_by_date=users_by_date,
                         top_products=top_products)