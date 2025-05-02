-- Question: What are the tables created in this project?
-- Query: Create the `users` table to store user information.
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    user_type ENUM('buyer', 'seller') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Query: Create the `auctions` table to store auction details.
CREATE TABLE auctions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    starting_price DECIMAL(10, 2) NOT NULL,
    end_time DATETIME NOT NULL,
    seller_id INT NOT NULL,
    image_path VARCHAR(255),
    FOREIGN KEY (seller_id) REFERENCES users(id)
);

-- Query: Create the `bids` table to store bid details.
CREATE TABLE bids (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    item_id INT NOT NULL,
    bid_amount DECIMAL(10, 2) NOT NULL,
    bid_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (item_id) REFERENCES auctions(id)
);

-- Query: Create the `item_requests` table to store buyer requests.
CREATE TABLE item_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    buyer_id INT NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    budget DECIMAL(10, 2) NOT NULL,
    status ENUM('Pending', 'Matched') DEFAULT 'Pending',
    seller_id INT DEFAULT NULL,
    FOREIGN KEY (buyer_id) REFERENCES users(id),
    FOREIGN KEY (seller_id) REFERENCES users(id)
);

-- Query: Create the `feedback` table to store feedback for users.
CREATE TABLE feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reviewer_id INT NOT NULL,
    reviewed_user_id INT NOT NULL,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    review TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reviewer_id) REFERENCES users(id),
    FOREIGN KEY (reviewed_user_id) REFERENCES users(id)
);

-- Question: What are the queries used to insert data into the tables?
-- Query: Insert sample data into the `users` table.
INSERT INTO users (username, email, password, user_type)
VALUES 
('JohnDoe', 'john@example.com', 'hashed_password_1', 'buyer'),
('JaneSmith', 'jane@example.com', 'hashed_password_2', 'seller');

-- Query: Insert sample data into the `auctions` table.
INSERT INTO auctions (title, description, starting_price, end_time, seller_id, image_path)
VALUES 
('Auction Title', 'Auction Description', 1000.00, '2025-05-01 11:27:00', 2, 'uploads/image.jpg'),
('Vintage Clock', 'A beautiful vintage clock from the 19th century.', 500.00, '2025-12-31 23:59:59', 2, 'uploads/vintage_clock.jpg');

-- Query: Insert sample data into the `bids` table.
INSERT INTO bids (user_id, item_id, bid_amount)
VALUES 
(1, 1, 1100.00),
(1, 2, 600.00);

-- Query: Insert sample data into the `item_requests` table.
INSERT INTO item_requests (buyer_id, item_name, description, budget, status)
VALUES 
(1, 'Antique Vase', 'Looking for a rare antique vase.', 2000.00, 'Pending'),
(1, 'Wooden Chair', 'Need a handcrafted wooden chair.', 1500.00, 'Matched');

-- Query: Insert sample data into the `feedback` table.
INSERT INTO feedback (reviewer_id, reviewed_user_id, rating, review)
VALUES 
(1, 2, 5, 'Excellent seller!'),
(2, 1, 4, 'Great buyer, smooth transaction.');

-- Question: What are the queries used to update or modify data in the tables?
-- Query: Update the status of a request in the `item_requests` table.
UPDATE item_requests
SET status = 'Matched', seller_id = 2
WHERE id = 1;

-- Query: Update the highest bid in the `bids` table.
UPDATE bids
SET bid_amount = 1200.00
WHERE id = 1;

-- Question: What are the queries used to delete data from the tables?
-- Query: Delete a request from the `item_requests` table.
DELETE FROM item_requests
WHERE id = 2;

-- Query: Delete an auction from the `auctions` table.
DELETE FROM auctions
WHERE id = 1;

-- Question: What are the queries used to fetch data from the tables?
-- Query: Fetch all active auctions.
SELECT * FROM auctions
WHERE end_time > NOW();

-- Query: Fetch all bids for a specific auction.
SELECT b.bid_amount, b.bid_time, u.username
FROM bids b
JOIN users u ON b.user_id = u.id
WHERE b.item_id = 1
ORDER BY b.bid_amount DESC;

-- Query: Fetch all requests for a specific buyer.
SELECT * FROM item_requests
WHERE buyer_id = 1;

-- Query: Fetch feedback for a specific user.
SELECT * FROM feedback
WHERE reviewed_user_id = 2;
