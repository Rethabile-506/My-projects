# ThriftTech

A Flask-based e-commerce web app for buying, renting, auctioning, and repairing tech products. SQL Server (LocalDB) backs product data, orders, invoices, carts, and more. Includes a customer area (My Account) and an Admin dashboard with reports.

## Tech Stack
- Python 3.10+
- Flask
- SQL Server LocalDB via pyodbc
- HTML/CSS (Jinja templates)

## Features
- Products: SQL-backed catalog and product detail pages (tech-only categories enforced)
- Cart & Checkout: Add/update/remove items; VAT, shipping, loyalty discounts; order, items, and invoice creation 
- Invoices: List and view invoice details
- Orders: List, detail, cancel (pending/processing), and reorder
- Auctions: Active auctions list and bidding, auto-seeded sample auctions 
- Repairs: Submit repair requests and view history
- My Account: Profile editing, password change, loyalty balance, recent orders/invoices/repairs
- Admin: Dashboard, product management (add/edit/delete), users list, reports (orders by date, top products, categories, inventory)

## Prerequisites
- Windows with SQL Server LocalDB installed
- ODBC Driver 17 for SQL Server
- Python (3.10 or newer)

## Read the requirements.txt and check if you have everything installed 

## Running the app 
- Navigate to the app.py in the project folder 
- Run it in its own terminal 
- It runs in debug mode and seeds auctions and ensures admin user
- Navigate to http://127.0.0.1:5000


## Logging in (Example Accounts)
- Admin (from TTDb.sql):
  - Email: `admin@thrifttech.com`
  - Password: `Admin@123`
  - On login, admins are redirected to the Admin Dashboard and see an Admin link in the nav.

- Fallback Admin (only created if no admin exists):
  - Email: `admin@thrifttech.local`
  - Password: `Admin@123`

- Example customers (from TTDb.sql):
  - The seed users have placeholder password hashes. To log in as a customer, register a new account via the Register page, or update one user’s `PasswordHash` to a known hash, or use the profile update features after registering.

## Key Navigation
- Home: `/`
- Products: `/product`
- Product Detail: `/product/<id>`
- Cart: `/cart`
- Checkout: `/user/checkout` (button in Cart)
- Invoices: `/user/invoices`
- Orders: `/user/orders`
- My Account: `/user/account` (also via "My Account" in nav)
- Auction: `/auction`
- Repair: `/repair`
- Admin Dashboard: `/admin/dashboard`
- Admin Products: `/admin/products`
- Admin Reports: `/admin/reports`


## Security Notes
- Passwords are hashed using Werkzeug.
- Session-based auth; admin routes require `session['role'] == 'admin']`.

