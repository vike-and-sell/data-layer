from flask import Flask, request, jsonify
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

# connect the app to the database
db = SQLAlchemy(app)

@app.route('/get_user', methods=['GET'])
def test_sql():
    result = db.session.execute(text("SELECT * FROM Users WHERE username = 'john_doe'"))
    rows = result.fetchall()
    return str(rows)

@app.post('/create_rating')
def create_rating():
    listing_id = request.json.get('listing_id')
    user_id = request.json.get('user_id')
    rating_value = request.json.get('rating')

    try:
        db.session.execute(text("INSERT INTO Listing_Ratings (rated_listing_id, rating_user_id, rating_value) VALUES ({}, {}, {})".format(listing_id, user_id, rating_value)))
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
        result = db.session.execute(text("SELECT pgp_sym_decrypt(username::BYTEA,'{}'), rating_value FROM Listing_Ratings JOIN Users on Listing_Ratings.rating_user_id = Users.user_id WHERE rated_listing_id = {}".format(ENCRYPTION_KEY,listing_id)))
    except IntegrityError:
        return jsonify({}), 400
    except:
        return jsonify({}), 500
    rows = result.fetchall()
    return jsonify(format_result(['username', 'rating'], rows)), 200

if __name__ == '__main__':
    app.run(debug=True)