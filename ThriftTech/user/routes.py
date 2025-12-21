# importing database connection library for talking to sql server
import pyodbc
# importing datetime to track when things happen
from datetime import datetime
# importing flask tools for web pages, redirects, and user sessions
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
# importing password security tools to hash and check passwords safely
from werkzeug.security import generate_password_hash, check_password_hash
# importing our custom database connection function
from database import get_db_connection
# importing loyalty program table setup function
from services.transaction import _ensure_loyalty_table_exists
# importing this blueprint to organize user-related routes
from . import user_bp
# importing models to work with invoices, cart, and products
from models.invoice import Invoice
from models.cart import Cart
from models.product import Product

# making sure all the order and invoice tables exist in database
def _ensure_order_schema_exists():
    # connecting to database to create necessary tables if they don't exist
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # creating orders table if it doesn't already exist
        cursor.execute(
            """
            IF OBJECT_ID('dbo.Orders', 'U') IS NULL
            BEGIN
                CREATE TABLE Orders (
                    OrderId INT IDENTITY(1,1) PRIMARY KEY,
                    UserId INT NOT NULL,
                    TotalAmount DECIMAL(10,2) NOT NULL,
                    TaxAmount DECIMAL(10,2) DEFAULT 0,
                    ShippingAmount DECIMAL(10,2) DEFAULT 0,
                    DiscountAmount DECIMAL(10,2) DEFAULT 0,
                    Status NVARCHAR(20) DEFAULT 'pending',
                    ShippingAddress NVARCHAR(MAX),
                    PaymentMethod NVARCHAR(50),
                    PaymentStatus NVARCHAR(20) DEFAULT 'pending',
                    FOREIGN KEY (UserId) REFERENCES Users(UserId)
                )
            END

            IF OBJECT_ID('dbo.OrderItems', 'U') IS NULL
            BEGIN
                CREATE TABLE OrderItems (
                    OrderItemId INT IDENTITY(1,1) PRIMARY KEY,
                    OrderId INT NOT NULL,
                    ProductId INT NOT NULL,
                    Quantity INT NOT NULL,
                    Price DECIMAL(10,2) NOT NULL,
                    FOREIGN KEY (OrderId) REFERENCES Orders(OrderId),
                    FOREIGN KEY (ProductId) REFERENCES Products(ProductId)
                )
            END

            IF OBJECT_ID('dbo.Invoices', 'U') IS NULL
            BEGIN
                CREATE TABLE Invoices (
                    InvoiceId INT IDENTITY(1,1) PRIMARY KEY,
                    UserId INT NOT NULL,
                    OrderId INT NOT NULL,
                    Total DECIMAL(10,2) NOT NULL,
                    CreatedAt DATETIME DEFAULT GETDATE(),
                    FOREIGN KEY (UserId) REFERENCES Users(UserId),
                    FOREIGN KEY (OrderId) REFERENCES Orders(OrderId)
                )
            END
            """
        )
        conn.commit()
    finally:
        conn.close()



# helper function to get database connection
def get_db():
    if 'db_conn' not in g:
        g.db_conn = get_db_connection()
    return g.db_conn

# teardown function to close the database connection
@user_bp.teardown_app_request
def close_db_connection(e=None):
    db = g.pop('db_conn', None)
    if db is not None:
        db.close()
        


# my account

@user_bp.route('/account')
def account():
    if 'user_id' not in session:
        flash('Please log in to view your account.', 'error')
        return redirect(url_for('user.login', next=url_for('user.account')))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    # basic user info
    cursor.execute("SELECT UserId, FullName, Username, Email, Role FROM Users WHERE UserId = ?", (user_id,))
    user = cursor.fetchone()

    # loyalty points (ensure table exists first)
    try:
        _ensure_loyalty_table_exists()
        cursor.execute("SELECT Points FROM LoyaltyPoints WHERE UserId = ?", (user_id,))
        lp = cursor.fetchone()
        loyalty_points = int(lp.Points) if lp else 0
    except Exception:
        loyalty_points = 0

    # recent orders
    try:
        _ensure_order_schema_exists()
        cursor.execute(
            "SELECT TOP 5 OrderId, TotalAmount, Status FROM Orders WHERE UserId = ? ORDER BY OrderId DESC",
            (user_id,)
        )
        recent_orders = cursor.fetchall()
    except Exception:
        recent_orders = []

    # recent invoices
    try:
        cursor.execute(
            "SELECT TOP 5 InvoiceId, OrderId, Total, CreatedAt FROM Invoices WHERE UserId = ? ORDER BY InvoiceId DESC",
            (user_id,)
        )
        recent_invoices = cursor.fetchall()
    except Exception:
        recent_invoices = []

    # recent repair requests
    try:
        cursor.execute(
            """
            IF OBJECT_ID('dbo.RepairServices', 'U') IS NULL
            BEGIN
                SELECT CAST(NULL AS INT) AS ServiceId, CAST(NULL AS NVARCHAR(100)) AS DeviceType,
                       CAST(NULL AS NVARCHAR(MAX)) AS IssueDescription, CAST(NULL AS NVARCHAR(20)) AS Status,
                       CAST(NULL AS DATETIME) AS SubmittedAt
            END
            ELSE
            BEGIN
                SELECT TOP 5 ServiceId, DeviceType, IssueDescription, Status, SubmittedAt
                FROM RepairServices WHERE UserId = ? ORDER BY SubmittedAt DESC
            END
            """,
            (user_id,)
        )
        # filter out the placeholder 
        rows = [r for r in cursor.fetchall() if getattr(r, 'ServiceId', None)]
        recent_repairs = rows
    except Exception:
        recent_repairs = []

    conn.close()

    return render_template(
        'account.html',
        user=user,
        loyalty_points=loyalty_points,
        recent_orders=recent_orders,
        recent_invoices=recent_invoices,
        recent_repairs=recent_repairs
    )

@user_bp.route('/account/profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('user.login', next=url_for('user.account')))
    full_name = request.form.get('FullName', '').strip()
    username = request.form.get('Username', '').strip()
    email = request.form.get('Email', '').strip()

    if not full_name or not email:
        flash('Full name and email are required.', 'error')
        return redirect(url_for('user.account'))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # ensure unique email 
        cursor.execute("SELECT COUNT(*) AS Cnt FROM Users WHERE Email = ? AND UserId <> ?", (email, session['user_id']))
        if cursor.fetchone()[0] > 0:
            flash('Email already in use by another account.', 'error')
            conn.close()
            return redirect(url_for('user.account'))

        cursor.execute(
            "UPDATE Users SET FullName = ?, Username = ?, Email = ? WHERE UserId = ?",
            (full_name, username or full_name, email, session['user_id'])
        )
        conn.commit()
        session['email'] = email
        session['full_name'] = full_name
        flash('Profile updated successfully.', 'success')
    except Exception as e:
        conn.rollback()
        flash('Error updating profile.', 'error')
        print(f"Profile update error: {e}")
    finally:
        conn.close()
    return redirect(url_for('user.account'))

@user_bp.route('/account/password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('user.login', next=url_for('user.account')))
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not current_password or not new_password:
        flash('Please fill in all password fields.', 'error')
        return redirect(url_for('user.account'))
    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('user.account'))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT PasswordHash FROM Users WHERE UserId = ?", (session['user_id'],))
        row = cursor.fetchone()
        if not row:
            flash('User not found.', 'error')
            return redirect(url_for('user.account'))
        if not check_password_hash(row.PasswordHash, current_password):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('user.account'))
        new_hash = generate_password_hash(new_password)
        cursor.execute("UPDATE Users SET PasswordHash = ? WHERE UserId = ?", (new_hash, session['user_id']))
        conn.commit()
        flash('Password updated successfully.', 'success')
    except Exception as e:
        conn.rollback()
        flash('Error updating password.', 'error')
        print(f"Password change error: {e}")
    finally:
        conn.close()
    return redirect(url_for('user.account'))
        
@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['FullName']
        password = request.form['PasswordHash']
        confirm_password = request.form['confirm_PasswordHash']
        email = request.form['Email'] 
        username = full_name  # set Username to FullName
        
        if not all([full_name, password, email]):
            flash('Please fill out all fields', 'error')
            return redirect(url_for('user.register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('user.register'))

        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        
        if conn is None:
            flash('Database connection error', 'error')
            return redirect(url_for('user.register'))
        
        try:
            with conn.cursor() as cursor:
                # check for duplicate email
                cursor.execute("SELECT COUNT(*) FROM Users WHERE Email=?", (email,))
                if cursor.fetchone()[0] > 0:
                    flash('Email already exists. Please use a different email or try logging in.', 'error')
                    return redirect(url_for('user.register'))
                
                cursor.execute("""
                    INSERT INTO Users (FullName, Username, PasswordHash, Email, Role) 
                    VALUES (?, ?, ?, ?, ?)
                """, (full_name, username, password_hash, email, 'customer'))
                conn.commit()
                
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('user.login'))
        except pyodbc.Error as ex:
            flash(f"An error occurred: {ex}", 'error')
            conn.rollback()
            return redirect(url_for('user.register'))
        finally:
            conn.close()
            
    return render_template('register.html')

## loggin in 

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['Email']
        password = request.form['PasswordHash']
        
        if not email or not password:
            flash('Please enter both email and password', 'error')
            return redirect(url_for('user.login'))
        
        conn = get_db_connection()
        if conn is None:
            flash('Database connection error', 'error')
            return redirect(url_for('user.login'))
        
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT UserId, Email, PasswordHash, Role, FullName FROM Users WHERE Email=?",
                    (email,)
                )
                user = cursor.fetchone()
                
                if user:
                    stored_password_hash = user.PasswordHash
                    if check_password_hash(stored_password_hash, password):
                        session['logged_in'] = True
                        session['user_id'] = user.UserId
                        session['email'] = email
                        session['role'] = user.Role
                        session['full_name'] = user.FullName

                        # admins go straight to the dashboard
                        if user.Role == 'admin':
                            return redirect(url_for('admin.dashboard'))

                        # otherwise, redirect to previous page 
                        next_page = request.form.get('next') or session.pop('next_page', None)
                        if next_page:
                            return redirect(next_page)
                        return redirect(url_for('home'))
                    else:
                        flash('Invalid email or password', 'error')
                else:
                    flash('Invalid email or password', 'error')
        except pyodbc.Error as ex:
            flash(f"An error occurred: {ex}", 'error')
        finally:
            conn.close()
        
        return redirect(url_for('user.login'))
    
    # GET request 
    next_page = request.args.get('next')
    if next_page:
        session['next_page'] = next_page
    elif request.referrer and not request.referrer.endswith('/login') and not request.referrer.endswith('/register'):
        # store the referring page, but not if it's login or register
        session['next_page'] = request.referrer

    return render_template('login.html')

## logout 

@user_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('home'))


## add to cart functionality 

@user_bp.route('/add_to_cart/<int:product_id>', methods=['GET', 'POST'])
def add_to_cart(product_id):
    """Add product to cart"""
    wants_json = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in (request.headers.get('Accept', '') or '')
    if 'user_id' not in session:
        if wants_json:
            from flask import jsonify
            return jsonify({'success': False, 'error': 'auth', 'message': 'Please log in to add items to cart'}), 401
        flash('Please log in to add items to cart', 'error')
        return redirect(url_for('user.login'))
    
    try:
        from models.cart import Cart
        from models.product import Product
        # accept quantity 
        quantity = 1
        if request.method == 'POST':
            quantity = int(request.form.get('quantity', 1) or 1)
        else:
            quantity = int(request.args.get('quantity', 1) or 1)
        # clamp quantity between 1 and 10
        quantity = max(1, min(10, quantity))

        # validate product exists
        product = Product.get_by_id(product_id)
        if not product:
            if wants_json:
                from flask import jsonify
                return jsonify({'success': False, 'error': 'not_found', 'message': 'Product not found'}), 404
            flash('Product not found', 'error')
            return redirect(request.referrer or url_for('product_catalog'))
        
        cart_item = Cart(user_id=session['user_id'], product_id=product_id, quantity=quantity)
        if cart_item.save():
            if wants_json:
                from flask import jsonify
                return jsonify({'success': True, 'message': 'Item added to cart'})
            flash('Item added to cart successfully!', 'success')
            return redirect(url_for('cart'))
        else:
            if wants_json:
                from flask import jsonify
                return jsonify({'success': False, 'error': 'server', 'message': 'Error adding item to cart'}), 500
            flash('Error adding item to cart', 'error')
            
    except Exception as e:
        if wants_json:
            from flask import jsonify
            return jsonify({'success': False, 'error': 'exception', 'message': 'Error adding item to cart'}), 500
        flash('Error adding item to cart', 'error')
        print(f"Cart error: {e}")
    
    return redirect(url_for('product_catalog'))

## updating the cart 
@user_bp.route('/update_cart/<int:cart_id>', methods=['POST'])
def update_cart(cart_id):
    """Update cart item quantity"""
    if 'user_id' not in session:
        return redirect(url_for('user.login'))
    
    try:
        from models.cart import Cart
        quantity = int(request.form.get('quantity', 1))
        # clamp quantity between 0 and 10 and also 0 is the removal 
        if quantity < 0:
            quantity = 0
        if quantity > 10:
            quantity = 10
        
        if quantity > 0:
            Cart.update_quantity(cart_id, session['user_id'], quantity)
            flash('Cart updated successfully!', 'success')
        else:
            Cart.remove_item(cart_id, session['user_id'])
            flash('Item removed from cart', 'success')
            
    except Exception as e:
        flash('Error updating cart', 'error')
        print(f"Update cart error: {e}")
    
    return redirect(url_for('cart'))

# clearing or deleting the cart 

@user_bp.route('/remove_from_cart/<int:cart_id>')
def remove_from_cart(cart_id):
    """Remove item from cart"""
    if 'user_id' not in session:
        return redirect(url_for('user.login'))
    
    try:
        from models.cart import Cart
        Cart.remove_item(cart_id, session['user_id'])
        flash('Item removed from cart', 'success')
    except Exception as e:
        flash('Error removing item from cart', 'error')
        print(f"Remove cart error: {e}")
    
    return redirect(url_for('cart'))

# checking out 

@user_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Checkout page"""
    if 'user_id' not in session:
        flash('Please log in to checkout', 'error')
        return redirect(url_for('user.login'))
    from models.cart import Cart
    from models.invoice import Invoice
    from services.transaction import TransactionService 

    _ensure_order_schema_exists()
    cart_items = Cart.get_user_cart(session['user_id'])
    if not cart_items:
        flash('Your cart is empty', 'error')
        return redirect(url_for('cart'))
    
    # calculate total with all transaction rules
    totals = TransactionService.calculate_cart_totals(cart_items, session['user_id'])
    
    # GET request - show checkout form
    if request.method == 'GET':
        return render_template('checkout.html', cart_items=cart_items, totals=totals)
    
    # POST request - process the order
    if request.method == 'POST':
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'address', 'city', 'province', 'zip_code', 'payment_method']
        for field in required_fields:
            if not request.form.get(field):
                flash(f'{field.replace("_", " ").title()} is required', 'error')
                return render_template('checkout.html', cart_items=cart_items, totals=totals)
        
        # create order
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Orders (UserId, TotalAmount, Status) VALUES (?, ?, ?)", 
                       (session['user_id'], totals['total'], 'completed'))
        conn.commit()
        order_id = cursor.execute("SELECT @@IDENTITY").fetchone()[0]
        
        # insert order items
        for item in cart_items:
            cursor.execute("INSERT INTO OrderItems (OrderId, ProductId, Quantity, Price) VALUES (?, ?, ?, ?)", 
                           (order_id, item['ProductId'], item['Quantity'], item['Price']))
        conn.commit()
        conn.close()
        
        # generate invoice
        invoice_id = Invoice.create(session['user_id'], order_id, totals['total'])
        
        # award loyalty points
        points_earned = TransactionService.award_loyalty_points(session['user_id'], totals['total'])
        
        # use loyalty points if any discount was applied
        if totals['loyalty_discount'] > 0:
            points_used = int(totals['loyalty_discount'] / 0.10)
            TransactionService.use_loyalty_points(session['user_id'], points_used)
        
        # clear cart
        Cart.clear_user_cart(session['user_id'])
        
        flash(f'Checkout complete! Invoice generated. You earned {points_earned} loyalty points!', 'success')
        return redirect(url_for('user.invoice_detail', invoice_id=invoice_id))

@user_bp.route('/invoices')
def invoices():
    if 'user_id' not in session:
        return redirect(url_for('user.login'))
    invoices = Invoice.get_by_user(session['user_id'])
    return render_template('invoices.html', invoices=invoices)

@user_bp.route('/invoice/<int:invoice_id>')
def invoice_detail(invoice_id):
    if 'user_id' not in session:
        return redirect(url_for('user.login'))
    invoice = Invoice.get_by_id(invoice_id)
    if not invoice or invoice.UserId != session['user_id']:
        flash('Invoice not found.', 'error')
        return redirect(url_for('user.invoices'))
    # get order items
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT oi.Quantity, oi.Price, p.Title FROM OrderItems oi JOIN Products p ON oi.ProductId = p.ProductId WHERE oi.OrderId = ?", (invoice.OrderId,))
    order_items = [
        {'Quantity': row.Quantity, 'Price': row.Price, 'Title': row.Title}
        for row in cursor.fetchall()
    ]
    conn.close()
    return render_template('invoice_detail.html', invoice=invoice, order_items=order_items)


#  list all orders for the logged-in user
@user_bp.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('user.login', next=url_for('user.orders')))
    _ensure_order_schema_exists()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT OrderId, UserId, TotalAmount, TaxAmount, ShippingAmount, DiscountAmount, Status
        FROM Orders WHERE UserId = ? ORDER BY OrderId DESC
        """,
        (session['user_id'],)
    )
    orders = cursor.fetchall()
    conn.close()
    return render_template('orders.html', orders=orders)


# detail view of the orders 
@user_bp.route('/order/<int:order_id>')
def order_detail(order_id):
    if 'user_id' not in session:
        return redirect(url_for('user.login', next=url_for('user.order_detail', order_id=order_id)))
    _ensure_order_schema_exists()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Orders WHERE OrderId = ?", (order_id,))
    order = cursor.fetchone()
    if not order or order.UserId != session['user_id']:
        conn.close()
        flash('Order not found.', 'error')
        return redirect(url_for('user.orders'))
    cursor.execute(
        """
        SELECT oi.ProductId, oi.Quantity, oi.Price, p.Title, p.Photo
        FROM OrderItems oi JOIN Products p ON oi.ProductId = p.ProductId
        WHERE oi.OrderId = ?
        """,
        (order_id,)
    )
    items = cursor.fetchall()
    conn.close()
    # compute total breakdown
    subtotal = sum(float(row.Price) * int(row.Quantity) for row in items)
    tax = float(order.TaxAmount) if getattr(order, 'TaxAmount', None) is not None else 0.0
    shipping = float(order.ShippingAmount) if getattr(order, 'ShippingAmount', None) is not None else 0.0
    discount = float(order.DiscountAmount) if getattr(order, 'DiscountAmount', None) is not None else 0.0
    total = float(order.TotalAmount)
    return render_template('order_detail.html', order=order, items=items, totals={
        'subtotal': round(subtotal, 2),
        'tax': round(tax, 2),
        'shipping': round(shipping, 2),
        'discount': round(discount, 2),
        'total': round(total, 2),
    })


#  cancel orders 
@user_bp.route('/order/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    if 'user_id' not in session:
        return redirect(url_for('user.login'))
    _ensure_order_schema_exists()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT OrderId, UserId, Status FROM Orders WHERE OrderId = ?", (order_id,))
    row = cursor.fetchone()
    if not row or row.UserId != session['user_id']:
        conn.close()
        flash('Order not found.', 'error')
        return redirect(url_for('user.orders'))
    if row.Status not in ('pending', 'processing'):
        conn.close()
        flash('This order cannot be cancelled.', 'error')
        return redirect(url_for('user.order_detail', order_id=order_id))
    cursor.execute("UPDATE Orders SET Status='cancelled' WHERE OrderId = ?", (order_id,))
    conn.commit()
    conn.close()
    flash('Order cancelled.', 'success')
    return redirect(url_for('user.order_detail', order_id=order_id))


#  reorder 
@user_bp.route('/order/<int:order_id>/reorder', methods=['POST'])
def reorder(order_id):
    if 'user_id' not in session:
        return redirect(url_for('user.login'))
    _ensure_order_schema_exists()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT OrderId, UserId FROM Orders WHERE OrderId = ?", (order_id,))
    order = cursor.fetchone()
    if not order or order.UserId != session['user_id']:
        conn.close()
        flash('Order not found.', 'error')
        return redirect(url_for('user.orders'))
    cursor.execute("SELECT ProductId, Quantity FROM OrderItems WHERE OrderId = ?", (order_id,))
    items = cursor.fetchall()
    conn.close()
    from models.cart import Cart
    added = 0
    for it in items:
        try:
            ci = Cart(user_id=session['user_id'], product_id=it.ProductId, quantity=int(it.Quantity))
            ci.save()
            added += 1
        except Exception:
            pass
    flash(f'Re-added {added} items to your cart.', 'success')
    return redirect(url_for('cart'))