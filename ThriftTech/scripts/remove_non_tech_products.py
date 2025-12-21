import sys
import os

# Ensure we can import app modules
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import get_db_connection
from models.product import Product

TECH_CATEGORIES = {
    'electronics',
    'smartphones',
    'laptops',
    'tablets',
    'cameras',
    'gaming console',
    'audio equipment',
    'camera rental',
    'laptop rental',
    'audio rental',
    'av rental',
    'vr rental',
    'drone rental',
    'gaming rental',
}

#validate and remove non-tech products
def main(dry_run: bool = False, force: bool = False):
    products = Product.get_all()
    to_remove = [p for p in products if (p.get('Category') or '').lower() not in TECH_CATEGORIES]
    print(f"Total products: {len(products)}")
    print(f"Non-tech products found: {len(to_remove)}")
    if not to_remove:
        return
    if dry_run:
        for p in to_remove:
            print(f"DRY RUN - would remove: #{p['ProductId']} {p['Title']} [{p.get('Category')}] ")
        return
    removed = 0
    soft = 0
    # optional: pre-delete auctions for non-tech products if forcing
    if force:
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            ids = [p['ProductId'] for p in to_remove]
            if ids:
                ph_ids = ",".join("?" for _ in ids)
                # find auctions tied to these products
                cur.execute(f"SELECT AuctionId FROM Auctions WHERE ProductId IN ({ph_ids})", ids)
                auction_ids = [row[0] if isinstance(row, tuple) else row.AuctionId for row in cur.fetchall()]
                if auction_ids:
                    ph_auc = ",".join("?" for _ in auction_ids)
                    # delete bid history first (if table exists)
                    try:
                        cur.execute(f"DELETE FROM BidHistory WHERE AuctionId IN ({ph_auc})", auction_ids)
                    except Exception:
                        pass
                    # then delete auctions
                    cur.execute(f"DELETE FROM Auctions WHERE AuctionId IN ({ph_auc})", auction_ids)
                # commit auction cleanup
                conn.commit()
        except Exception as e:
            print(f"Warning: failed to pre-delete auctions for non-tech products: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass
    for p in to_remove:
        ok, msg = Product.delete(p['ProductId'])
        if ok:
            if 'unavailable' in msg:
                soft += 1
            else:
                removed += 1
            print(f"OK - {msg} -> #{p['ProductId']} {p['Title']} [{p.get('Category')}] ")
        else:
            print(f"FAILED - Could not remove #{p['ProductId']} {p['Title']}: {msg}")
    print(f"Hard-deleted: {removed}; Soft-deleted: {soft}")


if __name__ == '__main__':
    dry = '--dry-run' in sys.argv
    force = '--force' in sys.argv
    main(dry_run=dry, force=force)
