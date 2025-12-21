import sys, os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from database import get_db_connection

RENTAL_CATEGORIES = {
     'laptop rental', 'audio rental', 'av rental', 'vr rental', 'drone rental', 'gaming rental'
}

def main():
    conn = get_db_connection()
    cur = conn.cursor()
    print('Distinct categories:')
    cur.execute("SELECT DISTINCT Category FROM Products ORDER BY Category")
    cats = [r[0] if isinstance(r, tuple) else r.Category for r in cur.fetchall()]
    for c in cats:
        print('-', c)
    print('\nProducts with category like %rental%:')
    cur.execute("SELECT ProductId, Title, Category FROM Products WHERE Category LIKE '%Rental%' ORDER BY ProductId")
    for r in cur.fetchall():
        pid = r[0] if isinstance(r, tuple) else r.ProductId
        title = r[1] if isinstance(r, tuple) else r.Title
        cat = r[2] if isinstance(r, tuple) else r.Category
        print(pid, title, cat)
    print('\nProducts in RENTAL_CATEGORIES:')
    placeholders = ','.join('?' for _ in RENTAL_CATEGORIES)
    cur.execute(f"SELECT ProductId, Title, Category FROM Products WHERE LOWER(Category) IN ({placeholders}) ORDER BY ProductId", tuple(RENTAL_CATEGORIES))
    rows = cur.fetchall()
    for r in rows:
        pid = r[0] if isinstance(r, tuple) else r.ProductId
        title = r[1] if isinstance(r, tuple) else r.Title
        cat = r[2] if isinstance(r, tuple) else r.Category
        print(pid, title, cat)
    print(f"\nCount in RENTAL_CATEGORIES: {len(rows)}")
    conn.close()

if __name__ == '__main__':
    main()
