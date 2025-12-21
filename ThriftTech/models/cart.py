from database import get_db_connection


def _ensure_cart_table_exists():
    """Create Cart table if it doesn't exist (idempotent)."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            IF OBJECT_ID('dbo.Cart', 'U') IS NULL
            BEGIN
                CREATE TABLE Cart (
                    CartId INT IDENTITY(1,1) PRIMARY KEY,
                    UserId INT NOT NULL,
                    ProductId INT NOT NULL,
                    Quantity INT DEFAULT 1,
                    AddedAt DATETIME DEFAULT GETDATE(),
                    FOREIGN KEY (UserId) REFERENCES Users(UserId),
                    FOREIGN KEY (ProductId) REFERENCES Products(ProductId)
                )
            END
            """
        )
        conn.commit()
    finally:
        conn.close()

class Cart:
    def __init__(self, cart_id=None, user_id=None, product_id=None, quantity=1):
        self.cart_id = cart_id
        self.user_id = user_id
        self.product_id = product_id
        self.quantity = quantity

    @staticmethod
    def get_user_cart(user_id):
        """Get all cart items for a user"""
        _ensure_cart_table_exists()
        conn = get_db_connection()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.CartId, c.UserId, c.ProductId, c.Quantity,
                       p.Title, p.Price, p.Photo, p.Description
                FROM Cart c
                JOIN Products p ON c.ProductId = p.ProductId
                WHERE c.UserId = ?
            """, (user_id,))
            cart_items = []
            for row in cursor.fetchall():
                cart_items.append({
                    'CartId': row.CartId,
                    'UserId': row.UserId,
                    'ProductId': row.ProductId,
                    'Quantity': row.Quantity,
                    'Title': row.Title,
                    'Price': float(row.Price),
                    'Photo': row.Photo,
                    'Description': row.Description,
                    'Total': float(row.Price) * float(row.Quantity)
                })
            conn.close()
            return cart_items
        except Exception as e:
            print(f"Error getting cart: {e}")
            conn.close()
            return []

    def save(self):
        """Add item to cart or update quantity if exists"""
        _ensure_cart_table_exists()
        conn = get_db_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            
            # check if item already exists in cart
            cursor.execute("""
                SELECT CartId, Quantity FROM Cart 
                WHERE UserId = ? AND ProductId = ?
            """, (self.user_id, self.product_id))
            existing_item = cursor.fetchone()
            
            if existing_item:
                # update quantity
                new_quantity = existing_item.Quantity + self.quantity
                cursor.execute("""
                    UPDATE Cart SET Quantity = ? 
                    WHERE CartId = ?
                """, (new_quantity, existing_item.CartId))
            else:
                # insert new item
                cursor.execute("""
                    INSERT INTO Cart (UserId, ProductId, Quantity)
                    VALUES (?, ?, ?)
                """, (self.user_id, self.product_id, self.quantity))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error saving cart item: {e}")
            conn.rollback()
            conn.close()
            return False

    @staticmethod
    def remove_item(cart_id, user_id):
        """Remove item from cart"""
        _ensure_cart_table_exists()
        conn = get_db_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM Cart 
                WHERE CartId = ? AND UserId = ?
            """, (cart_id, user_id))
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error removing cart item: {e}")
            conn.close()
            return False

    @staticmethod
    def update_quantity(cart_id, user_id, quantity):
        """Update quantity for a cart item; if quantity <= 0, remove the item.

        Returns True on success, False on failure.
        """
        _ensure_cart_table_exists()
        conn = get_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            if quantity <= 0:
                # treat non-positive quantities as a remove action
                cursor.execute(
                    "DELETE FROM Cart WHERE CartId = ? AND UserId = ?",
                    (cart_id, user_id),
                )
            else:
                cursor.execute(
                    "UPDATE Cart SET Quantity = ? WHERE CartId = ? AND UserId = ?",
                    (quantity, cart_id, user_id),
                )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating cart quantity: {e}")
            conn.rollback()
            conn.close()
            return False

    @staticmethod
    def clear_user_cart(user_id):
        """Clear all items from user's cart"""
        _ensure_cart_table_exists()
        conn = get_db_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Cart WHERE UserId = ?", (user_id,))
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error clearing cart: {e}")
            conn.close()
            return False