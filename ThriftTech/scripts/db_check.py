import sys, os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from database import get_db_connection
# validation for not having non tech products
def main():
    conn = get_db_connection()
    cur = conn.cursor()
    print('Checking Products columns...')
    cur.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='Products' ORDER BY ORDINAL_POSITION")
    cols = [r[0] for r in cur.fetchall()]
    print('Products columns:', cols)
    print('Has Status column:', 'Status' in cols)

    print('\nChecking presence of tables Cart and CartItems...')
    cur.execute("SELECT name FROM sys.tables WHERE name IN ('Cart','CartItems','Auctions','OrderItems','Rentals') ORDER BY name")
    print('Tables:', [r[0] for r in cur.fetchall()])

    print('\nSample non-tech products (id, title, category):')
    cur.execute("SELECT TOP 10 ProductId, Title, Category FROM Products WHERE Category NOT IN ('Electronics','Smartphones','Laptops','Tablets','Cameras','Gaming Console','Audio Equipment','Camera Rental','Laptop Rental','Audio Rental','AV Rental','VR Rental','Drone Rental','Gaming Rental') ORDER BY ProductId")
    for r in cur.fetchall():
        print(r.ProductId, r.Title, r.Category)

    conn.close()

if __name__ == '__main__':
    main()
