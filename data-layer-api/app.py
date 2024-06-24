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
            "SELECT pgp_sym_decrypt(username::BYTEA,'{}'), rating_value FROM Listing_Ratings JOIN Users on Listing_Ratings.rating_user_id = Users.user_id WHERE rated_listing_id = {}".format(ENCRYPTION_KEY, listing_id)))
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
            "SELECT pgp_sym_decrypt(username::BYTEA,'{}'), review_content FROM Listing_Reviews JOIN Users on Listing_Reviews.review_user_id = Users.user_id WHERE reviewed_listing_id = {}".format(ENCRYPTION_KEY, listing_id)))
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
        result = db.session.execute(text("SELECT pgp_sym_decrypt(username::BYTEA,'{}'), pgp_sym_decrypt(address::BYTEA,'{}'), joining_date, items_sold, items_purchased FROM Users WHERE user_id = {}".format(
            ENCRYPTION_KEY, ENCRYPTION_KEY, user_id)))
    except IntegrityError:
        return jsonify({}), 400
    except:
        return jsonify({}), 500
    rows = result.fetchall()
    if (rows):
        return jsonify(format_result(['username', 'address', 'joining_date', 'items_sold', 'items_purchased'], rows)), 200
    return jsonify({}), 404


@app.post('/update_user')
def update_user():
    user_id = request.json.get('user_id')
    address = request.json.get('address')
    try:
        db.session.execute(text("UPDATE Users SET address = pgp_sym_encrypt('{}', '{}') WHERE user_id = {}".format(
            address, ENCRYPTION_KEY, user_id)))
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({}), 400
    except:
        db.session.rollback()
        return jsonify({}), 500
    return jsonify({}), 200


if __name__ == '__main__':
    app.run(debug=True)
