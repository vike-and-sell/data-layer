from flask import Flask, request, jsonify, Response
import os
from utils import format_result
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://{username}:{password}@{host}:{port}/{database}'.format(
    username=os.environ['RDS_USERNAME'],
    password=os.environ['RDS_PASSWORD'],
    host=os.environ['RDS_HOSTNAME'],
    port=os.environ['RDS_PORT'],
    database=os.environ['RDS_DB_NAME'],
)
app.config['DEBUG'] = True

ENCRYPTION_KEY = os.environ['ENCRYPTION_KEY']
API_KEY = os.environ['API_KEY']

# connect the app to the database
db = SQLAlchemy(app)


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
    try:
        result = db.session.execute(text("SELECT * FROM Users"))
        db.session.commit()
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

    try:
        result = db.session.execute(text("INSERT INTO Users (username, email, password, location, address, joining_date) VALUES ('{}', '{}', '{}', ll_to_earth({},{}), '{}', '{}') RETURNING user_id".format(
            username, email, password, lat, lng, address, join_date)))
        db.session.commit()
        row = result.fetchone()
        if row:
            return jsonify(format_result(['user_id'], [row])), 200
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({}), 400
    except:
        db.session.rollback()
        return jsonify({'message': 'Something went wrong'}), 500
    return jsonify({}), 500


@app.get('/get_user_info_for_login')
def get_user_for_login():
    username = request.args.get('usr')
    try:
        result = db.session.execute(text("SELECT user_id, password FROM Users WHERE username = '{}'".format(
            username)))
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
    try:
        result = db.session.execute(
            text("SELECT user_id, username FROM Users WHERE email = '{}'".format(email)))
        db.session.commit()
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

    try:
        db.session.execute(text(
            "UPDATE Users SET password = '{}' WHERE user_id = '{}'".format(password, user_id)))
        db.session.commit()
        return jsonify({}), 200
    except Exception as e:
        print(e)

    return jsonify({}), 400


@app.post('/create_rating')
def create_rating():
    listing_id = request.json.get('listing_id')
    user_id = request.json.get('user_id')
    rating_value = request.json.get('rating')

    try:
        db.session.execute(text("INSERT INTO Listing_Ratings (rated_listing_id, rating_user_id, rating_value) VALUES ({}, {}, {})".format(
            listing_id, user_id, rating_value)))
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        if e.orig.pgcode == '23503':
            return jsonify({'message': 'Listing not found'}), 404
        else:
            return jsonify({}), 400
    except:
        db.session.rollback()
        return jsonify({'message': 'Something went wrong'}), 500
    return jsonify({}), 200


@app.get('/get_ratings')
def get_ratings():
    listing_id = request.args.get('listingId')
    if not listing_id:
        return jsonify({}), 400
    try:
        result = db.session.execute(text(
            "SELECT username, rating_value FROM Listing_Ratings JOIN Users on Listing_Ratings.rating_user_id = Users.user_id WHERE rated_listing_id = {}".format(listing_id)))
    except IntegrityError:
        return jsonify({}), 400
    except:
        return jsonify({}), 500
    rows = result.fetchall()
    return jsonify(format_result(['username', 'rating'], rows)), 200


@app.post('/create_review')
def create_review():
    listing_id = request.json.get('listing_id')
    user_id = request.json.get('user_id')
    review_content = request.json.get('review')

    try:
        db.session.execute(text("INSERT INTO Listing_Reviews (reviewed_listing_id, review_user_id, review_content) VALUES ({}, {}, '{}')".format(
            listing_id, user_id, review_content)))
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        if e.orig.pgcode == '23503':
            return jsonify({'message': 'Listing not found'}), 404
        else:
            return jsonify({}), 400
    except:
        db.session.rollback()
        return jsonify({'message': 'Something went wrong'}), 500
    return jsonify({}), 200


@app.get('/get_reviews')
def get_reviews():
    listing_id = request.args.get('listingId')
    if not listing_id:
        return jsonify({}), 400
    try:
        result = db.session.execute(text(
            "SELECT username, review_content FROM Listing_Reviews JOIN Users on Listing_Reviews.review_user_id = Users.user_id WHERE reviewed_listing_id = {}".format(listing_id)))
    except IntegrityError:
        return jsonify({}), 400
    except:
        return jsonify({}), 500
    rows = result.fetchall()
    return jsonify(format_result(['username', 'review'], rows)), 200


@app.get('/get_user')
def get_user():
    user_id = request.args.get('userId')
    try:
        result = db.session.execute(text(
            "SELECT username, address, joining_date, items_sold, items_purchased FROM Users WHERE user_id = {}".format(user_id)))
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
            "items_sold": row[3],
            "items_purchased": row[4],
        }), 200
    return jsonify({}), 404


@app.post('/update_user')
def update_user():
    user_id = request.json.get('userId')
    address = request.json.get('address')
    location = request.json.get('location')
    try:
        db.session.execute(text("UPDATE Users SET address = '{}', location = ll_to_earth({}, {}) WHERE user_id = {}".format(
            address, location["lat"], location["lng"], user_id)))
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({}), 400
    except:
        db.session.rollback()
        return jsonify({}), 500
    return jsonify({}), 200


@app.get('/get_all_users')
def get_all_users():
    try:
        result = db.session.execute(text(
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
    try:
        result = db.session.execute(text(
            "SELECT listing_id, seller_id, title, price, location, address, status, created_on FROM Listings"))
    except IntegrityError:
        return jsonify({}), 400
    except:
        return jsonify({}), 500
    rows = result.fetchall()
    if (rows):
        return jsonify(format_result(['listing_id', 'seller_id', 'title', 'price', 'location', 'address', 'status', 'created_on'], rows)), 200
    return jsonify({}), 404


@app.get('/get_chats')
def get_chats():
    user_id = request.args.get('userId')
    try:
        result = db.session.execute(text("SELECT chat_id FROM Chats WHERE seller = {user_id} OR buyer = {user_id}".format(
            user_id=user_id)))
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
    try:
        result = db.session.execute(text(
            "SELECT search_text, search_date FROM Searches WHERE user_id = {}".format(user_id)))
    except IntegrityError:
        return jsonify({}), 400
    except:
        return jsonify({}), 500
    rows = result.fetchall()
    if (rows):
        return jsonify(format_result(['search_text', 'search_date'], rows)), 200
    return jsonify({}), 404


@app.get('/get_chat_info')
def get_chat_info():
    chat_id = request.args.get('chatId')
    try:
        result = db.session.execute(text("SELECT chat_id, seller, buyer, listing_id FROM Chats WHERE chat_id = {}".format(
            chat_id)))
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
    try:
        result = db.session.execute(text("SELECT message_id, sender_id, message_content, created_on FROM Messages WHERE chat_id = {}".format(
            chat_id)))
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
    try:
        result = db.session.execute(text("SELECT created_on FROM Messages WHERE chat_id = {} ORDER BY created_on DESC LIMIT 1".format(
            chat_id)))
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

    try:
        db.session.execute(text("INSERT INTO Messages (chat_id, sender_id, message_content) VALUES ({}, {}, '{}')".format(
            chat_id, sender_id, message_content)))
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        if e.orig.pgcode == '23503':
            return jsonify({'message': 'Listing not found'}), 404
        else:
            return jsonify({}), 400
    except:
        db.session.rollback()
        return jsonify({'message': 'Something went wrong'}), 500
    return jsonify({}), 200


if __name__ == '__main__':
    app.run(debug=True)
