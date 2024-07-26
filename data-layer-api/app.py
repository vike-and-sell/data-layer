from flask import Flask, request, jsonify, Response
import os
from utils import format_result
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://{username}:{password}@{host}:{port}/{database}'.format(
    username=os.environ['RDS_USERNAME'],
    password=os.environ['RDS_PASSWORD'],
    host=os.environ['RDS_HOSTNAME'],
    port=os.environ['RDS_PORT'],
    database=os.environ['RDS_DB_NAME'],
)

# Configuration for secondary (read) database
app.config['SQLALCHEMY_BINDS'] = {
    'read_replica': 'postgresql://{username}:{password}@{replica_host}:{port}/{database}'.format(
        username=os.environ['RDS_USERNAME'],
        password=os.environ['RDS_PASSWORD'],
        replica_host=os.environ['RDS_HOSTNAME-REPLICA'],
        port=os.environ['RDS_PORT'],
        database=os.environ['RDS_DB_NAME']
    )
}

engine_w = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
engine_r = create_engine(app.config['SQLALCHEMY_BINDS']['read_replica'])

app.config['DEBUG'] = True

ENCRYPTION_KEY = os.environ['ENCRYPTION_KEY']
API_KEY = os.environ['API_KEY']


@app.before_request
def check_api_key():
    api_key = request.headers.get("X-Api-Key")
    if api_key != API_KEY:
        return Response(status=401)


@app.route('/', methods=['GET'])
def welcome():
    return "Hello World"


@app.route('/dump_users', methods=['GET'])
def dump_users():
    with engine_r.connect() as connection:
        try:
            result = connection.execute(text("SELECT * FROM Users"))
            connection.commit()
            row = result.fetchall()
            return Response(str(row), status=200)
        except:
            return Response(status=500)


@app.route('/dump_listings', methods=['GET'])
def dump_listings():
    with engine_r.connect() as connection:
        try:
            result = connection.execute(text("SELECT * FROM Listings"))
            connection.commit()
            row = result.fetchall()
            return Response(str(row), status=200)
        except:
            return Response(status=500)


@app.post('/make_user')
def make_user():
    email = request.json.get('email')
    username = request.json.get('username')
    password = request.json.get('password')
    address = request.json.get('address')
    location = request.json.get('location')
    lat = location["lat"]
    lng = location["lng"]
    join_date = request.json.get('join_date')

    with engine_w.connect() as connection:
        try:
            result = connection.execute(text(
                "INSERT INTO Users (username, email, password, location, address, joining_date) VALUES (:usrname, :e_mail, :passwd, ll_to_earth(:lat, :lng), :addr, :joinDate) RETURNING user_id"),
                {"usrname": username, "e_mail": email, "passwd": password,
                    "lat": lat, "lng": lng, "addr": address, "joinDate": join_date}
            )
            connection.commit()
            row = result.fetchone()
            if row:
                return jsonify(format_result(['user_id'], [row])), 200
        except IntegrityError as e:
            connection.rollback()
            return jsonify({}), 400
        except:
            connection.rollback()
            return jsonify({'message': 'Something went wrong'}), 500
        return jsonify({}), 500


@app.get('/get_user_info_for_login')
def get_user_for_login():
    username = request.args.get('usr')
    with engine_r.connect() as connection:
        try:
            result = connection.execute(text(
                "SELECT user_id, password FROM Users WHERE username = :usrname"), {"usrname": username})
        except IntegrityError:
            return jsonify({}), 400
        except:
            return jsonify({}), 500
        row = result.fetchone()
        if (row):
            return jsonify(format_result(['user_id', 'password'], [row])), 200
        return jsonify({}), 404


@app.get('/get_user_by_email')
def get_user_by_email():
    email = request.args.get('eml')
    with engine_r.connect() as connection:
        try:
            result = connection.execute(text(
                "SELECT user_id, username FROM Users WHERE email = :e_mail"), {"e_mail": email})
            connection.commit()
            row = result.fetchone()
            print(row)
            if row:
                return jsonify(format_result(['user_id', 'username'], [row]))
        except Exception as e:
            print(e)

        return jsonify({}), 400


@app.post('/update_user_password')
def update_user_password():
    user_id = request.json.get('user_id')
    password = request.json.get('password')

    with engine_w.connect() as connection:
        try:
            connection.execute(text("UPDATE Users SET password = :passwd WHERE user_id = :uID"), {
                               "passwd": password, "uID": user_id})
            connection.commit()
            return jsonify({}), 200
        except Exception as e:
            print(e)

        return jsonify({}), 400


@app.post('/create_rating')
def create_rating():
    listing_id = request.json.get('listingId')
    user_id = request.json.get('userId')
    rating_value = request.json.get('rating')

    with engine_w.connect() as connection:
        try:
            result = connection.execute(
                text("INSERT INTO Listing_Ratings (rated_listing_id, rating_user_id, rating_value) VALUES (:listing_id, :usr_id, :value) RETURNING listing_rating_id, created_on"),
                {"listing_id": listing_id, "usr_id": user_id, "value": rating_value}
            )
            connection.commit()
            row = result.fetchone()
            if row:
                return jsonify(format_result(['rating_id', 'created_on'], [row])), 200
            connection.rollback()
            return jsonify({'message': 'Something went wrong'}), 500
        except IntegrityError as e:
            connection.rollback()
            if e.orig.pgcode == '23503':
                return jsonify({'message': 'Listing not found'}), 404
            else:
                return jsonify({}), 400
        except:
            connection.rollback()
            return jsonify({'message': 'Something went wrong'}), 500


@app.get('/get_ratings')
def get_ratings():
    listing_id = request.args.get('listingId')
    if not listing_id:
        return jsonify({}), 400

    with engine_r.connect() as connection:
        try:
            result = connection.execute(
                text("SELECT username, rating_value, created_on FROM Listing_Ratings JOIN Users on Listing_Ratings.rating_user_id = Users.user_id WHERE rated_listing_id = :listing_id"),
                {"listing_id": listing_id}
            )
        except IntegrityError:
            return jsonify({}), 400
        except:
            return jsonify({}), 500
        rows = result.fetchall()
        return jsonify(format_result(['username', 'rating', 'created_on'], rows, True)), 200


@app.post('/create_review')
def create_review():
    listing_id = request.json.get('listingId')
    user_id = request.json.get('userId')
    review_content = request.json.get('review')

    with engine_w.connect() as connection:
        try:
            result = connection.execute(
                text("INSERT INTO Listing_Reviews (reviewed_listing_id, review_user_id, review_content) VALUES (:listing_id, :usr_id, :content) RETURNING listing_review_id, reviewed_listing_id, created_on"),
                {"listing_id": listing_id, "usr_id": user_id,
                    "content": review_content}
            )
            connection.commit()
            row = result.fetchone()
            if row:
                return jsonify(format_result(['review_id', 'listing_id', 'created_on'], [row])), 200
            connection.rollback()
            return jsonify({'message': 'Something went wrong'}), 500
        except IntegrityError as e:
            connection.rollback()
            if e.orig.pgcode == '23503':
                return jsonify({'message': 'Listing not found'}), 404
            else:
                return jsonify({}), 400
        except:
            connection.rollback()
            return jsonify({'message': 'Something went wrong'}), 500


@app.get('/get_reviews')
def get_reviews():
    listing_id = request.args.get('listingId')
    if not listing_id:
        return jsonify({}), 400

    with engine_r.connect() as connection:
        try:
            result = connection.execute(
                text("SELECT username, review_content, created_on FROM Listing_Reviews JOIN Users on Listing_Reviews.review_user_id = Users.user_id WHERE reviewed_listing_id = :listing_id"),
                {"listing_id": listing_id}
            )
        except IntegrityError:
            return jsonify({}), 400
        except:
            return jsonify({}), 500
        rows = result.fetchall()
        return jsonify(format_result(['username', 'review', 'created_on'], rows, True)), 200


@app.get('/get_user')
def get_user():
    user_id = request.args.get('userId')

    with engine_r.connect() as connection:
        try:
            result = connection.execute(text(
                "SELECT username, address, joining_date, charity FROM Users WHERE user_id = :usr_id"), {"usr_id": user_id})
        except IntegrityError:
            return jsonify({}), 400
        except:
            return jsonify({}), 500
        row = result.fetchone()
        if row:
            return jsonify({
                "username": row[0],
                "address": row[1],
                "joining_date": row[2].isoformat(),
                "charity": row[3]
            }), 200
        return jsonify({}), 404


@app.get('/get_user_purchases')
def get_user_purchases():
    user_id = request.args.get('userId')

    with engine_r.connect() as connection:
        try:
            result = connection.execute(text(
                "SELECT listing_id FROM Sales WHERE buyer_id = :usr_id"), {"usr_id": user_id})
            rows = result.fetchall()
            if rows:
                print(rows[0])
                return jsonify([x[0] for x in rows]), 200
            else:
                return jsonify({}), 200
        except IntegrityError:
            return jsonify({}), 400
        except Exception as e:
            print(f"unknown exception {e}")

    return jsonify({}), 500


@app.get('/get_user_sales')
def get_user_sales():
    user_id = request.args.get('userId')

    with engine_r.connect() as connection:
        try:
            result = connection.execute(text(
                "SELECT Sales.listing_id FROM Sales JOIN Listings ON Sales.listing_id = Listings.listing_id WHERE seller_id = :usr_id"), {"usr_id": user_id})
            rows = result.fetchall()
            if rows:
                return jsonify([x[0] for x in rows]), 200
            else:
                return jsonify([]), 200
        except IntegrityError:
            return jsonify({}), 400


@app.post('/update_user')
def update_user():
    user_id = request.json.get('userId')
    address = request.json.get('address')
    location = request.json.get('location')
    charity = request.json.get('charity')

    with engine_w.connect() as connection:
        try:
            connection.execute(
                text(
                    "UPDATE Users SET address = :addr, location = ll_to_earth(:lat, :lng), charity = :charity WHERE user_id = :usr_id"),
                {"addr": address, "lat": location["lat"],
                    "lng": location["lng"], "usr_id": user_id,
                    "charity": charity}
            )
            connection.commit()
        except IntegrityError:
            connection.rollback()
            return jsonify({}), 400
        except:
            connection.rollback()
            return jsonify({}), 500
        return jsonify({}), 200


@app.get('/get_listings')
def get_listings():
    max_price = request.args.get('maxPrice', 99999999)
    min_price = request.args.get('minPrice', 0)
    status = request.args.get('status', 'AVAILABLE')
    sort_by = request.args.get('sortBy', 'created_on')
    is_descending = request.args.get('isDescending', False)

    with engine_r.connect() as connection:
        try:
            if not is_descending:
                result = connection.execute(
                    text(f"SELECT listing_id, seller_id, title, price, address, status, charity, created_on, last_updated_at FROM Listings WHERE price < :max_price AND price > :min_price AND status = :l_status ORDER BY {
                         sort_by}"),
                    {"max_price": max_price, "min_price": min_price,
                        "l_status": status}
                )
            else:
                result = connection.execute(
                    text(f"SELECT listing_id, seller_id, title, price, address, status, charity, created_on, last_updated_at FROM Listings WHERE price < :max_price AND price > :min_price AND status = :l_status ORDER BY {
                         sort_by} DESC"),
                    {"max_price": max_price, "min_price": min_price,
                        "l_status": status}
                )
        except IntegrityError:
            return jsonify({}), 400
        except:
            return jsonify({}), 500
        rows = result.fetchall()
        if (rows):
            return jsonify(format_result(['listingId', 'sellerId', 'title', 'price', 'address', 'status', 'charity', 'listedAt', 'lastUpdatedAt'], rows, True)), 200
        return jsonify({}), 404


@app.get('/get_listing')
def get_listing():
    listing_id = request.args.get('listingId')

    with engine_r.connect() as connection:
        try:
            result = connection.execute(text(
                "SELECT listing_id, seller_id, title, price, address, status, charity, created_on, last_updated_at FROM Listings WHERE listing_id = :l_id"), {"l_id": listing_id})
        except IntegrityError:
            return jsonify({}), 400
        except:
            return jsonify({}), 500
        rows = result.fetchall()
        if (rows):
            return jsonify(format_result(['listingId', 'sellerId', 'title', 'price', 'address', 'status', 'charity', 'listedAt', 'lastUpdatedAt'], rows)), 200
        return jsonify({}), 404


@app.get('/get_listing_by_seller')
def get_listing_by_seller():
    user_id = request.args.get('userId')

    with engine_r.connect() as connection:
        try:
            result = connection.execute(text(
                "SELECT listing_id, seller_id, title, price, address, status, charity, created_on, last_updated_at FROM Listings WHERE seller_id = :usr_id"), {"usr_id": user_id})
        except IntegrityError:
            return jsonify({}), 400
        except:
            return jsonify({}), 500
        rows = result.fetchall()
        if (rows):
            return jsonify(format_result(['listingId', 'sellerId', 'title', 'price', 'address', 'status', 'charity', 'listedAt', 'lastUpdatedAt'], rows)), 200
        return jsonify({}), 404


@app.post('/create_listing')
def create_listing():
    seller_id = request.json.get('sellerId')
    title = request.json.get('title')
    price = request.json.get('price')
    address = request.json.get('address')
    status = request.json.get('status')
    latitude = request.json.get('latitude')
    longitude = request.json.get('longitude')
    charity = request.json.get('charity')

    with engine_w.connect() as connection:
        try:
            if charity:
                result = connection.execute(
                    text("INSERT INTO Listings (seller_id, title, price, address, location, status, charity) VALUES (:sllr_id, :l_title, :l_price, :addr, ll_to_earth(:lat, :lng), :l_status, :charity) RETURNING listing_id, title, price, address, status, charity"),
                    {"sllr_id": seller_id, "l_title": title, "l_price": price,
                        "addr": address, "lat": latitude, "lng": longitude, "l_status": status, "charity": charity}
                )
            else:
                result = connection.execute(
                    text("INSERT INTO Listings (seller_id, title, price, address, location, status) VALUES (:sllr_id, :l_title, :l_price, :addr, ll_to_earth(:lat, :lng), :l_status) RETURNING listing_id, title, price, address, status, charity"),
                    {"sllr_id": seller_id, "l_title": title, "l_price": price,
                        "addr": address, "lat": latitude, "lng": longitude, "l_status": status}
                )
            connection.commit()
        except IntegrityError as e:
            connection.rollback()
            if e.orig.pgcode == '23503':
                return jsonify({'message': 'Listing not found'}), 404
            else:
                return jsonify({}), 400
        except:
            connection.rollback()
            return jsonify({'message': 'Something went wrong'}), 500

        row = result.fetchall()
        return jsonify(format_result(['listingId', 'title', 'price', 'address', 'status', 'charity'], row)), 201


@app.post('/create_sale')
def create_sale():
    listing_id = request.json.get('listingId')
    buyer_username = request.json.get('buyerUsername')
    with engine_w.connect() as connection:
        try:
            result = connection.execute(text("SELECT user_id from Users WHERE username = :username"), {
                "username": buyer_username})
            row = result.fetchone()
            if row:
                connection.execute(text("INSERT INTO Sales (listing_id, buyer_id) VALUES (:l_id, :b_id)"), {
                                "l_id": listing_id, "b_id": row[0]})
                
                listing = connection.execute(text("SELECT charity FROM Listings WHERE listing_id = :l_id"), {
                                "l_id": listing_id})
                
                listing_row = listing.fetchone()
                charity = listing_row[0]

                if charity:
                    charity = connection.execute(text("SELECT charity_id from Charity WHERE status = 'AVAILABLE' ORDER BY end_date LIMIT 1"))
                    charity_row = charity.fetchone()
                    charity_id = charity_row[0]

                    connection.execute(text("UPDATE Charity SET fund = fund + (SELECT price FROM Listings WHERE listing_id = :l_id) WHERE charity_id = :l_charity_id"), {
                             "l_id": listing_id, "l_charity_id": charity_id})

                connection.commit()
            else:
                return jsonify({}), 404
        except:
            connection.rollback()
            return jsonify({}), 500
        return jsonify({}), 200



@app.post('/update_listing')
def update_listing():
    listing_id = request.json.get('listingId')
    title = request.json.get('title')
    price = request.json.get('price')
    status = request.json.get('status')
    charity = request.json.get('charity')

    with engine_w.connect() as connection:
        try:
            if title is not None:
                connection.execute(text("UPDATE Listings SET title = :l_title WHERE listing_id = :l_id"), {
                                   "l_title": title, "l_id": listing_id})
            if price is not None:
                connection.execute(text("UPDATE Listings SET price = :l_price WHERE listing_id = :l_id"), {
                                   "l_price": price, "l_id": listing_id})
            if status is not None:
                connection.execute(text("UPDATE Listings SET status = :l_status WHERE listing_id = :l_id"), {
                                   "l_status": status, "l_id": listing_id})
            if charity is not None:
                connection.execute(text("UPDATE Listings SET charity = :l_charity WHERE listing_id = :l_id"), {
                                   "l_charity": charity, "l_id": listing_id})
            connection.commit()
        except IntegrityError:
            connection.rollback()
            return jsonify({}), 400
        except:
            connection.rollback()
            return jsonify({}), 500
        return jsonify({}), 200


@app.get('/get_all_users')
def get_all_users():

    with engine_r.connect() as connection:
        try:
            result = connection.execute(text(
                "SELECT username, address, joining_date, items_sold, items_purchased FROM Users"))
        except IntegrityError:
            return jsonify({}), 400
        except:
            return jsonify({}), 500
        rows = result.fetchall()
        if (rows):
            return jsonify(format_result(['username', 'address', 'joining_date', 'items_sold', 'items_purchased'], rows)), 200
        return jsonify({}), 404


@app.get('/get_all_listings')
def get_all_listings():

    with engine_r.connect() as connection:
        try:
            result = connection.execute(text(
                "SELECT listing_id, seller_id, title, price, location, address, status, charity, created_on FROM Listings"))
        except IntegrityError:
            return jsonify({}), 400
        except:
            return jsonify({}), 500
        rows = result.fetchall()
        if (rows):
            return jsonify(format_result(['listing_id', 'seller_id', 'title', 'price', 'location', 'address', 'status', 'charity', 'created_on'], rows)), 200
        return jsonify({}), 404


@app.get('/get_chats')
def get_chats():
    user_id = request.args.get('userId')

    with engine_r.connect() as connection:
        try:
            result = connection.execute(text(
                "SELECT chat_id FROM Chats WHERE seller = :usr_id OR buyer = :usr_id"), {"usr_id": user_id})
        except IntegrityError:
            return jsonify({}), 400
        except:
            return jsonify({}), 500
        rows = result.fetchall()
        if (rows):
            return jsonify([row[0] for row in rows]), 200
        return jsonify({}), 404


@app.get('/get_search_history')
def get_search_history():
    user_id = request.args.get('userId')

    with engine_r.connect() as connection:
        try:
            result = connection.execute(text(
                "SELECT search_text, search_date FROM Searches WHERE user_id = :usr_id"), {"usr_id": user_id})
        except IntegrityError:
            return jsonify({}), 400
        except:
            return jsonify({}), 500
        rows = result.fetchall()
        if (rows):
            return jsonify(format_result(['search_text', 'search_date'], rows)), 200
        return jsonify({}), 404


@app.post('/create_search')
def get_search():
    user_id = request.json.get('userId')
    search = request.json.get('search')
    with engine_w.connect() as connection:
        try:
            connection.execute(
                text(
                    "INSERT INTO Searches (user_id, search_text) VALUES (:u_id, :search)"),
                {"u_id": user_id, "search": search}
            )
            connection.commit()
        except:
            connection.rollback()
            return jsonify({'message': 'Something went wrong'}), 500
    return jsonify({}), 200


@app.get('/get_chat_info')
def get_chat_info():
    chat_id = request.args.get('chatId')

    with engine_r.connect() as connection:
        try:
            result = connection.execute(text(
                "SELECT chat_id, seller, buyer, listing_id FROM Chats WHERE chat_id = :c_id"), {"c_id": chat_id})
        except IntegrityError:
            return jsonify({}), 400
        except:
            return jsonify({}), 500
        rows = result.fetchall()
        if (rows):
            return jsonify(format_result(['chat_id', 'seller', 'buyer', 'listing_id'], rows)), 200
        return jsonify({}), 404


@app.get('/get_messages')
def get_messages():
    chat_id = request.args.get('chatId')

    with engine_r.connect() as connection:
        try:
            result = connection.execute(text(
                "SELECT message_id, sender_id, message_content, created_on FROM Messages WHERE chat_id = :c_id"), {"c_id": chat_id})
        except IntegrityError:
            return jsonify({}), 400
        except:
            return jsonify({}), 500
        rows = result.fetchall()
        if (rows):
            return jsonify(format_result(['message_id', 'sender_id', 'message_content', 'created_on'], rows, True)), 200
        return jsonify({}), 404


@app.get('/get_last_message_timestamp')
def get_last_message_timestamp():
    chat_id = request.args.get('chatId')

    with engine_r.connect() as connection:
        try:
            result = connection.execute(text(
                "SELECT created_on FROM Messages WHERE chat_id = :c_id ORDER BY created_on DESC LIMIT 1"), {"c_id": chat_id})
        except IntegrityError:
            return jsonify({}), 400
        except:
            return jsonify({}), 500
        rows = result.fetchall()
        if (rows):
            return jsonify(format_result(['timestamp'], rows)), 200
        return jsonify({}), 404


@app.post('/create_message')
def create_message():
    chat_id = request.json.get('chatId')
    message_content = request.json.get('content')
    sender_id = request.json.get('senderId')

    with engine_w.connect() as connection:
        try:
            connection.execute(text("INSERT INTO Messages (chat_id, sender_id, message_content) VALUES (:c_id, :s_id, :content)"), {
                               "c_id": chat_id, "s_id": sender_id, "content": message_content})
            connection.commit()
        except IntegrityError as e:
            connection.rollback()
            if e.orig.pgcode == '23503':
                return jsonify({'message': 'Listing not found'}), 404
            else:
                return jsonify({}), 400
        except:
            connection.rollback()
            return jsonify({'message': 'Something went wrong'}), 500
        return jsonify({}), 200


@app.post('/create_chat')
def create_chat():
    listing_id = request.json.get('listingId')
    seller_id = request.json.get('sellerId')
    buyer_id = request.json.get('buyerId')
    if seller_id == buyer_id:
        return jsonify({'message': 'Cannot create a chat with yourself'}), 400

    with engine_w.connect() as connection:
        try:
            result = connection.execute(text("SELECT chat_id from Chats WHERE listing_id = :l_id AND seller = :s_id AND buyer = :b_id"), {
                                        "l_id": listing_id, "s_id": seller_id, "b_id": buyer_id})
            row = result.fetchone()
            if row:
                return jsonify(format_result(['chatId'], [row])), 409
            result = connection.execute(text("INSERT INTO Chats (listing_id, seller, buyer) VALUES (:l_id, :s_id, :b_id) RETURNING chat_id"), {
                                        "l_id": listing_id, "s_id": seller_id, "b_id": buyer_id})
            connection.commit()
            rows = result.fetchall()
        except IntegrityError as e:
            connection.rollback()
            if e.orig.pgcode == '23503':
                return jsonify({'message': 'Listing not found'}), 404
            else:
                return jsonify({}), 400
        except:
            connection.rollback()
            return jsonify({'message': 'Something went wrong'}), 500
        if rows:
            return jsonify(format_result(['chatId'], rows)), 200
        return jsonify({'message': 'Something went wrong'}), 500


@app.route('/dump_ignores', methods=['GET'])
def dump_ignores():
    with engine_r.connect() as connection:
        try:
            result = connection.execute(text("SELECT * FROM Ignored"))
            connection.commit()
            row = result.fetchall()
            return Response(str(row), status=200)
        except:
            return Response(status=500)


@app.post('/ignore_listing')
def ignore_listing():
    userId = request.json.get("userId")
    listingId = request.json.get("listingId")

    with engine_w.connect() as connection:
        try:
            connection.execute(text("INSERT INTO Ignored (listing_id, user_id) VALUES (:l_id, :u_id);"), {
                "l_id": listingId,
                "u_id": userId,
            })
            connection.commit()
            return jsonify({}), 200
        except IntegrityError as e:
            connection.rollback()
            if e.orig.pgcode == '23505':
                return jsonify({'message': 'that user has already ignored that listing'}), 409
        except Exception as e:
            print(e)

    return jsonify({'message': 'Something went wrong'}), 500


@app.get('/get_user_recommendation_info')
def get_user_recommendation_info():
    userId = request.args.get("userId")
    with engine_r.connect() as connection:
        try:
            result = connection.execute(text("SELECT listing_id FROM Ignored WHERE user_id = :u_id;"), {
                "u_id": userId,
            })
            connection.commit()
            ignored = result.fetchall()
            result = connection.execute(text("SELECT search_text FROM Searches WHERE user_id = :u_id;"), {
                "u_id": userId,
            })
            connection.commit()
            searches = result.fetchall()

            return jsonify({
                "ignored": [x[0] for x in ignored],
                "searches": [x[0] for x in searches],
            }), 200
        except Exception as e:
            print(e)
            return Response(status=500)


@app.get('/get_user_recommendation_info')
def get_user_recommendation_info():
    userId = request.args.get("userId")
    with engine_r.connect() as connection:
        try:
            result = connection.execute(text("SELECT listing_id FROM Ignored WHERE user_id = :u_id;"), {
                "u_id": userId,
            })
            connection.commit()
            ignored = result.fetchall()
            result = connection.execute(text("SELECT search_text FROM Searches WHERE user_id = :u_id;"), {
                "u_id": userId,
            })
            connection.commit()
            searches = result.fetchall()

            return jsonify({
                "ignored": [x[0] for x in ignored],
                "searches": [x[0] for x in searches],
            }), 200
        except Exception as e:
            print(e)
            return Response(status=500)


@app.get('/get_charities')
def get_charities():
    with engine_r.connect() as connection:
        try:
            result = connection.execute(
                text("SELECT charity_id, name, status, fund, logo_url, start_date, end_date, num_listings FROM Charity"),
            )
        except IntegrityError:
            return jsonify({}), 400
        except:
            return jsonify({}), 500
        rows = result.fetchall()
        if (rows):
            return jsonify(format_result(['charity_id', 'name', 'status', 'fund', 'logo_url', 'start_date', 'end_date', 'num_listings'], rows)), 200
        return jsonify({}), 404

if __name__ == '__main__':
    app.run(debug=True)
