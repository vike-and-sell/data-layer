#!/bin/bash

# if [-z "$SECRET_KEY"]; then
#     echo "SECRET_KEY not set"
#     exit 1
# fi

SQL_COMMANDS=$(cat <<EOF
-- Insert dummy data into Users table
INSERT INTO Users (username, email, password, location, address, joining_date)
VALUES
('john_doe', 'john_doe@uvic.ca', '8b053b0b4813dc1986827113c07d5edc9a206f12244e9432cb0a98419a15ab66',  ll_to_earth(34.052235,118.243683), '123 Valley Lane', '2023-01-01'),
('jane_smith', 'jane_smith@uvic.ca', '05f5d58d4146def0c5fb14f6b8161029d8c1672faf5c6c6f82164df64e2d9ca1',  ll_to_earth(34.052235,-118.243683), '842 Boniface Dr', '2023-02-01');

-- Insert dummy data into Searches table
INSERT INTO Searches (user_id, search_text, search_date)
VALUES
(1, 'Hot Wheels', '2024-01-01'),
(2, 'Palpatine Lego Lightning Hands', '2023-02-01');

-- Insert dummy data into Listings table
INSERT INTO Listings (seller_id, title, price, location, address, status)
VALUES
(1, 'Bicycle for sale', 150.00, ll_to_earth(40.730610,-73.935242), '440 Kilner St', 'AVAILABLE'),
(2, 'Laptop for sale', 800.00, ll_to_earth(34.052235,-118.243683), '892 Jonas Ave', 'AVAILABLE');

-- Insert dummy data into Chats table
INSERT INTO Chats (seller, buyer, listing_id)
VALUES
(1, 2, 1),
(2, 1, 2);

-- Insert dummy data into Messages table
INSERT INTO Messages (chat_id, sender_id, message_content, created_on)
VALUES
(2, 1, 'Is the bicycle still available?', '2023-03-02 10:00:00'),
(1, 2, 'Can you lower the price for the laptop?', '2023-04-02 15:30:00');

-- Insert dummy data into Listing Ratings table
INSERT INTO Listing_Ratings (rated_listing_id, rating_user_id, rating_value, created_on)
VALUES
(1, 2, 4, '2023-03-03 12:00:00'),
(2, 1, 5, '2023-04-03 17:45:00');

-- Insert dummy data into Listing Reviews table
INSERT INTO Listing_Reviews (reviewed_listing_id, review_user_id, review_content, created_on)
VALUES
(1, 2, 'The bicycle was in excellent condition, very happy with the purchase!', '2023-03-03 12:05:00'),
(2, 1, 'The laptop works perfectly, very satisfied!', '2023-04-03 17:50:00');
EOF
)

echo "$SQL_COMMANDS" | psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"