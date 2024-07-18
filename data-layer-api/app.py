from flask import Flask, request, jsonify, Response
import os
from utils import format_result
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine
import redis

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
r_client = redis.Redis(host='magical_tu', port=6379)

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
    query = "SELECT * FROM Users"
    try:
        result = r_client.get(query)
        if not result is None:
            return Response(result, status=200)
    finally:  
        with engine_r.connect() as connection:
            try:
                result = connection.execute(text(query))
                connection.commit()
                row = result.fetchall()
                r_client.set(query, str(row))
                return Response(str(row), status=200)
            except:
                return Response(status=500)


@app.route('/dump_listings', methods=['GET'])
def dump_listings():
    query = "SELECT * FROM Listings"
    try:
        result = r_client.get(query)
        if not result is None:
            return Response(result, status=200)
    finally:
        with engine_r.connect() as connection:
            try:
                result = connection.execute(text(query))
                connection.commit()
                row = result.fetchall()
                r_client.set(query, str(row))
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
    query = f"SELECT user_id, password FROM Users WHERE username = {username}"
    try:
        result = r_client.get(query)
        if not result is None:
            return result, 200
    finally:
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
                json = jsonify(format_result(['user_id', 'password'], [row]))
                r_client.set(query, str(json))
                return json, 200
            return jsonify({}), 404


@app.get('/get_user_by_email')
def get_user_by_email():
    email = request.args.get('eml')
    query = f"SELECT user_id, username FROM Users WHERE email = {email}"
    try:
        result = r_client.get(query)
        if not result is None:
            return result
    finally:
        with engine_r.connect() as connection:
            try:
                result = connection.execute(text(
                    "SELECT user_id, username FROM Users WHERE email = :e_mail"), {"e_mail": email})
                connection.commit()
                row = result.fetchone()
                if row:
                    json = jsonify(format_result(['user_id', 'username'], [row]))
                    r_client.set(query, str(json))
                    return json
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
            connection.execute(
                text("INSERT INTO Listing_Ratings (rated_listing_id, rating_user_id, rating_value) VALUES (:listing_id, :usr_id, :value)"),
                {"listing_id": listing_id, "usr_id": user_id, "value": rating_value}
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
        return jsonify({}), 200


@app.get('/get_ratings')
def get_ratings():
    listing_id = request.args.get('listingId')
    if not listing_id:
        return jsonify({}), 400
    query = f"SELECT username, rating_value, created_on FROM Listing_Ratings JOIN Users on Listing_Ratings.rating_user_id = Users.user_id WHERE rated_listing_id = {listing_id}"

    try:
        result = r_client.get(query)
        if not result is None:
            return result, 200
    finally:
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
            json = jsonify(format_result(['username', 'rating', 'created_on'], rows, True))
            r_client.set(query, str(json))
            return json, 200


@app.post('/create_review')
def create_review():
    listing_id = request.json.get('listingId')
    user_id = request.json.get('userId')
    review_content = request.json.get('review')

    with engine_w.connect() as connection:
        try:
            connection.execute(
                text("INSERT INTO Listing_Reviews (reviewed_listing_id, review_user_id, review_content) VALUES (:listing_id, :usr_id, :content)"),
                {"listing_id": listing_id, "usr_id": user_id,
                    "content": review_content}
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
        return jsonify({}), 200


@app.get('/get_reviews')
def get_reviews():
    listing_id = request.args.get('listingId')
    if not listing_id:
        return jsonify({}), 400
    query = f"SELECT username, review_content, created_on FROM Listing_Reviews JOIN Users on Listing_Reviews.review_user_id = Users.user_id WHERE reviewed_listing_id = {listing_id}"

    try:
        result = r_client.get(query)
        if not result is None:
            return result, 200
    finally:
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
            json = jsonify(format_result(['username', 'review', 'created_on'], rows, True))
            r_client.set(query, str(json))
            return json, 200


@app.get('/get_user')
def get_user():
    user_id = request.args.get('userId')
    query = f"SELECT username, address, joining_date FROM Users WHERE user_id = {user_id}"

    try:
        result = r_client.get(query)
        if not result is None:
            return result, 200
    finally:
        with engine_r.connect() as connection:
            try:
                result = connection.execute(text(
                    "SELECT username, address, joining_date FROM Users WHERE user_id = :usr_id"), {"usr_id": user_id})
            except IntegrityError:
                return jsonify({}), 400
            except:
                return jsonify({}), 500
            row = result.fetchone()
            if row:
                json = jsonify({
                    "username": row[0],
                    "address": row[1],
                    "joining_date": row[2].isoformat(),
                })
                r_client.set(query, str(json))
                return json, 200
            return jsonify({}), 404


@app.get('/get_user_purchases')
def get_user_purchases():
    user_id = request.args.get('userId')
    query = f"SELECT listing_id FROM Sales WHERE buyer_id = {user_id}"

    try:
        result = r_client.get(query)
        if not result is None:
            return result, 200
    finally:
        with engine_r.connect() as connection:
            try:
                result = connection.execute(text(
                    "SELECT listing_id FROM Sales WHERE buyer_id = :usr_id"), {"usr_id": user_id})
                rows = result.fetchall()
                if rows:
                    json = jsonify([x[0] for x in rows])
                    r_client.set(query, str(json))
                    return json, 200
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
    query = f"SELECT Sales.listing_id FROM Sales JOIN Listings ON Sales.listing_id = Listings.listing_id WHERE seller_id = {user_id}"

    try:
        result = r_client.get(query)
        if not result is None:
            return result, 200
    finally:
        with engine_r.connect() as connection:
            try:
                result = connection.execute(text(
                    "SELECT Sales.listing_id FROM Sales JOIN Listings ON Sales.listing_id = Listings.listing_id WHERE seller_id = :usr_id"), {"usr_id": user_id})
                rows = result.fetchall()
                if rows:
                    json = jsonify([x[0] for x in rows])
                    r_client.set(query, str(json))
                    return json, 200
                else:
                    return jsonify([]), 200
            except IntegrityError:
                return jsonify({}), 400


@app.post('/update_user')
def update_user():
    user_id = request.json.get('userId')
    address = request.json.get('address')
    location = request.json.get('location')

    with engine_w.connect() as connection:
        try:
            connection.execute(
                text(
                    "UPDATE Users SET address = :addr, location = ll_to_earth(:lat, :lng) WHERE user_id = :usr_id"),
                {"addr": address, "lat": location["lat"],
                    "lng": location["lng"], "usr_id": user_id}
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
    if not is_descending:
        query = f"SELECT listing_id, seller_id, title, price, address, status, created_on, last_updated_at FROM Listings WHERE price < {max_price} AND price > {min_price} AND status = {status} ORDER BY {sort_by} DESC"
    else:
        query = f"SELECT listing_id, seller_id, title, price, address, status, created_on, last_updated_at FROM Listings WHERE price < {max_price} AND price > {min_price} AND status = {status} ORDER BY {sort_by} DESC"

    try:
        result = r_client.get(query)
        if not result is None:
            return result, 200
    finally:
        with engine_r.connect() as connection:
            try:
                if not is_descending:
                    result = connection.execute(
                        text("SELECT listing_id, seller_id, title, price, address, status, created_on, last_updated_at FROM Listings WHERE price < :max_price AND price > :min_price AND status = :l_status ORDER BY :srt_by"),
                        {"max_price": max_price, "min_price": min_price,
                            "l_status": status, "srt_by": sort_by}
                    )
                else:
                    result = connection.execute(
                        text("SELECT listing_id, seller_id, title, price, address, status, created_on, last_updated_at FROM Listings WHERE price < :max_price AND price > :min_price AND status = :l_status ORDER BY :srt_by DESC"),
                        {"max_price": max_price, "min_price": min_price,
                            "l_status": status, "srt_by": sort_by}
                    )
            except IntegrityError:
                return jsonify({}), 400
            except:
                return jsonify({}), 500
            rows = result.fetchall()
            if (rows):
                json = jsonify(format_result(['listingId', 'sellerId', 'title', 'price', 'address', 'status', 'listedAt', 'lastUpdatedAt'], rows, True))
                r_client.set(query, str(json))
                return json, 200
            return jsonify({}), 404


@app.get('/get_listing')
def get_listing():
    listing_id = request.args.get('listingId')
    query = f"SELECT listing_id, seller_id, title, price, address, status, created_on, last_updated_at FROM Listings WHERE listing_id = {listing_id}"

    try:
        result = r_client.get(query)
        if not result is None:
            return result, 200
    finally:
        with engine_r.connect() as connection:
            try:
                result = connection.execute(text(
                    "SELECT listing_id, seller_id, title, price, address, status, created_on, last_updated_at FROM Listings WHERE listing_id = :l_id"), {"l_id": listing_id})
            except IntegrityError:
                return jsonify({}), 400
            except:
                return jsonify({}), 500
            rows = result.fetchall()
            if (rows):
                json = jsonify(format_result(['listingId', 'sellerId', 'title', 'price', 'address', 'status', 'listedAt', 'lastUpdatedAt'], rows))
                r_client.set(query, str(json))
                return json, 200
            return jsonify({}), 404


@app.get('/get_listing_by_seller')
def get_listing_by_seller():
    user_id = request.args.get('userId')
    query = f"SELECT listing_id, seller_id, title, price, address, status, created_on, last_updated_at FROM Listings WHERE seller_id = {user_id}"

    try:
        result = r_client.get(query)
        if not result is None:
            return result, 200
    finally:
        with engine_r.connect() as connection:
            try:
                result = connection.execute(text(
                    "SELECT listing_id, seller_id, title, price, address, status, created_on, last_updated_at FROM Listings WHERE seller_id = :usr_id"), {"usr_id": user_id})
            except IntegrityError:
                return jsonify({}), 400
            except:
                return jsonify({}), 500
            rows = result.fetchall()
            if (rows):
                json = jsonify(format_result(['listingId', 'sellerId', 'title', 'price', 'address', 'status', 'createdOn', 'lastUpdatedAt'], rows))
                r_client.set(query, str(json))
                return json, 200
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

    with engine_w.connect() as connection:
        try:
            result = connection.execute(
                text("INSERT INTO Listings (seller_id, title, price, address, location, status) VALUES (:sllr_id, :l_title, :l_price, :addr, ll_to_earth(:lat, :lng), :l_status) RETURNING listing_id"),
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
        return jsonify(format_result(['listingId'], row)), 201


@app.post('/update_listing')
def update_listing():
    listing_id = request.json.get('listingId')
    title = request.json.get('title')
    price = request.json.get('price')
    status = request.json.get('status')

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
    query = "SELECT username, address, joining_date, items_sold, items_purchased FROM Users"

    try:
        result = r_client.get(query)
        if not result is None:
            return result, 200
    finally:  
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
                json = jsonify(format_result(['username', 'address', 'joining_date', 'items_sold', 'items_purchased'], rows))
                r_client.set(query, str(json))
                return json, 200
            return jsonify({}), 404


@app.get('/get_all_listings')
def get_all_listings():
    query = "SELECT listing_id, seller_id, title, price, location, address, status, created_on FROM Listings"

    try:
        result = r_client.get(query)
        if not result is None:
            return result, 200
    finally: 
        with engine_r.connect() as connection:
            try:
                result = connection.execute(text(
                    "SELECT listing_id, seller_id, title, price, location, address, status, created_on FROM Listings"))
            except IntegrityError:
                return jsonify({}), 400
            except:
                return jsonify({}), 500
            rows = result.fetchall()
            if (rows):
                json = jsonify(format_result(['listing_id', 'seller_id', 'title', 'price', 'location', 'address', 'status', 'created_on'], rows))
                r_client.set(query, str(json))
                return json, 200
            return jsonify({}), 404


@app.get('/get_chats')
def get_chats():
    user_id = request.args.get('userId')
    query = f"SELECT chat_id FROM Chats WHERE seller = {user_id} OR buyer = {user_id}"

    try:
        result = r_client.get(query)
        if not result is None:
            return result, 200
    finally: 
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
                json = jsonify([row[0] for row in rows])
                r_client.set(query, str(json))
                return json, 200
            return jsonify({}), 404


@app.get('/get_search_history')
def get_search_history():
    user_id = request.args.get('userId')
    query = f"SELECT search_text, search_date FROM Searches WHERE user_id = {user_id}"

    try:
        result = r_client.get(query)
        if not result is None:
            return result, 200
    finally:
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
                json = jsonify(format_result(['search_text', 'search_date'], rows))
                r_client.set(query, str(json))
                return json, 200
            return jsonify({}), 404


@app.get('/get_chat_info')
def get_chat_info():
    chat_id = request.args.get('chatId')
    query = f"SELECT chat_id, seller, buyer, listing_id FROM Chats WHERE chat_id = {chat_id}"

    try:
        result = r_client.get(query)
        if not result is None:
            return result, 200
    finally:
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
                json = jsonify(format_result(['chat_id', 'seller', 'buyer', 'listing_id'], rows))
                r_client.set(query, str(json))
                return json, 200
            return jsonify({}), 404


@app.get('/get_messages')
def get_messages():
    chat_id = request.args.get('chatId')
    query = f"SELECT message_id, sender_id, message_content, created_on FROM Messages WHERE chat_id = {chat_id}"

    try:
        result = r_client.get(query)
        if not result is None:
            return result, 200
    finally:
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
                json = jsonify(format_result(['message_id', 'sender_id', 'message_content', 'created_on'], rows, True))
                r_client.set(query, str(json))
                return json, 200
            return jsonify({}), 404


@app.get('/get_last_message_timestamp')
def get_last_message_timestamp():
    chat_id = request.args.get('chatId')
    query = f"SELECT created_on FROM Messages WHERE chat_id = {chat_id} ORDER BY created_on DESC LIMIT 1"

    try:
        result = r_client.get(query)
        if not result is None:
            return result, 200
    finally:
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
                json = jsonify(format_result(['timestamp'], rows))
                r_client.set(query, str(json))
                return json, 200
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
            result = connection.execute(text("SELECT * from Chats WHERE listing_id = :l_id AND seller = :s_id AND buyer = :b_id"), {
                                        "l_id": listing_id, "s_id": seller_id, "b_id": buyer_id})
            rows = result.fetchall()
            if rows:
                return jsonify({'message': 'Chat already exists'}), 409
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
    query = "SELECT * FROM Ignored"
    try:
        result = r_client.get(query)
        if not result is None:
            return Response(result, status=200)
    finally:
        with engine_r.connect() as connection:
            try:
                result = connection.execute(text(query))
                connection.commit()
                row = result.fetchall()
                r_client.set(query, str(row))
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


if __name__ == '__main__':
    app.run(debug=True)
