#!/bin/bash

# if [-z "$SECRET_KEY"]; then
#     echo "SECRET_KEY not set"
#     exit 1
# fi

SQL_COMMANDS=$(cat <<EOF
-- Insert dummy data into Users table
INSERT INTO Users (username, email, password, location, address, joining_date)
VALUES
('john_doe', 'john_doe@uvic.ca', '8b053b0b4813dc1986827113c07d5edc9a206f12244e9432cb0a98419a15ab66',  ll_to_earth(34.052235,118.243683), '100 Fort St, Victoria, BC V8W 1H8', '2024-05-24T02:19:32.816610+00:00'),
('jane_smith', 'jane_smith@uvic.ca', '2edae18d7da86b00a3aaef6b2090f563c73853eb5b2e28ba1eb915268687718a',  ll_to_earth(34.052235,-118.243683), '1145 Royal Oak Dr, Victoria, BC V8X 3T7', '2024-06-25T02:19:32.816610+00:00');

-- Insert dummy data into Searches table
INSERT INTO Searches (user_id, search_text, search_date)
VALUES
(1, 'Hot Wheels', '2024-01-01'),
(1, 'iPod touch 5th Gen', '2024-01-02'),
(2, 'Lego Palpatine Lightning Hands', '2023-02-01'),
(2, 'Lego Power Miners', '2023-02-01');

-- Insert dummy data into Listings table
INSERT INTO Listings (seller_id, title, price, location, address, status)
VALUES
(1, 'Bicycle for sale', 150.00, ll_to_earth(40.730610,-73.935242), '440 Kilner St, Capital Regional District, BC V8K 2K4', 'AVAILABLE'),
(2, 'Laptop for sale', 800.00, ll_to_earth(34.052235,-118.243683), '892 Jonas Way, Chemainus, BC V0R 1K3', 'AVAILABLE');

-- Insert dummy data into Chats table
INSERT INTO Chats (seller, buyer, listing_id)
VALUES
(1, 2, 1),
(2, 1, 2);

-- Insert dummy data into Messages table
INSERT INTO Messages (chat_id, sender_id, message_content, created_on)
VALUES
(2, 1, 'Is the bicycle still available?', '2024-06-25T02:20:33.197311+00:00'),
(1, 2, 'Can you lower the price for the laptop?', '2024-06-25T02:20:48.554520+00:00');

-- Insert dummy data into Listing Ratings table
INSERT INTO Listing_Ratings (rated_listing_id, rating_user_id, rating_value, created_on)
VALUES
(1, 2, 4, '2024-06-25T02:21:02.212634+00:00'),
(2, 1, 5, '2024-06-25T02:21:13.816068+00:00');

-- Insert dummy data into Listing Reviews table
INSERT INTO Listing_Reviews (reviewed_listing_id, review_user_id, review_content, created_on)
VALUES
(1, 2, 'The bicycle was in excellent condition, very happy with the purchase!', '2024-06-25T02:21:24.104635+00:00'),
(2, 1, 'The laptop works perfectly, very satisfied!', '2024-06-25T02:21:38.067998+00:00');
EOF
)

echo "$SQL_COMMANDS" | psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"