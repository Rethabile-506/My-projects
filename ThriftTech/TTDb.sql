-- database to create all tables for thrifttech marketplace
USE TTDb -- connect to our  database
GO 

-- clean up any existing tables before creating new ones
DROP TABLE IF EXISTS RepairServices;
DROP TABLE IF EXISTS Auctions;
DROP TABLE IF EXISTS Rentals;
DROP TABLE IF EXISTS CartItems;
DROP TABLE IF EXISTS OrderItems;
DROP TABLE IF EXISTS Orders;
DROP TABLE IF EXISTS Cart;
DROP TABLE IF EXISTS Products;
DROP TABLE IF EXISTS Users;


-- table to store user accounts and login info

CREATE TABLE Users (
    UserId INT IDENTITY(1,1) PRIMARY KEY,
    Username NVARCHAR(50) NOT NULL UNIQUE,         -- unique username for login
    Email NVARCHAR(100) NOT NULL UNIQUE,           -- email address for login and contact
    PasswordHash NVARCHAR(255) NOT NULL,           -- encrypted password for security
    FullName NVARCHAR(100),                        -- display name
    Role NVARCHAR(20) DEFAULT 'customer',          -- customer, admin, or seller permissions       
    RegistrationDate DATETIME DEFAULT GETDATE(),   -- when they joined
    LastLogin DATETIME,                             -- track user activity
    IsActive BIT DEFAULT 1                          -- can disable accounts without deleting
);


-- table for all products available on the marketplace  

CREATE TABLE Products (
    ProductId INT IDENTITY(1,1) PRIMARY KEY,
    Title NVARCHAR(100) NOT NULL,                  -- product name
    Description NVARCHAR(MAX),                     -- detailed description
    Category NVARCHAR(50),                         -- smartphones, laptops, etc                     
    Price DECIMAL(10,2) NOT NULL,                  -- sale price in rands
    Stock INT NOT NULL DEFAULT 10,                 -- how many available
    Photo NVARCHAR(500),                           -- image url or path                       
    SellerId INT,                                   -- who listed this product               
    Status NVARCHAR(20) DEFAULT 'available',       -- available, sold, or discontinued    
    Condition NVARCHAR(20) DEFAULT 'refurbished',  -- new, used, refurbished 
    DailyRate DECIMAL(10,2) NULL,                  -- rental price per day if applicable
    CreatedAt DATETIME DEFAULT GETDATE(),          -- when product was listed
    UpdatedAt DATETIME DEFAULT GETDATE(),          -- last modified date
    FOREIGN KEY (SellerId) REFERENCES Users(UserId)
);


-- CART TABLE

CREATE TABLE Cart (
    CartId INT IDENTITY(1,1) PRIMARY KEY,
    UserId INT NOT NULL,
    ProductId INT NOT NULL,
    Quantity INT DEFAULT 1,
    AddedAt DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (UserId) REFERENCES Users(UserId),
    FOREIGN KEY (ProductId) REFERENCES Products(ProductId)
);


-- ORDERS TABLE

CREATE TABLE Orders (
    OrderId INT IDENTITY(1,1) PRIMARY KEY,
    UserId INT NOT NULL,
    TotalAmount DECIMAL(10,2) NOT NULL,
    TaxAmount DECIMAL(10,2) DEFAULT 0,
    ShippingAmount DECIMAL(10,2) DEFAULT 0,
    DiscountAmount DECIMAL(10,2) DEFAULT 0,
    Status NVARCHAR(20) DEFAULT 'pending',      
    ShippingAddress NVARCHAR(MAX),
    PaymentMethod NVARCHAR(50),
    PaymentStatus NVARCHAR(20) DEFAULT 'pending',
    FOREIGN KEY (UserId) REFERENCES Users(UserId)
);


-- ORDER ITEMS TABLE

CREATE TABLE OrderItems (
    OrderItemId INT IDENTITY(1,1) PRIMARY KEY,
    OrderId INT NOT NULL,
    ProductId INT NOT NULL,
    Quantity INT NOT NULL,
    Price DECIMAL(10,2) NOT NULL,               
    Subtotal AS (Quantity * Price),             
    FOREIGN KEY (OrderId) REFERENCES Orders(OrderId),
    FOREIGN KEY (ProductId) REFERENCES Products(ProductId)
);


-- RENTAL TABLE 

CREATE TABLE Rentals (
    RentalId INT IDENTITY(1,1) PRIMARY KEY,
    ProductId INT NOT NULL,
    UserId INT NOT NULL,
    StartDate DATE NOT NULL,
    EndDate DATE NOT NULL,
    DailyRate DECIMAL(10,2) NOT NULL,
    TotalCost DECIMAL(10,2) NOT NULL,
    Status NVARCHAR(20) DEFAULT 'active',       -- active, returned, overdue
    CreatedAt DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (ProductId) REFERENCES Products(ProductId),
    FOREIGN KEY (UserId) REFERENCES Users(UserId)
);


-- AUCTIONS TABLE

CREATE TABLE Auctions (
    AuctionId INT IDENTITY(1,1) PRIMARY KEY,
    ProductId INT NOT NULL,
    StartingBid DECIMAL(10,2) NOT NULL,
    CurrentBid DECIMAL(10,2),
    HighestBidderId INT,
    StartTime DATETIME NOT NULL,
    EndTime DATETIME NOT NULL,
    Status NVARCHAR(20) DEFAULT 'active',       -- active, ended, cancelled
    CreatedAt DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (ProductId) REFERENCES Products(ProductId),
    FOREIGN KEY (HighestBidderId) REFERENCES Users(UserId)
);


-- REPAIR SERVICES TABLE

CREATE TABLE RepairServices (
    ServiceId INT IDENTITY(1,1) PRIMARY KEY,
    UserId INT NOT NULL,
    DeviceType NVARCHAR(100) NOT NULL,
    IssueDescription NVARCHAR(MAX) NOT NULL,
    EstimatedCost DECIMAL(10,2),
    Status NVARCHAR(20) DEFAULT 'submitted',    -- submitted, in_progress, completed, cancelled
    SubmittedAt DATETIME DEFAULT GETDATE(),
    CompletedAt DATETIME,
    FOREIGN KEY (UserId) REFERENCES Users(UserId)
);

-- INVOICES TABLE
CREATE TABLE Invoices (
    InvoiceId INT IDENTITY(1,1) PRIMARY KEY,
    UserId INT NOT NULL,
    OrderId INT NOT NULL,
    Total DECIMAL(10,2) NOT NULL,
    CreatedAt DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (UserId) REFERENCES Users(UserId),
    FOREIGN KEY (OrderId) REFERENCES Orders(OrderId)
);

-- LOYALTY POINTS TABLE
CREATE TABLE LoyaltyPoints (
    UserId INT PRIMARY KEY,
    Points INT DEFAULT 0,
    FOREIGN KEY (UserId) REFERENCES Users(UserId)
);

-- Insert admin user
INSERT INTO Users (Username, Email, PasswordHash, FullName, Role) VALUES 
('admin', 'admin@thrifttech.com', 'pbkdf2:sha256:260000$salt$hash', 'Administrator', 'admin');

-- Insert sample products 
INSERT INTO Products (Title, Description, Category, Price, Photo) VALUES 
('iPhone 13 Pro Refurbished', 'Excellent condition iPhone 13 Pro with 128GB storage. Fully tested and comes with warranty. Perfect for Cape Town professionals.', 'Smartphones', 11999.99, 'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=400&h=300'),
('MacBook Air M1 2020', 'Lightly used MacBook Air with M1 chip. Perfect for students at UCT, Wits, or Stellenbosch University.', 'Laptops', 15499.99, 'https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=400&h=300'),
('Canon EOS R5 Camera', 'Professional mirrorless camera in excellent condition. Great for capturing the beauty of Table Mountain and Kruger Park.', 'Cameras', 48999.99, 'https://images.unsplash.com/photo-1606983340126-99ab4feaa64a?w=400&h=300'),
('PlayStation 5 Console', 'Like-new PS5 console with controller and cables. Load shedding-tested with UPS backup included.', 'Gaming Console', 8999.99, 'https://images.unsplash.com/photo-1606144042614-b2417e99c4e3?w=400&h=300'),
('Sony WH-1000XM4 Headphones', 'Premium noise-cancelling headphones. Perfect for blocking out Joburg traffic or Cape Town wind.', 'Audio Equipment', 4299.99, 'https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=400&h=300'),
('iPad Pro 11-inch', 'Refurbished iPad Pro with Apple Pencil support. Perfect for creative work in Maboneng or Woodstock.', 'Tablets', 11199.99, 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400&h=300'),
('Samsung Galaxy S22 Ultra', 'Flagship Samsung phone with S Pen. Excellent camera for capturing Blyde River Canyon.', 'Smartphones', 15499.99, 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400&h=300'),
('Dell XPS 13 Laptop', 'Ultrabook with Intel i7 processor. Great for remote work from Camps Bay or Sandton.', 'Laptops', 20699.99, 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&h=300'),
('Nikon D850 DSLR', 'Professional DSLR camera with high resolution sensor. Perfect for wildlife photography in the Drakensberg.', 'Cameras', 39599.99, 'https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=400&h=300'),
('Xbox Series X', 'Next-gen gaming console with 4K gaming capabilities. Perfect for gaming during load shedding breaks.', 'Gaming Console', 7799.99, 'https://images.unsplash.com/photo-1621259182978-fbf93132d53d?w=400&h=300'),
('AirPods Pro 2nd Gen', 'Latest Apple AirPods with active noise cancellation. Great for commuting on the Gautrain.', 'Audio Equipment', 3449.99, 'https://images.unsplash.com/photo-1625419887199-0eefc2b3c79e?w=400&h=300'),
('Google Pixel 7 Pro', 'Google flagship phone with amazing camera AI. Perfect for capturing the sunset from Signal Hill.', 'Smartphones', 12899.99, 'https://images.unsplash.com/photo-1598300042247-d088f8ab3a91?w=400&h=300'),
('Razer Blade 15 Gaming Laptop', 'High-performance gaming laptop with RTX graphics. Perfect for eSports enthusiasts in Durban.', 'Laptops', 32799.99, 'https://images.unsplash.com/photo-1593642702821-c8da6771f0c6?w=400&h=300'),
('Fujifilm X-T4 Camera', 'Mirrorless camera with film simulation modes. Great for street photography in Bo-Kaap.', 'Cameras', 24099.99, 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=400&h=300'),
('Nintendo Switch OLED', 'Latest Nintendo Switch with vibrant OLED screen. Perfect for gaming at the Waterfront.', 'Gaming Console', 5499.99, 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&h=300'),
('Bose QuietComfort 45', 'Premium noise-cancelling headphones. Excellent for peaceful work in noisy Johannesburg offices.', 'Audio Equipment', 4819.99, 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=300'),
('Surface Pro 9', 'Microsoft 2-in-1 tablet and laptop. Includes Type Cover and Surface Pen. Great for Sandton executives.', 'Tablets', 17299.99, 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400&h=300'),
('OnePlus 11 5G', 'Flagship Android phone with fast charging. Perfect for staying connected across Mzansi.', 'Smartphones', 10349.99, 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400&h=300'),
('ASUS ROG Strix Gaming Laptop', 'Powerful gaming laptop with RGB lighting. Perfect for gaming cafes in Pretoria.', 'Laptops', 27599.99, 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=400&h=300'),
('GoPro Hero 11 Black', 'Latest action camera with 5.3K video recording. Perfect for adventure sports in the Garden Route.', 'Cameras', 6899.99, 'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=400&h=300');

-- Insert sample users 
INSERT INTO Users (Username, Email, PasswordHash, FullName, Role) VALUES 
('thabo_mthembu', 'thabo.mthembu@gmail.com', 'pbkdf2:sha256:260000$salt$hash', 'Thabo Mthembu', 'customer'),
('nomsa_dlamini', 'nomsa.dlamini@yahoo.com', 'pbkdf2:sha256:260000$salt$hash', 'Nomsa Dlamini', 'customer'),
('pieter_van_der_merwe', 'pieter.vdm@webmail.co.za', 'pbkdf2:sha256:260000$salt$hash', 'Pieter van der Merwe', 'seller'),
('zanele_khumalo', 'zanele.khumalo@outlook.com', 'pbkdf2:sha256:260000$salt$hash', 'Zanele Khumalo', 'customer'),
('johan_pretorius', 'johan.pretorius@gmail.com', 'pbkdf2:sha256:260000$salt$hash', 'Johan Pretorius', 'seller'),
('lindiwe_mahlangu', 'lindiwe.mahlangu@live.com', 'pbkdf2:sha256:260000$salt$hash', 'Lindiwe Mahlangu', 'customer'),
('andre_botha', 'andre.botha@telkomsa.net', 'pbkdf2:sha256:260000$salt$hash', 'André Botha', 'customer'),
('precious_modise', 'precious.modise@gmail.com', 'pbkdf2:sha256:260000$salt$hash', 'Precious Modise', 'customer'),
('chris_williams', 'chris.williams@capetown.gov.za', 'pbkdf2:sha256:260000$salt$hash', 'Chris Williams', 'seller'),
('fatima_abrahams', 'fatima.abrahams@uct.ac.za', 'pbkdf2:sha256:260000$salt$hash', 'Fatima Abrahams', 'customer');

-- Insert sample repair service requests
INSERT INTO RepairServices (UserId, DeviceType, IssueDescription, EstimatedCost, Status) VALUES 
(2, 'iPhone 12 Pro', 'Cracked screen needs replacement. Device still functional but screen is difficult to read. Happened after dropping at Sandton City.', 850.00, 'submitted'),
(3, 'MacBook Pro 13-inch', 'Keyboard keys are sticky and some keys not responding. Liquid spill damage from coffee incident at UCT library.', 1200.00, 'in_progress'),
(4, 'Samsung Galaxy S22', 'Battery drains very quickly, only lasts 2-3 hours with normal use. Issue started after recent software update.', 450.00, 'submitted'),
(5, 'PlayStation 5', 'Console turns off randomly during gaming sessions. Overheating issue suspected due to Johannesburg heat and load shedding.', 950.00, 'in_progress'),
(6, 'iPad Air 4th Gen', 'Touch screen not responding in certain areas. Possible digitizer issue after being dropped at Cape Town Waterfront.', 750.00, 'completed'),
(7, 'Dell XPS 13', 'Laptop won''t turn on. Power button does not respond. Charging light is working but no display or boot sequence.', 680.00, 'submitted'),
(8, 'Canon EOS R5', 'Camera lens stuck and making grinding noise when trying to focus. Error message appears on LCD screen.', 1450.00, 'in_progress'),
(9, 'AirPods Pro', 'Left earbud not working properly. No sound coming from left side, charging case also has issues.', 320.00, 'completed'),
(10, 'Nintendo Switch', 'Joy-Con drift issue on both controllers. Characters move on their own in games, affecting gameplay experience.', 285.00, 'submitted'),
(11, 'Sony WH-1000XM4', 'Noise cancellation stopped working after firmware update. Headphones work but no active noise reduction.', 540.00, 'submitted');

GO