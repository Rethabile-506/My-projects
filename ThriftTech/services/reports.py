from database import get_db_connection
## overiew of reports service 

#  number of different products sold
class ReportService:
    @staticmethod
    def get_product_sales_count():
        """Number of different products sold"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT ProductId) FROM OrderItems")
        count = cursor.fetchone()[0] or 0
        conn.close()
        return count
# getting the number of products on hand
    @staticmethod
    def get_products_on_hand():
        """Number of products on hand for each product"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Title, Stock FROM Products WHERE Stock > 0")
        products = cursor.fetchall()
        conn.close()
        return products

# getting the number of users registered today
    @staticmethod
    def get_users_registered_today():
        """Number of users registered today"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Users WHERE CAST(RegistrationDate AS DATE) = CAST(GETDATE() AS DATE)")
        count = cursor.fetchone()[0] or 0
        conn.close()
        return count
# total revenue from all orders
    @staticmethod
    def get_total_revenue():
        """Total revenue from all orders"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(TotalAmount) FROM Orders WHERE Status = 'completed'")
        total = cursor.fetchone()[0] or 0
        conn.close()
        return total
# number of orders today
    @staticmethod
    def get_orders_today():
        """Number of orders today"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Invoices WHERE CAST(CreatedAt AS DATE) = CAST(GETDATE() AS DATE)")
        count = cursor.fetchone()[0] or 0
        conn.close()
        return count
# top selling categories
    @staticmethod
    def get_top_selling_categories():
        """Top selling categories"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.Category, SUM(oi.Quantity) as TotalSold 
            FROM OrderItems oi 
            JOIN Products p ON oi.ProductId = p.ProductId 
            GROUP BY p.Category 
            ORDER BY TotalSold DESC
        """)
        categories = cursor.fetchall()
        conn.close()
        return categories
# getting products with low stock
    @staticmethod
    def get_low_stock_products():
        """Products with low stock (less than 5)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Title, Stock FROM Products WHERE Stock < 5 ORDER BY Stock ASC")
        products = cursor.fetchall()
        conn.close()
        return products