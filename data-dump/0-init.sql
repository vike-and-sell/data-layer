-- create_tables_and_insert_data.sql
CREATE EXTENSION cube;
CREATE EXTENSION earthdistance;
CREATE EXTENSION pgcrypto;

-- Create Users table
CREATE TABLE IF NOT EXISTS Users (
    user_id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL CHECK (password ~ '^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z\d]).{8,}$'),
    location EARTH NOT NULL,
    address TEXT NOT NULL,
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
    location EARTH NOT NULL,
    address TEXT NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('AVAILABLE', 'SOLD', 'REMOVED')),
    created_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create Messages table
CREATE TABLE IF NOT EXISTS Messages (
    message_id SERIAL PRIMARY KEY,
    sender_id INT NOT NULL REFERENCES users(user_id),
    receiver_id INT NOT NULL REFERENCES users(user_id),
    listing_id INT NOT NULL REFERENCES listings(listing_id),
    message_content TEXT NOT NULL,
    created_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create Listing Ratings table
CREATE TABLE IF NOT EXISTS Listing_Ratings (
    listing_rating_id SERIAL PRIMARY KEY,
    rated_listing_id INT NOT NULL REFERENCES listings(listing_id),
    rating_user_id INT NOT NULL REFERENCES users(user_id),
    rating_value INT NOT NULL CHECK (rating_value BETWEEN 1 AND 5),
    created_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create Listing Reviews table
CREATE TABLE IF NOT EXISTS Listing_Reviews (
    listing_review_id SERIAL PRIMARY KEY,
    reviewed_listing_id INT NOT NULL REFERENCES listings(listing_id),
    review_user_id INT NOT NULL REFERENCES users(user_id),
    review_content TEXT NOT NULL,
    created_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);