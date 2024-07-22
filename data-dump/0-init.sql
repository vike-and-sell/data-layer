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
    charity BOOLEAN NOT NULL DEFAULT FALSE,
    joining_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS UsersUserIdIndex ON Users (
    user_id
);

CREATE INDEX IF NOT EXISTS UsersUsernameIndex ON Users (
    username
);

CREATE INDEX IF NOT EXISTS UsersEmailIndex ON Users (
    email
);

-- Create Searches table
CREATE TABLE IF NOT EXISTS Searches (
    user_id INT NOT NULL REFERENCES Users(user_id),
    search_text TEXT NOT NULL,
    search_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS SearchesUserIdIndex ON Searches (
    user_id
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
    for_charity BOOLEAN NOT NULL DEFAULT FALSE,
    created_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ListingsListingIdIndex ON Listings (
    listing_id
);

CREATE INDEX IF NOT EXISTS ListingsSellerIdIndex ON Listings (
    seller_id
);

-- Create Ignores table
CREATE TABLE IF NOT EXISTS Ignored (
    user_id INT NOT NULL REFERENCES Users(user_id),
    listing_id INT NOT NULL REFERENCES Listings(listing_id),
    UNIQUE (user_id, listing_id)
);

CREATE INDEX IF NOT EXISTS IgnoredUserIdIndex ON Ignored (
    user_id
);

-- Create Sales table
CREATE TABLE IF NOT EXISTS Sales (
    listing_id INT NOT NULL REFERENCES Listings(listing_id),
    buyer_id INT NOT NULL REFERENCES Users(user_id),
    sale_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS SalesListingIdIndex ON Sales (
    listing_id
);

CREATE INDEX IF NOT EXISTS SalesBuyerIdIndex ON Sales (
    buyer_id
);

-- Create Chats table
CREATE TABLE IF NOT EXISTS Chats (
    chat_id SERIAL PRIMARY KEY,
    seller INT NOT NULL REFERENCES Users(user_id),
    buyer INT NOT NULL REFERENCES Users(user_id),
    listing_id INT NOT NULL REFERENCES Listings(listing_id)
);

CREATE INDEX IF NOT EXISTS SellerBuyerIdIndex ON Chats (
    seller,
    buyer
);

-- Create Messages table
CREATE TABLE IF NOT EXISTS Messages (
    message_id SERIAL PRIMARY KEY,
    chat_id INT NOT NULL REFERENCES Chats(chat_id),
    sender_id INT NOT NULL REFERENCES Users(user_id),
    message_content TEXT NOT NULL,
    created_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ChatIdIndex ON Messages (
    chat_id
);

-- Create Listing Ratings table
CREATE TABLE IF NOT EXISTS Listing_Ratings (
    listing_rating_id SERIAL PRIMARY KEY,
    rated_listing_id INT NOT NULL REFERENCES Listings(listing_id),
    rating_user_id INT NOT NULL REFERENCES Users(user_id),
    rating_value INT NOT NULL CHECK (rating_value BETWEEN 1 AND 5),
    created_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS RatingsListingIdIndex ON Listing_Ratings (
    rated_listing_id
);

-- Create Listing Reviews table
CREATE TABLE IF NOT EXISTS Listing_Reviews (
    listing_review_id SERIAL PRIMARY KEY,
    reviewed_listing_id INT NOT NULL REFERENCES Listings(listing_id),
    review_user_id INT NOT NULL REFERENCES Users(user_id),
    review_content TEXT NOT NULL,
    created_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ReviewsListingIdIndex ON Listing_Reviews (
    reviewed_listing_id
);

-- Create Charity table
CREATE TABLE IF NOT EXISTS Charity (
    charity_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('AVAILABLE', 'CLOSED')),
    fund DECIMAL(10, 2) NOT NULL,
    logo_url TEXT NOT NULL UNIQUE,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    num_listings INT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS CharityCharityIdIndex ON Charity (
    charity_id
);
