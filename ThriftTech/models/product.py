# importing database connection to talk to our product storage
from database import get_db_connection

# product model class that represents items people can buy, rent or auction
class Product:
    # setting up a new product object with all the details about an item
    def __init__(self, product_id=None, title=None, description=None, price=None,
                 category=None, photo=None, seller_id=None, status='available', daily_rate=None):
        # unique number to identify this product
        self.product_id = product_id
        # the name/title of the item being sold
        self.title = title  
        # detailed explanation of what the product is
        self.description = description
        # how much money it costs to buy
        self.price = price
        # what type of product it is (electronics, clothing, etc)
        self.category = category
        # picture filename to show what it looks like
        self.photo = photo
        # id of the person who is selling this item
        self.seller_id = seller_id
        # whether item is available, sold, rented, etc
        self.status = status
        # how much it costs per day if renting
        self.daily_rate = daily_rate

    # making sure the database has a daily rate column for rental prices
    @staticmethod
    def _ensure_daily_rate_column(cur):
        """Add Products.DailyRate column if missing (idempotent)."""
        try:
            # checking if daily rate column already exists in products table
            cur.execute("SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Products') AND name = 'DailyRate'")
            if cur.fetchone() is None:
                # adding the daily rate column if it's missing
                cur.execute("ALTER TABLE dbo.Products ADD DailyRate DECIMAL(10,2) NULL")
        except Exception:
            # ignoring errors because column might not exist in some setups
            pass

    # getting all products from database to display on website
    @staticmethod
    def get_all():
        """Get all products from database"""
        # connecting to database to fetch all available products
        conn = get_db_connection()
        cursor = conn.cursor()
        # asking database for every single product record
        cursor.execute("SELECT * FROM Products")
        products = []
        # going through each product and building a nice dictionary for each one
        for row in cursor.fetchall():
            products.append({
                'ProductId': row.ProductId,
                'Title': row.Title,
                'Description': row.Description,
                'Price': row.Price,
                'Category': row.Category,
                'Photo': row.Photo,
                'DailyRate': getattr(row, 'DailyRate', None),
                'Stock': row.Stock,
                'CreatedAt': row.CreatedAt,
                'UpdatedAt': row.UpdatedAt,
                'name': row.Title  # alias for compatibility with older code
            })
        conn.close()
        # returning the complete list of all products
        return products
# get product by ID
    @staticmethod
    def get_by_id(product_id):
        """Get product by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Products WHERE ProductId = ?", (product_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'ProductId': row.ProductId,
                'Title': row.Title,
                'Description': row.Description,
                'Price': row.Price,
                'Category': row.Category,
                'Photo': row.Photo,
                'DailyRate': getattr(row, 'DailyRate', None),
                'Stock': row.Stock,
                'CreatedAt': row.CreatedAt,
                'UpdatedAt': row.UpdatedAt,
                'name': row.Title  # Alias for compatibility
            }
        return None

# get products by category
    @staticmethod
    def get_by_category(category):
        """Get products by category"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Products WHERE Category = ?", (category,))
        products = []
        for row in cursor.fetchall():
            products.append({
                'ProductId': row.ProductId,
                'Title': row.Title,
                'Description': row.Description,
                'Price': row.Price,
                'Category': row.Category,
                'Photo': row.Photo,
                'DailyRate': getattr(row, 'DailyRate', None),
                'Stock': row.Stock,
                'CreatedAt': row.CreatedAt,
                'UpdatedAt': row.UpdatedAt,
                'name': row.Title  # Alias for compatibility
            })
        conn.close()
        return products
# save product
    def save(self):
        """Save product to database"""
        conn = get_db_connection()
        cursor = conn.cursor()
        if self.product_id:
            # Update existing product
            # ensure column exists before referencing it
            Product._ensure_daily_rate_column(cursor)
            if self.daily_rate is not None:
                cursor.execute(
                    """
                    UPDATE Products 
                    SET Title=?, Description=?, Price=?, Category=?, Photo=?, DailyRate=?
                    WHERE ProductId=?
                    """,
                    (self.title, self.description, self.price, self.category, self.photo, self.daily_rate, self.product_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE Products 
                    SET Title=?, Description=?, Price=?, Category=?, Photo=?
                    WHERE ProductId=?
                    """,
                    (self.title, self.description, self.price, self.category, self.photo, self.product_id),
                )
        else:
            # Insert new product - match actual database schema
            Product._ensure_daily_rate_column(cursor)
            if self.daily_rate is not None:
                cursor.execute(
                    """
                    INSERT INTO Products (Title, Description, Price, Category, Photo, Stock, DailyRate)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (self.title, self.description, self.price, self.category, self.photo, 10, self.daily_rate),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO Products (Title, Description, Price, Category, Photo, Stock)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (self.title, self.description, self.price, self.category, self.photo, 10),
                )
        conn.commit()
        conn.close()

# delete product
    @staticmethod
    def delete(product_id):
        """Safely delete a product.
        - If referenced by OrderItems, perform a soft delete (set Status='unavailable').
        - Else, delete dependent rows in Cart and Auctions, then delete the product.
        Returns (success: bool, message: str).
        """
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            # Helper to check references safely (table may not exist in older DBs)
            def _has_refs(table_name: str) -> bool:
                try:
                    cur.execute(f"SELECT TOP 1 1 FROM {table_name} WHERE ProductId = ?", (product_id,))
                    return cur.fetchone() is not None
                except Exception:
                    return False

            # Check for existing references that should preserve history
            has_order_refs = _has_refs('OrderItems')
            has_auction_refs = _has_refs('Auctions')
            has_rental_refs = _has_refs('Rentals')

            if has_order_refs or has_auction_refs or has_rental_refs:
                # Soft delete to maintain referential integrity and preserve history
                cur.execute("UPDATE Products SET Status='unavailable' WHERE ProductId = ?", (product_id,))
                conn.commit()
                reason = []
                if has_order_refs:
                    reason.append('orders')
                if has_auction_refs:
                    reason.append('auctions')
                if has_rental_refs:
                    reason.append('rentals')
                return True, f"Product set to unavailable (referenced by {', '.join(reason)})."

            # Remove from carts (ignore if table missing)
            try:
                cur.execute("DELETE FROM Cart WHERE ProductId = ?", (product_id,))
            except Exception:
                pass
            # No historical references: it's safe to drop auctions entirely (ignore if table missing)
            try:
                cur.execute("DELETE FROM Auctions WHERE ProductId = ?", (product_id,))
            except Exception:
                pass
            # Now delete the product
            cur.execute("DELETE FROM Products WHERE ProductId = ?", (product_id,))
            conn.commit()
            return True, "Product deleted."
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            return False, "Failed to delete product."
        finally:
            conn.close()

# add new product 
    @staticmethod
    def add(title, description, price, category, photo):
        """Add a new product to the database (admin)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        Product._ensure_daily_rate_column(cursor)
        cursor.execute(
            """
            INSERT INTO Products (Title, Description, Price, Category, Photo, Stock)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, description, price, category, photo, 10),
        )
        conn.commit()
        conn.close()

# update existing product
    @staticmethod
    def update(product_id, title, description, price, category, photo):
        """Update an existing product in the database (admin)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        Product._ensure_daily_rate_column(cursor)
        cursor.execute(
            """
            UPDATE Products SET Title=?, Description=?, Price=?, Category=?, Photo=?
            WHERE ProductId=?
            """,
            (title, description, price, category, photo, product_id),
        )
        conn.commit()
        conn.close()