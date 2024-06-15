-- create_tables_and_insert_data.sql


-- Create Users table
CREATE TABLE IF NOT EXISTS Users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(20) NOT NULL CHECK (username ~ '^[a-zA-Z0-9_@]{6,20}$'),
    email VARCHAR(100) NOT NULL CHECK (email ~ '^[^@]+@uvic\.ca$'),
    password VARCHAR(100) NOT NULL CHECK (password ~ '^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z\d]).{8,}$'),
    location VARCHAR(100) NOT NULL,
    joining_date DATE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    items_sold INT[] NOT NULL DEFAULT '{}',
    items_purchased INT[] NOT NULL DEFAULT '{}'
);

-- Create Listings table
CREATE TABLE IF NOT EXISTS Listings (
    listing_id SERIAL PRIMARY KEY,
    seller_id INT NOT NULL REFERENCES users(user_id),
    title VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    location VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('available', 'sold', 'removed')),
    listed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create Messages table
CREATE TABLE IF NOT EXISTS Messages (
    message_id SERIAL PRIMARY KEY,
    sender_id INT NOT NULL REFERENCES users(user_id),
    receiver_id INT NOT NULL REFERENCES users(user_id),
    listing_id INT NOT NULL REFERENCES listings(listing_id),
    message_content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create Listing Ratings table
CREATE TABLE IF NOT EXISTS Listing_Ratings (
    listing_rating_id SERIAL PRIMARY KEY,
    rated_listing_id INT NOT NULL REFERENCES listings(listing_id),
    rating_user_id INT NOT NULL REFERENCES users(user_id),
    rating_value INT NOT NULL CHECK (rating_value BETWEEN 1 AND 5),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create Listing Reviews table
CREATE TABLE IF NOT EXISTS Listing_Reviews (
    listing_review_id SERIAL PRIMARY KEY,
    reviewed_listing_id INT NOT NULL REFERENCES listings(listing_id),
    review_user_id INT NOT NULL REFERENCES users(user_id),
    review_content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insert dummy data into Users table
INSERT INTO Users (username, email, password, location, joining_date)
VALUES
('john_doe', 'john_doe@uvic.ca', 'Password123!', '100N,200W', '2023-01-01'),
('jane_smith', 'jane_smith@uvic.ca', 'SecurePass1$', '123N,300W', '2023-02-01');

-- Insert dummy data into Listings table
INSERT INTO Listings (seller_id, title, price, location, status)
VALUES
(1, 'Bicycle for sale', 150.00, '100N,150W', 'available'),
(2, 'Laptop for sale', 800.00, '123N,456W', 'available');

-- Insert dummy data into Messages table
INSERT INTO Messages (sender_id, receiver_id, listing_id, message_content, timestamp)
VALUES
(1, 2, 1, 'Is the bicycle still available?', '2023-03-02 10:00:00'),
(2, 1, 2, 'Can you lower the price for the laptop?', '2023-04-02 15:30:00');

-- Insert dummy data into Listing Ratings table
INSERT INTO Listing_Ratings (rated_listing_id, rating_user_id, rating_value, timestamp)
VALUES
(1, 2, 4, '2023-03-03 12:00:00'),
(2, 1, 5, '2023-04-03 17:45:00');

-- Insert dummy data into Listing Reviews table
INSERT INTO Listing_Reviews (reviewed_listing_id, review_user_id, review_content, timestamp)
VALUES
(1, 2, 'The bicycle was in excellent condition, very happy with the purchase!', '2023-03-03 12:05:00'),
(2, 1, 'The laptop works perfectly, very satisfied!', '2023-04-03 17:50:00');
