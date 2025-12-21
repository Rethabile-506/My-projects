from database import get_db_connection

# ensure table exists for loyalty points 
def _ensure_loyalty_table_exists():
    """Create LoyaltyPoints table if it doesn't exist (idempotent)."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            IF OBJECT_ID('dbo.LoyaltyPoints', 'U') IS NULL
            BEGIN
                CREATE TABLE LoyaltyPoints (
                    UserId INT PRIMARY KEY,
                    Points INT DEFAULT 0,
                    FOREIGN KEY (UserId) REFERENCES Users(UserId)
                )
            END
            """
        )
        conn.commit()
    finally:
        conn.close()

# handling transactions 
class TransactionService:
    @staticmethod
    def calculate_cart_totals(cart_items, user_id=None):
        """Calculate cart totals with all transaction rules"""
        # snsure we use float arithmetic 
        subtotal = sum(float(item['Total']) for item in cart_items)
        
        # rule 1: tax (15% VAT)
        tax = subtotal * 0.15
        
        # rule 2: free Shipping (orders over R500)
        shipping = 0.0 if subtotal > 500.0 else 85.0
        
        # rule 3: loyalty points discount
        loyalty_discount = 0
        if user_id:
            loyalty_discount = TransactionService.apply_loyalty_discount(subtotal, user_id)

        # rule 4: bulk discount (orders over R1000 get 5% off)
        bulk_discount = 0
        if subtotal > 1000.0:
            bulk_discount = subtotal * 0.05
        
        total_discount = loyalty_discount + bulk_discount
        final_total = subtotal + tax + shipping - total_discount
        
        return {
            'subtotal': round(subtotal, 2),
            'tax': round(tax, 2),
            'shipping': round(shipping, 2),
            'loyalty_discount': round(loyalty_discount, 2),
            'bulk_discount': round(bulk_discount, 2),
            'total_discount': round(total_discount, 2),
            'total': round(final_total, 2)
        }
    
    # applying loyalty points discount
    @staticmethod
    def apply_loyalty_discount(subtotal, user_id):
        """Apply loyalty points discount (max 10% of order)"""
        _ensure_loyalty_table_exists()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Points FROM LoyaltyPoints WHERE UserId = ?", (user_id,))
        result = cursor.fetchone()
        points = result.Points if result else 0
        conn.close()
        
        # each point = R0.10 discount, max 10% of order
        max_discount = float(subtotal) * 0.10
        points_discount = min(float(points) * 0.10, max_discount)
        return points_discount
    
    # awarding loyalty points
    @staticmethod
    def award_loyalty_points(user_id, order_total):
        """Award loyalty points (1 point per R10 spent)"""
        points_earned = int(order_total / 10)
        _ensure_loyalty_table_exists()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # check if user has loyalty record
        cursor.execute("SELECT Points FROM LoyaltyPoints WHERE UserId = ?", (user_id,))
        result = cursor.fetchone()
        
        if result:
            new_points = result.Points + points_earned
            cursor.execute("UPDATE LoyaltyPoints SET Points = ? WHERE UserId = ?", (new_points, user_id))
        else:
            cursor.execute("INSERT INTO LoyaltyPoints (UserId, Points) VALUES (?, ?)", (user_id, points_earned))
        
        conn.commit()
        conn.close()
        return points_earned

    # deducting loyalty points after purchase 
    @staticmethod
    def use_loyalty_points(user_id, points_used):
        """Deduct loyalty points after purchase"""
        _ensure_loyalty_table_exists()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE LoyaltyPoints SET Points = Points - ? WHERE UserId = ?", (points_used, user_id))
        conn.commit()
        conn.close()