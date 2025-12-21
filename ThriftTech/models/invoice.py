from database import get_db_connection
from datetime import datetime

class Invoice:
    def __init__(self, invoice_id=None, user_id=None, order_id=None, total=None, created_at=None):
        self.invoice_id = invoice_id
        self.user_id = user_id
        self.order_id = order_id
        self.total = total
        self.created_at = created_at or datetime.now()

    @staticmethod
    def create(user_id, order_id, total):
        # ensure table exists
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
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
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Invoices (UserId, OrderId, Total, CreatedAt)
            VALUES (?, ?, ?, ?)
        """, (user_id, order_id, total, datetime.now()))
        conn.commit()
        invoice_id = cursor.execute("SELECT @@IDENTITY").fetchone()[0]
        conn.close()
        return invoice_id

    @staticmethod
    def get_by_user(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Invoices WHERE UserId = ? ORDER BY CreatedAt DESC", (user_id,))
        invoices = cursor.fetchall()
        conn.close()
        return invoices

    @staticmethod
    def get_by_id(invoice_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Invoices WHERE InvoiceId = ?", (invoice_id,))
        invoice = cursor.fetchone()
        conn.close()
        return invoice
