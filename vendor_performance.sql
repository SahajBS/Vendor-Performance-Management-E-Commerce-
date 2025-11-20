-- ==========================================
-- 🚀 DATABASE: Vendor Performance Management (FINAL VERSION)
-- ==========================================

DROP DATABASE IF EXISTS vendor_performance_db;
CREATE DATABASE vendor_performance_db;
USE vendor_performance_db;

-- =====================
-- 1️⃣ Vendor Table
-- =====================
CREATE TABLE Vendor (
    Vendor_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    Password VARCHAR(100) NOT NULL,
    Contact_No VARCHAR(15) CHECK (Contact_No REGEXP '^[0-9]{10,15}$'),
    Business_Type ENUM('Electronics','Clothing','Grocery','Books','Home','Others') DEFAULT 'Others',
    Avg_Review_Rating DECIMAL(3,2) DEFAULT 0.00 CHECK (Avg_Review_Rating BETWEEN 0 AND 5),
    Customer_Satisfaction_Rate DECIMAL(5,2) DEFAULT 0.00 CHECK (Customer_Satisfaction_Rate BETWEEN 0 AND 100),
    Registration_Date DATE DEFAULT (CURRENT_DATE),
    Last_Evaluation_Date DATE DEFAULT NULL,
    Last_Feedback_Date DATE DEFAULT NULL,
    Performance_Score DECIMAL(5,2) DEFAULT 0.00 CHECK (Performance_Score BETWEEN 0 AND 100),
    Vendor_Status ENUM('Active','Inactive','Suspended') DEFAULT 'Active'
);

-- =====================
-- 2️⃣ Product Table
-- =====================
CREATE TABLE Product (
    Product_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Description TEXT,
    Price DECIMAL(10,2) NOT NULL CHECK (Price > 0),
    Stock INT DEFAULT 0 CHECK (Stock >= 0),
    Category ENUM('Electronics','Clothing','Grocery','Books','Home','Others') DEFAULT 'Others',
    Vendor_ID INT NOT NULL,
    FOREIGN KEY (Vendor_ID) REFERENCES Vendor(Vendor_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    UNIQUE (Vendor_ID, Name)
);

-- =====================
-- 3️⃣ Customer Table
-- =====================
CREATE TABLE Customer (
    Customer_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    Password VARCHAR(100) NOT NULL,
    Phone VARCHAR(15) CHECK (Phone REGEXP '^[0-9]{10,15}$'),
    Address VARCHAR(255),
    Gender ENUM('Male','Female','Other') DEFAULT 'Other',
    Registration_Date DATE DEFAULT (CURRENT_DATE),
    Loyalty_Points INT DEFAULT 0 CHECK (Loyalty_Points >= 0)
);

-- =====================
-- 4️⃣ Orders Table (NO Delivery_Date)
-- =====================
CREATE TABLE Orders (
    Order_ID INT AUTO_INCREMENT PRIMARY KEY,
    Customer_ID INT NOT NULL,
    Product_ID INT NOT NULL,
    Quantity INT DEFAULT 1 CHECK (Quantity > 0),
    Status ENUM('Pending','Processing','Shipped','Delivered','Cancelled') DEFAULT 'Pending',
    Order_Date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Customer_ID) REFERENCES Customer(Customer_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (Product_ID) REFERENCES Product(Product_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- =====================
-- 5️⃣ Payment Table
-- =====================
CREATE TABLE Payment (
    Payment_ID INT AUTO_INCREMENT PRIMARY KEY,
    Order_ID INT NOT NULL,
    Customer_ID INT NOT NULL,
    Payment_Method ENUM('Credit Card','Debit Card','UPI','NetBanking','Cash','Wallet') NOT NULL,
    Payment_Status ENUM('Pending','Completed','Failed','Refunded') DEFAULT 'Pending',
    Amount DECIMAL(10,2) NOT NULL CHECK (Amount >= 0),
    Currency CHAR(3) DEFAULT 'INR',
    Payment_Date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Order_ID) REFERENCES Orders(Order_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (Customer_ID) REFERENCES Customer(Customer_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    UNIQUE (Order_ID, Payment_Method)
);

-- =====================
-- 6️⃣ Review Table
-- =====================
CREATE TABLE Review (
    Review_ID INT AUTO_INCREMENT PRIMARY KEY,
    Customer_ID INT NOT NULL,
    Vendor_ID INT NOT NULL,
    Product_ID INT NOT NULL,
    Comment TEXT,
    Rating INT CHECK (Rating BETWEEN 1 AND 5),
    Review_Date DATETIME DEFAULT CURRENT_TIMESTAMP,
    Sentiment ENUM('Positive','Neutral','Negative') DEFAULT 'Neutral',
    FOREIGN KEY (Customer_ID) REFERENCES Customer(Customer_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (Vendor_ID) REFERENCES Vendor(Vendor_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (Product_ID) REFERENCES Product(Product_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    UNIQUE (Customer_ID, Product_ID)
);

-- =====================
-- 7️⃣ Vendor Performance Table
-- =====================
CREATE TABLE Vendor_Performance (
    Performance_ID INT AUTO_INCREMENT PRIMARY KEY,
    Vendor_ID INT NOT NULL,
    Avg_Review_Rating DECIMAL(3,2) DEFAULT 0.00 CHECK (Avg_Review_Rating BETWEEN 0 AND 5),
    Customer_Satisfaction_Rate DECIMAL(5,2) DEFAULT 0.00 CHECK (Customer_Satisfaction_Rate BETWEEN 0 AND 100),
    Last_Feedback_Date DATE,
    Performance_Score DECIMAL(5,2) DEFAULT 0.00 CHECK (Performance_Score BETWEEN 0 AND 100),
    Updated_By VARCHAR(100) DEFAULT 'System',
    FOREIGN KEY (Vendor_ID) REFERENCES Vendor(Vendor_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    UNIQUE (Vendor_ID, Last_Feedback_Date)
);

-- =====================
-- 8️⃣ Audit Log Table
-- =====================
CREATE TABLE Audit_Log (
    Log_ID INT AUTO_INCREMENT PRIMARY KEY,
    Table_Name VARCHAR(100),
    Operation ENUM('INSERT','UPDATE','DELETE'),
    Record_ID INT,
    User_Executed VARCHAR(100),
    Operation_Time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =====================
-- 9️⃣ Admin Table
-- =====================
CREATE TABLE Admin (
    Admin_ID INT AUTO_INCREMENT PRIMARY KEY,
    Username VARCHAR(100) UNIQUE NOT NULL,
    Password VARCHAR(100) NOT NULL
);

INSERT INTO Admin (Username, Password) VALUES ('admin', 'admin123');

-- =========================================
-- ⚡ TRIGGERS
-- =========================================
DELIMITER //

-- 🔸 Update vendor rating safely (no recursion)
CREATE TRIGGER trg_update_vendor_rating
AFTER INSERT ON Review
FOR EACH ROW
BEGIN
    DECLARE new_avg DECIMAL(3,2);
    DECLARE satisfaction_rate DECIMAL(5,2);
    DECLARE positive_count INT;
    DECLARE total_count INT;
    
    SET new_avg = (SELECT AVG(Rating) FROM Review WHERE Vendor_ID = NEW.Vendor_ID);
    
    -- Calculate satisfaction rate as percentage of positive reviews (rating >= 4 or sentiment = 'Positive')
    SET total_count = (SELECT COUNT(*) FROM Review WHERE Vendor_ID = NEW.Vendor_ID);
    SET positive_count = (SELECT COUNT(*) FROM Review WHERE Vendor_ID = NEW.Vendor_ID AND (Rating >= 4 OR Sentiment = 'Positive'));
    
    IF total_count > 0 THEN
        SET satisfaction_rate = (positive_count * 100.0 / total_count);
    ELSE
        SET satisfaction_rate = 0.00;   
    END IF;
    
    UPDATE Vendor
    SET Avg_Review_Rating = new_avg,
        Customer_Satisfaction_Rate = satisfaction_rate,
        Last_Feedback_Date = CURRENT_DATE
    WHERE Vendor_ID = NEW.Vendor_ID;

    INSERT INTO Vendor_Performance (Vendor_ID, Avg_Review_Rating, Customer_Satisfaction_Rate, Last_Feedback_Date)
    VALUES (NEW.Vendor_ID, new_avg, satisfaction_rate, CURRENT_DATE)
    ON DUPLICATE KEY UPDATE
        Avg_Review_Rating = new_avg,
        Customer_Satisfaction_Rate = satisfaction_rate,
        Last_Feedback_Date = CURRENT_DATE;
END;
//

-- 🔸 Reduce stock after an order
CREATE TRIGGER trg_reduce_stock
AFTER INSERT ON Orders
FOR EACH ROW
BEGIN
    UPDATE Product
    SET Stock = GREATEST(Stock - NEW.Quantity, 0)
    WHERE Product_ID = NEW.Product_ID;
END;
//

-- 🔸 Log vendor insertions
CREATE TRIGGER trg_audit_insert_vendor
AFTER INSERT ON Vendor
FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (Table_Name, Operation, Record_ID, User_Executed)
    VALUES ('Vendor', 'INSERT', NEW.Vendor_ID, CURRENT_USER());
END;
//

DELIMITER ;

-- =========================================
-- ⚙ FUNCTIONS
-- =========================================
DELIMITER //

-- Calculate vendor total sales
CREATE FUNCTION fn_total_sales(vendorId INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE total DECIMAL(10,2);
    SET total = (
        SELECT IFNULL(SUM(P.Amount),0)
        FROM Payment P
        JOIN Orders O ON O.Order_ID = P.Order_ID
        JOIN Product PR ON PR.Product_ID = O.Product_ID
        WHERE PR.Vendor_ID = vendorId AND P.Payment_Status='Completed'
    );
    RETURN total;
END;
//

DELIMITER ;

-- =========================================
-- 🧩 PROCEDURES
-- =========================================
DELIMITER //

-- Evaluate vendor and store in performance table
CREATE PROCEDURE sp_evaluate_vendor(IN vendorId INT)
BEGIN
    DECLARE score DECIMAL(5,2);
    DECLARE satisfaction_rate DECIMAL(5,2);
    DECLARE positive_count INT;
    DECLARE total_count INT;
    
    -- Calculate performance score
    SET score = fn_calculate_performance(vendorId);
    
    UPDATE Vendor
    SET Performance_Score = score,
        Last_Evaluation_Date = CURRENT_DATE
    WHERE Vendor_ID = vendorId;

    INSERT INTO Vendor_Performance(Vendor_ID, Performance_Score, Customer_Satisfaction_Rate, Last_Feedback_Date)
    VALUES (vendorId, score, satisfaction_rate, CURRENT_DATE)
    ON DUPLICATE KEY UPDATE
        Performance_Score = score,
        Customer_Satisfaction_Rate = satisfaction_rate,
        Last_Feedback_Date = CURRENT_DATE;
END;
//

-- Generate vendor leaderboard report
CREATE PROCEDURE sp_vendor_report()
BEGIN
    SELECT v.Vendor_ID, v.Name, v.Business_Type, v.Performance_Score,
           fn_total_sales(v.Vendor_ID) AS Total_Sales
    FROM Vendor v
    ORDER BY Performance_Score DESC;
END;
//

DELIMITER ;
