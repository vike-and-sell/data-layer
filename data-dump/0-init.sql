-- create_tables_and_insert_data.sql
CREATE EXTENSION cube;
CREATE EXTENSION earthdistance;
CREATE EXTENSION pgcrypto;

-- Create Users table
CREATE TABLE IF NOT EXISTS Users (
    user_id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    location EARTH NOT NULL,
    address TEXT NOT NULL,
    joining_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    items_sold INT[] NOT NULL DEFAULT '{}',
    items_purchased INT[] NOT NULL DEFAULT '{}'
);

-- Create Users table
CREATE TABLE IF NOT EXISTS Searches (
    user_id INT NOT NULL REFERENCES Users(user_id),
    search_text TEXT NOT NULL,
    search_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create Listings table
CREATE TABLE IF NOT EXISTS Listings (
    listing_id SERIAL PRIMARY KEY,
    seller_id INT NOT NULL REFERENCES Users(user_id),
    title VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    location EARTH NOT NULL,
    address TEXT NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('AVAILABLE', 'SOLD', 'REMOVED')),
    created_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create Chats table
CREATE TABLE IF NOT EXISTS Chats (
    chat_id SERIAL PRIMARY KEY,
    seller INT NOT NULL REFERENCES Users(user_id),
    buyer INT NOT NULL REFERENCES Users(user_id),
    listing_id INT NOT NULL REFERENCES Listings(listing_id)
);

-- Create Messages table
CREATE TABLE IF NOT EXISTS Messages (
    message_id SERIAL PRIMARY KEY,
    chat_id INT NOT NULL REFERENCES Chats(chat_id),
    sender_id INT NOT NULL REFERENCES Users(user_id),
    message_content TEXT NOT NULL,
    created_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create Listing Ratings table
CREATE TABLE IF NOT EXISTS Listing_Ratings (
    listing_rating_id SERIAL PRIMARY KEY,
    rated_listing_id INT NOT NULL REFERENCES Listings(listing_id),
    rating_user_id INT NOT NULL REFERENCES Users(user_id),
    rating_value INT NOT NULL CHECK (rating_value BETWEEN 1 AND 5),
    created_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create Listing Reviews table
CREATE TABLE IF NOT EXISTS Listing_Reviews (
    listing_review_id SERIAL PRIMARY KEY,
    reviewed_listing_id INT NOT NULL REFERENCES Listings(listing_id),
    review_user_id INT NOT NULL REFERENCES Users(user_id),
    review_content TEXT NOT NULL,
    created_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
