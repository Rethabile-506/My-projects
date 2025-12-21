from datetime import datetime
from database import get_db_connection


TECH_CATEGORIES = (
    'Electronics',
    'Smartphones',
    'Laptops',
    'Tablets',
    'Cameras',
    'Gaming Console',
    'Audio Equipment',
)

# auction model
class Auction:
    MIN_INCREMENT = 100.0

    @staticmethod
    def _ensure_table_exists():
        """Create Auctions table if it doesn't exist (idempotent)."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                IF OBJECT_ID('dbo.Auctions', 'U') IS NULL
                BEGIN
                    CREATE TABLE Auctions (
                        AuctionId INT IDENTITY(1,1) PRIMARY KEY,
                        ProductId INT NOT NULL,
                        StartingBid DECIMAL(10,2) NOT NULL,
                        CurrentBid DECIMAL(10,2),
                        HighestBidderId INT,
                        Photo NVARCHAR(500) NULL,
                        StartTime DATETIME NOT NULL,
                        EndTime DATETIME NOT NULL,
                        Status NVARCHAR(20) DEFAULT 'active',
                        CreatedAt DATETIME DEFAULT GETDATE(),
                        FOREIGN KEY (ProductId) REFERENCES Products(ProductId),
                        FOREIGN KEY (HighestBidderId) REFERENCES Users(UserId)
                    )
                END
                
                -- Add missing columns for older databases
                IF OBJECT_ID('dbo.Auctions', 'U') IS NOT NULL
                BEGIN
                    IF COL_LENGTH('dbo.Auctions', 'StartTime') IS NULL
                    BEGIN
                        ALTER TABLE dbo.Auctions ADD StartTime DATETIME CONSTRAINT DF_Auctions_StartTime DEFAULT GETDATE() WITH VALUES;
                        ALTER TABLE dbo.Auctions ALTER COLUMN StartTime DATETIME NOT NULL;
                    END

                    IF COL_LENGTH('dbo.Auctions', 'EndTime') IS NULL
                    BEGIN
                        ALTER TABLE dbo.Auctions ADD EndTime DATETIME CONSTRAINT DF_Auctions_EndTime DEFAULT (DATEADD(DAY, 3, GETDATE())) WITH VALUES;
                        ALTER TABLE dbo.Auctions ALTER COLUMN EndTime DATETIME NOT NULL;
                    END

                    IF COL_LENGTH('dbo.Auctions', 'Status') IS NULL
                    BEGIN
                        ALTER TABLE dbo.Auctions ADD Status NVARCHAR(20) CONSTRAINT DF_Auctions_Status DEFAULT 'active' WITH VALUES;
                        ALTER TABLE dbo.Auctions ALTER COLUMN Status NVARCHAR(20) NOT NULL;
                    END

                    -- Add Photo column for auction-specific images if missing
                    IF COL_LENGTH('dbo.Auctions', 'Photo') IS NULL
                    BEGIN
                        ALTER TABLE dbo.Auctions ADD Photo NVARCHAR(500) NULL;
                    END

                    -- Legacy columns: StartDate/EndDate (ensure defaults exist for inserts that don't set them)
                    IF COL_LENGTH('dbo.Auctions', 'StartDate') IS NOT NULL
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM sys.default_constraints dc
                            JOIN sys.columns c ON c.default_object_id = dc.object_id
                            WHERE dc.parent_object_id = OBJECT_ID('dbo.Auctions') AND c.name = 'StartDate'
                        )
                        BEGIN
                            ALTER TABLE dbo.Auctions ADD CONSTRAINT DF_Auctions_StartDate DEFAULT (GETDATE()) FOR StartDate;
                        END
                    END
                    IF COL_LENGTH('dbo.Auctions', 'EndDate') IS NOT NULL
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM sys.default_constraints dc
                            JOIN sys.columns c ON c.default_object_id = dc.object_id
                            WHERE dc.parent_object_id = OBJECT_ID('dbo.Auctions') AND c.name = 'EndDate'
                        )
                        BEGIN
                            ALTER TABLE dbo.Auctions ADD CONSTRAINT DF_Auctions_EndDate DEFAULT (DATEADD(DAY, 3, GETDATE())) FOR EndDate;
                        END
                    END
                END
                """
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _insert_auction(cur, product_id: int, starting_bid: float):
        """Insert auction row handling legacy StartDate/EndDate columns if present."""
        cur.execute("SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Auctions') AND name = 'StartDate'")
        has_startdate = cur.fetchone() is not None
        cur.execute("SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Auctions') AND name = 'EndDate'")
        has_enddate = cur.fetchone() is not None
        cur.execute("SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Auctions') AND name = 'Photo'")
        has_photo_col = cur.fetchone() is not None

        # try to use the product's current photo as the auction photo (if column exists)
        auction_photo = None
        if has_photo_col:
            cur.execute("SELECT Photo FROM Products WHERE ProductId = ?", (product_id,))
            pr = cur.fetchone()
            if pr:
                auction_photo = pr.Photo

        if has_startdate and has_enddate:
            if has_photo_col:
                cur.execute(
                    """
                    INSERT INTO Auctions (ProductId, StartingBid, CurrentBid, HighestBidderId, Photo, StartTime, EndTime, StartDate, EndDate, Status)
                    VALUES (?, ?, ?, NULL, ?, GETDATE(), DATEADD(DAY, 3, GETDATE()), GETDATE(), DATEADD(DAY, 3, GETDATE()), 'active')
                    """,
                    (product_id, starting_bid, starting_bid, auction_photo),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO Auctions (ProductId, StartingBid, CurrentBid, HighestBidderId, StartTime, EndTime, StartDate, EndDate, Status)
                    VALUES (?, ?, ?, NULL, GETDATE(), DATEADD(DAY, 3, GETDATE()), GETDATE(), DATEADD(DAY, 3, GETDATE()), 'active')
                    """,
                    (product_id, starting_bid, starting_bid),
                )
        elif has_startdate:
            if has_photo_col:
                cur.execute(
                    """
                    INSERT INTO Auctions (ProductId, StartingBid, CurrentBid, HighestBidderId, Photo, StartTime, EndTime, StartDate, Status)
                    VALUES (?, ?, ?, NULL, ?, GETDATE(), DATEADD(DAY, 3, GETDATE()), GETDATE(), 'active')
                    """,
                    (product_id, starting_bid, starting_bid, auction_photo),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO Auctions (ProductId, StartingBid, CurrentBid, HighestBidderId, StartTime, EndTime, StartDate, Status)
                    VALUES (?, ?, ?, NULL, GETDATE(), DATEADD(DAY, 3, GETDATE()), GETDATE(), 'active')
                    """,
                    (product_id, starting_bid, starting_bid),
                )
        elif has_enddate:
            if has_photo_col:
                cur.execute(
                    """
                    INSERT INTO Auctions (ProductId, StartingBid, CurrentBid, HighestBidderId, Photo, StartTime, EndTime, EndDate, Status)
                    VALUES (?, ?, ?, NULL, ?, GETDATE(), DATEADD(DAY, 3, GETDATE()), DATEADD(DAY, 3, GETDATE()), 'active')
                    """,
                    (product_id, starting_bid, starting_bid, auction_photo),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO Auctions (ProductId, StartingBid, CurrentBid, HighestBidderId, StartTime, EndTime, EndDate, Status)
                    VALUES (?, ?, ?, NULL, GETDATE(), DATEADD(DAY, 3, GETDATE()), DATEADD(DAY, 3, GETDATE()), 'active')
                    """,
                    (product_id, starting_bid, starting_bid),
                )
        else:
            if has_photo_col:
                cur.execute(
                    """
                    INSERT INTO Auctions (ProductId, StartingBid, CurrentBid, HighestBidderId, Photo, StartTime, EndTime, Status)
                    VALUES (?, ?, ?, NULL, ?, GETDATE(), DATEADD(DAY, 3, GETDATE()), 'active')
                    """,
                    (product_id, starting_bid, starting_bid, auction_photo),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO Auctions (ProductId, StartingBid, CurrentBid, HighestBidderId, StartTime, EndTime, Status)
                    VALUES (?, ?, ?, NULL, GETDATE(), DATEADD(DAY, 3, GETDATE()), 'active')
                    """,
                    (product_id, starting_bid, starting_bid),
                )

    @staticmethod
    def seed_sample_auctions(min_active: int = 4):
        """Ensure at least `min_active` active tech auctions exist (idempotent and non-duplicating)."""
        Auction._ensure_table_exists()
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            placeholders = ",".join("?" for _ in TECH_CATEGORIES)
            cur.execute(
                f"""
                SELECT COUNT(*)
                FROM Auctions a
                JOIN Products p ON p.ProductId = a.ProductId
                WHERE a.Status='active' AND a.EndTime > GETDATE()
                  AND p.Category IN ({placeholders})
                """,
                TECH_CATEGORIES,
            )
            current_cnt = int(cur.fetchone()[0] or 0)
            if current_cnt >= min_active:
                return

            need = min_active - current_cnt

            # avoid products already in active auctions
            cur.execute(
                f"""
                SELECT a.ProductId
                FROM Auctions a
                JOIN Products p ON p.ProductId = a.ProductId
                WHERE a.Status='active' AND a.EndTime > GETDATE()
                  AND p.Category IN ({placeholders})
                """,
                TECH_CATEGORIES,
            )
            existing_ids = {row.ProductId for row in cur.fetchall()}
# randomly pick tech products not already in active auctions
            not_in_clause = ''
            params = list(TECH_CATEGORIES)
            if existing_ids:
                placeholders_not = ",".join("?" for _ in existing_ids)
                not_in_clause = f" AND ProductId NOT IN ({placeholders_not})"
                params.extend(list(existing_ids))

            cur.execute(
                f"""
                SELECT TOP {need} ProductId, Price
                FROM Products
                WHERE Category IN ({placeholders})
                {not_in_clause}
                ORDER BY NEWID()
                """,
                params,
            )
            rows = cur.fetchall()
            for row in rows:
                product_id = row.ProductId
                try:
                    price = float(row.Price)
                except Exception:
                    price = 1000.0
                starting = round(max(500.0, price * 0.6), 2)
                Auction._insert_auction(cur, product_id, starting)
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_active_auctions():
        """Return list of active auctions joined with product and highest bidder info."""
        Auction._ensure_table_exists()
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            placeholders = ",".join("?" for _ in TECH_CATEGORIES)
            cur.execute(
                f"""
                SELECT a.AuctionId, a.ProductId, a.StartingBid, a.CurrentBid, a.HighestBidderId,
                       a.StartTime, a.EndTime, a.Status,
                       p.Title, p.Description, COALESCE(a.Photo, p.Photo) AS Photo,
                       u.FullName AS HighestBidder
                FROM Auctions a
                JOIN Products p ON p.ProductId = a.ProductId
                LEFT JOIN Users u ON u.UserId = a.HighestBidderId
                WHERE a.Status='active' AND a.EndTime > GETDATE()
                  AND p.Category IN ({placeholders})
                ORDER BY a.EndTime ASC
                """,
                TECH_CATEGORIES,
            )
            auctions = []
            now = datetime.now()
            for r in cur.fetchall():
                end_time = r.EndTime
                # compute time left as a friendly string
                delta = end_time - now
                if delta.total_seconds() < 0:
                    time_left = 'Ended'
                else:
                    days = delta.days
                    hours = int(delta.seconds // 3600)
                    minutes = int((delta.seconds % 3600) // 60)
                    parts = []
                    if days:
                        parts.append(f"{days}d")
                    if hours or days:
                        parts.append(f"{hours}h")
                    parts.append(f"{minutes}m")
                    time_left = ' '.join(parts)

                auctions.append({
                    'AuctionId': r.AuctionId,
                    'ProductId': r.ProductId,
                    'StartingBid': float(r.StartingBid) if r.StartingBid is not None else 0.0,
                    'CurrentBid': float(r.CurrentBid) if r.CurrentBid is not None else 0.0,
                    'HighestBidderId': r.HighestBidderId,
                    'StartTime': r.StartTime,
                    'EndTime': r.EndTime,
                    'Status': r.Status,
                    'Title': r.Title,
                    'Description': r.Description,
                    'Photo': r.Photo,
                    'HighestBidder': r.HighestBidder,
                    'TimeLeft': time_left,
                })
            return auctions
        finally:
            conn.close()

    @staticmethod
    def place_bid(auction_id: int, user_id: int, bid_amount: float):
        """Place a bid. Returns (success: bool, message: str)."""
        Auction._ensure_table_exists()
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT AuctionId, CurrentBid, StartingBid, HighestBidderId, EndTime, Status
                FROM Auctions WHERE AuctionId = ?
                """,
                (auction_id,),
            )
            row = cur.fetchone()
            if not row:
                return False, 'Auction not found.'
            if row.Status != 'active' or row.EndTime <= datetime.now():
                return False, 'This auction has ended.'

            current = float(row.CurrentBid) if row.CurrentBid is not None else 0.0
            base = current if current > 0 else float(row.StartingBid)
            min_bid = base + Auction.MIN_INCREMENT
            if bid_amount < min_bid:
                return False, f'Minimum bid is R{min_bid:.2f}.'

            cur.execute(
                "UPDATE Auctions SET CurrentBid = ?, HighestBidderId = ? WHERE AuctionId = ?",
                (bid_amount, user_id, auction_id),
            )
            conn.commit()
            return True, 'Your bid has been placed.'
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            return False, 'Error placing bid.'
        finally:
            conn.close()
