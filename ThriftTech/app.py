# import all the libraries we need to build our thrift tech website
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from user.routes import user_bp
from admin import admin_bp
from database import get_db_connection 
from models.product import Product
from models.auction import Auction
import os
from werkzeug.security import generate_password_hash

# create our main flask app instance that will handle all requests
app = Flask(__name__)   

# set up basic app settings like secret key for sessions and debug mode
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
app.config['DEBUG'] = True


# define which product categories count as "tech" items for our marketplace
TECH_CATEGORIES = {
    'electronics',
    'smartphones',
    'laptops',
    'tablets',
    'cameras',
    'gaming console',
    'audio equipment',
    # these are rental items but still tech-related so we include them
    'camera rental',
    'laptop rental',
    'audio rental',
    'av rental',
    'vr rental',
    'drone rental',
    'gaming rental'
}

# separate list of rental categories so we can exclude them from main product pages
RENTAL_CATEGORIES = {
    'camera rental',
    'laptop rental',
    'audio rental',
    'av rental',
    'vr rental',
    'drone rental',
    'gaming rental'
}

# register our blueprint modules so they can handle different parts of the site
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)

# make sure we always have an admin user available for managing the site
def _ensure_admin_user():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # check if we already have an admin user and fix their password if needed
        try:
            cursor.execute("SELECT UserId, Role, PasswordHash FROM Users WHERE Email=?", ('admin@thrifttech.com',))
            seeded = cursor.fetchone()
            if seeded:
                # make sure this user has admin role
                if getattr(seeded, 'Role', '') != 'admin':
                    cursor.execute("UPDATE Users SET Role='admin' WHERE UserId=?", (seeded.UserId,))
              
                # check if password hash looks broken and fix it
                ph = getattr(seeded, 'PasswordHash', '') or ''
                if ph.strip() == 'pbkdf2:sha256:260000$salt$hash' or len(ph) < 60:
                    pwd_hash = generate_password_hash('Admin@123')
                    cursor.execute("UPDATE Users SET PasswordHash=? WHERE UserId=?", (pwd_hash, seeded.UserId))
                conn.commit()
        except Exception:
            pass

        # if we already have any admin user, we're good to go
        cursor.execute("SELECT TOP 1 UserId FROM Users WHERE Role='admin'")
        if cursor.fetchone():
            conn.close()
            return

        # no admin found, so create or promote a default admin user
        admin_email = 'admin@thrifttech.local'
        cursor.execute("SELECT UserId FROM Users WHERE Email=?", (admin_email,))
        row = cursor.fetchone()
        if row:
            # found existing user, just promote them to admin role
            cursor.execute("UPDATE Users SET Role='admin' WHERE UserId=?", (row.UserId,))
        else:
            # no user found, create a brand new admin with default password
            pwd_hash = generate_password_hash('Admin@123')
            cursor.execute(
                """
                INSERT INTO Users (FullName, Username, PasswordHash, Email, Role)
                VALUES (?, ?, ?, ?, 'admin')
                """,
                ('Administrator', 'admin', pwd_hash, admin_email)
            )
        conn.commit()
        conn.close()
    except Exception as e:
        # if anything goes wrong, rollback database changes and continue
        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass
        print(f"Admin bootstrap skipped: {e}")

# run the admin setup when the app starts
_ensure_admin_user()

# create an api endpoint that other apps can use to get our product data
@app.route('/api/products', methods=['GET'])
def api_products():
    """
    api that returns product data as json so other websites can use our catalog
    lets people filter by category and sort the results different ways
    """
    try:
        # get filter and sort options from the url parameters
        category = request.args.get('category', '')
        sort_by = request.args.get('sort', 'Title')  
        order = request.args.get('order', 'asc')    
        
        # get all products but only include tech items and exclude rentals
        products = Product.get_all()
        products = [
            p for p in products
            if p.get('Category', '').lower() in TECH_CATEGORIES
            and p.get('Category', '').lower() not in RENTAL_CATEGORIES  # rentals don't belong in general product api
        ]
        
        # if user wants specific category, filter down to just those items
        if category:
            products = [
                p for p in products
                if p.get('Category', '').lower() == category.lower()
            ]
        
        # sort the products based on what user requested
        reverse_order = (order.lower() == 'desc')
        if sort_by == 'Price':
            products.sort(key=lambda x: float(x.get('Price', 0)), reverse=reverse_order)
        elif sort_by == 'Category':
            products.sort(key=lambda x: x.get('Category', ''), reverse=reverse_order)
        else:  # default to sorting by title
            products.sort(key=lambda x: x.get('Title', ''), reverse=reverse_order)
        
        # package up the response with useful info for api users
        response_data = {
            'success': True,
            'count': len(products),
            'products': products,
            'filters': {
                'category': category,
                'sort_by': sort_by,
                'order': order
            },
            'service_info': {
                'endpoint': '/api/products',
                'description': 'ThriftTech Product Catalog API',
                'version': '1.0'
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        # if something breaks, return error message instead of crashing
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to retrieve products'
        }), 500

# main home page that shows featured products to visitors
@app.route('/') 
def home(): 
    """grab some products to display on the home page"""
    # get all products but only show tech items, not rental stuff
    products = Product.get_all()
    products = [
        p for p in products
        if p.get('Category', '').lower() in TECH_CATEGORIES
        and p.get('Category', '').lower() not in RENTAL_CATEGORIES  # rentals have their own page
    ]
    return render_template('home.html', products=products) 

# product catalog page where people can browse and filter all our items
@app.route('/product')
def product_catalog():
    """show products with options to sort and filter them"""
    # get search/filter parameters from the url
    category = request.args.get('category')
    sort_by = request.args.get('sort', 'title') 
    order = request.args.get('order', 'asc')    
    
    # get products either by specific category or all products
    if category:
        products = Product.get_by_category(category)
    else:
        products = Product.get_all()

    # filter to only tech products and exclude rental items
    products = [
        p for p in products
        if p.get('Category', '').lower() in TECH_CATEGORIES
        and p.get('Category', '').lower() not in RENTAL_CATEGORIES  # exclude rentals from catalog
    ]
    
    # sort the products based on what the user requested
    reverse = (order == 'desc')
    if sort_by == 'price':
        products.sort(key=lambda x: x['Price'], reverse=reverse)
    elif sort_by == 'title':
        products.sort(key=lambda x: x['Title'], reverse=reverse)
    elif sort_by == 'category':
        products.sort(key=lambda x: x['Category'], reverse=reverse)
    
    # send the filtered and sorted products to the template
    return render_template('product.html', products=products, 
                         current_category=category, sort_by=sort_by, order=order)

# individual product page where people can see details and add to cart
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """show detailed info for one specific product"""
    # look up the product by its id number
    product = Product.get_by_id(product_id)
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('product_catalog'))
    
    # find similar products to suggest to the customer
    recommendations = Product.get_by_category(product['Category'])
    recommendations = [
        p for p in recommendations
        if p['ProductId'] != product_id and p.get('Category', '').lower() in TECH_CATEGORIES
    ][:4]  # only show 4 recommendations max
    
    return render_template('product_detail.html', product=product, recommendations=recommendations)

# shopping cart page where users can see what they want to buy
@app.route('/cart')
def cart():
    """show the user's shopping cart with all items and totals"""
    # make sure user is logged in before showing their cart
    if 'user_id' not in session:
        flash('Please log in to view your cart', 'error')
        return redirect(url_for('user.login'))
    
    from models.cart import Cart
    from services.transaction import TransactionService
    # get all items in this user's cart
    cart_items = Cart.get_user_cart(session['user_id'])
    
    # calculate totals including taxes, discounts, shipping etc
    totals = TransactionService.calculate_cart_totals(cart_items, session['user_id'])
    
    return render_template('cart.html', cart_items=cart_items, totals=totals)

# sell page where users can list their own items for sale
@app.route('/sell', methods=['GET', 'POST'])
def sell():
    """let users add their own products to sell on our marketplace"""
    # only logged in users can sell items
    if 'user_id' not in session:
        flash('Please log in to sell items', 'error')
        return redirect(url_for('user.login'))
    
    # if user submitted the form, process their listing
    if request.method == 'POST':
        # grab all the details they entered
        title = request.form.get('item-name')
        category = request.form.get('item-category')
        condition = request.form.get('item-condition', 'refurbished')
        description = request.form.get('item-description')
        price = request.form.get('item-price')
        photo = request.form.get('item-photo', '')
        
        # make sure they filled out the important stuff
        if not all([title, category, description, price]):
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('sell'))
        
        try:
            # convert price to number and make sure it's reasonable
            price = float(price)
            if price <= 0:
                flash('Price must be greater than 0', 'error')
                return redirect(url_for('sell'))
            
            # create the new product listing
            product = Product(
                title=title,
                description=description,
                price=price,
                category=category,
                photo=photo if photo else f'https://via.placeholder.com/300x200/6C757D/FFFFFF?text={title.replace(" ", "+")}'
            )
            
            # save it to the database
            product.save()
            flash(f'Product "{title}" listed successfully!', 'success')
            return redirect(url_for('product_catalog'))
            
        except ValueError:
            # if price wasn't a valid number
            flash('Please enter a valid price', 'error')
            return redirect(url_for('sell'))
        except Exception as e:
            # if database save failed or other issues
            flash(f'Error listing product: {str(e)}', 'error')
            return redirect(url_for('sell'))
    
    # if it's a get request, just show the selling form
    return render_template('sell.html')

# helper function to make sure rental database table exists
def _ensure_rental_schema_exists():
    """create the rentals table if it doesn't exist yet"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            IF OBJECT_ID('dbo.Rentals', 'U') IS NULL
            BEGIN
                CREATE TABLE Rentals (
                    RentalId INT IDENTITY(1,1) PRIMARY KEY,
                    ProductId INT NOT NULL,
                    UserId INT NOT NULL,
                    StartDate DATE NOT NULL,
                    EndDate DATE NOT NULL,
                    DailyRate DECIMAL(10,2) NOT NULL,
                    TotalCost DECIMAL(10,2) NOT NULL,
                    Status NVARCHAR(20) DEFAULT 'active',
                    CreatedAt DATETIME DEFAULT GETDATE(),
                    FOREIGN KEY (ProductId) REFERENCES Products(ProductId),
                    FOREIGN KEY (UserId) REFERENCES Users(UserId)
                )
            END
            """
        )
        conn.commit()
    finally:
        conn.close()

@app.route('/rent', methods=['GET', 'POST'])
def rent():
    """Rent page - display available rental products and allow simple bookings."""
    from datetime import date, datetime

    # Handle booking submissions
    if request.method == 'POST':
        if 'user_id' not in session:
            flash('Please log in to rent items.', 'error')
            return redirect(url_for('user.login', next=url_for('rent')))
        try:
            product_id = int(request.form.get('product_id') or 0)
            start_str = (request.form.get('rental_date') or '').strip()
            end_str = (request.form.get('return_date') or '').strip()
            if not product_id or not start_str or not end_str:
                raise ValueError('Missing fields')
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
            if end_date <= start_date:
                flash('End date must be after start date.', 'error')
                return redirect(url_for('rent'))

            # Look up product to determine authoritative daily rate
            pr = Product.get_by_id(product_id)
            if not pr:
                flash('Product not found for rental.', 'error')
                return redirect(url_for('rent'))
            try:
                price = float(pr.get('Price') or 0)
            except Exception:
                price = 0.0
            daily_rate = pr.get('DailyRate')
            try:
                daily_rate = float(daily_rate) if daily_rate is not None else None
            except Exception:
                daily_rate = None
            if daily_rate is None:
                daily_rate = max(150.0, round(price * 0.05, 2)) if price else 150.0

            # Compute days and total
            days = (end_date - start_date).days
            total = round(days * daily_rate, 2)

            # Persist rental
            _ensure_rental_schema_exists()
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO Rentals (ProductId, UserId, StartDate, EndDate, DailyRate, TotalCost, Status)
                VALUES (?, ?, ?, ?, ?, ?, 'active')
                """,
                (product_id, session['user_id'], start_date, end_date, daily_rate, total),
            )
            conn.commit()
            conn.close()
            flash(f'Rental confirmed for {days} day(s). Total: R{total:.2f}', 'success')
            return redirect(url_for('rent'))
        except ValueError:
            flash('Please provide valid rental details.', 'error')
            return redirect(url_for('rent'))
        except Exception as e:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            flash('Could not complete rental. Please try again.', 'error')
            return redirect(url_for('rent'))

    # Build available rentals list
    products = Product.get_all()
    rentals = []
    for p in products:
        cat = (p.get('Category') or '').lower()
        if cat in RENTAL_CATEGORIES:
            try:
                price = float(p.get('Price') or 0)
            except Exception:
                price = 0.0
            # prefer stored DailyRate, else compute
            if p.get('DailyRate') is not None:
                try:
                    daily_rate = float(p.get('DailyRate'))
                except Exception:
                    daily_rate = None
            else:
                daily_rate = None
            if daily_rate is None:
                daily_rate = max(150.0, round(price * 0.05, 2)) if price else 150.0
            p_with_rate = dict(p)
            p_with_rate['DailyRate'] = daily_rate
            rentals.append(p_with_rate)

    # Load current user's rentals for display
    user_rentals = None
    if 'user_id' in session:
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT r.RentalId, r.ProductId,
                       r.StartDate AS RentalDate,
                       r.EndDate AS ReturnDate,
                       r.DailyRate, r.TotalCost, r.Status,
                       p.Title, p.Photo
                FROM Rentals r
                JOIN Products p ON p.ProductId = r.ProductId
                WHERE r.UserId = ?
                ORDER BY r.CreatedAt DESC
                """,
                (session['user_id'],),
            )
            user_rentals = cur.fetchall()
            conn.close()
        except Exception:
            user_rentals = []

    today_str = date.today().isoformat()
    return render_template('rent.html', products=rentals, available_products=rentals, user_rentals=user_rentals, today=today_str)

@app.route('/auction')
@app.route('/auction', methods=['GET'])
def auction():
    """Auction page"""
    # show active auctions
    try:
        Auction.seed_sample_auctions(6)
    except Exception:
        pass
    auctions = Auction.get_active_auctions()
    return render_template('auction.html', active_auctions=auctions)


@app.route('/auction/bid', methods=['POST'])
def auction_bid():
    if 'user_id' not in session:
        flash('Please log in to place a bid.', 'error')
        return redirect(url_for('auction'))
    user_id = session.get('user_id')
    auction_id = request.form.get('auction_id')
    bid_amount = request.form.get('bid_amount')
    try:
        auction_id = int(auction_id)
        bid_amount = float(bid_amount)
    except (TypeError, ValueError):
        flash('Invalid bid.', 'error')
        return redirect(url_for('auction'))

    ok, msg = Auction.place_bid(auction_id, user_id, bid_amount)
    flash(msg, 'success' if ok else 'error')
    return redirect(url_for('auction'))

def _ensure_repair_schema_exists():
    """Create RepairServices table if it doesn't exist (idempotent)."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            IF OBJECT_ID('dbo.RepairServices', 'U') IS NULL
            BEGIN
                CREATE TABLE RepairServices (
                    ServiceId INT IDENTITY(1,1) PRIMARY KEY,
                    UserId INT NOT NULL,
                    DeviceType NVARCHAR(100) NOT NULL,
                    IssueDescription NVARCHAR(MAX) NOT NULL,
                    EstimatedCost DECIMAL(10,2),
                    Status NVARCHAR(20) DEFAULT 'submitted',
                    SubmittedAt DATETIME DEFAULT GETDATE(),
                    CompletedAt DATETIME,
                    FOREIGN KEY (UserId) REFERENCES Users(UserId)
                )
            END
            """
        )
        conn.commit()
    finally:
        conn.close()

@app.route('/repair', methods=['GET', 'POST'])
def repair():
    """Repair page: submit and view repair requests"""
    from flask import request
    user_repairs = None
    # form submission
    if request.method == 'POST':
        if 'user_id' not in session:
            flash('Please log in to submit a repair request', 'error')
            return redirect(url_for('user.login', next=url_for('repair')))
        device_type = request.form.get('device-type', '').strip()
        issue_description = request.form.get('issue-description', '').strip()
        if not device_type or not issue_description:
            flash('Please provide device type and issue description.', 'error')
            return redirect(url_for('repair'))
        try:
            _ensure_repair_schema_exists()
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO RepairServices (UserId, DeviceType, IssueDescription, Status, SubmittedAt)
                VALUES (?, ?, ?, 'submitted', GETDATE())
                """,
                (session['user_id'], device_type, issue_description)
            )
            conn.commit()
            conn.close()
            flash('Your repair request has been submitted. We\'ll notify you with updates.', 'success')
            return redirect(url_for('repair'))
        except Exception as e:
            # log and rollback safely
            print(f"Repair submission error: {e}")
            try:
                if conn:
                    conn.rollback()
                    conn.close()
            except Exception:
                pass
            flash('Error submitting repair request. Please try again.', 'error')
            return redirect(url_for('repair'))

    #  show user repair history if logged in
    if 'user_id' in session:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT ServiceId, UserId, DeviceType, IssueDescription, EstimatedCost, Status, SubmittedAt, CompletedAt FROM RepairServices WHERE UserId = ? ORDER BY SubmittedAt DESC",
                (session['user_id'],)
            )
            user_repairs = cursor.fetchall()
            conn.close()
        except Exception:
            user_repairs = []
    return render_template('repair.html', user_repairs=user_repairs)

if __name__ == '__main__':
    app.run(debug=True)