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
        result = db.session.execute(text("INSERT INTO Listing_Ratings (rated_listing_id, rating_user_id, rating_value) VALUES ({}, {}, {})".format(listing_id, user_id, rating_value)))
    except IntegrityError as e:
        if e.orig.pgcode == '23503':
            return jsonify({'message': 'Listing not found'}), 404
        else:
            return jsonify({}), 400
    except:
        return jsonify({'message': 'Something went wrong'}), 500
    if result:
        return jsonify({}), 200
    return jsonify({'message': 'Something went wrong'}), 500

@app.get('/get_ratings/<int:listing_id>')
def get_listings(listing_id):
    try:
        result = db.session.execute(text("SELECT username, rating_value FROM Listing_Ratings NATURAL JOIN Users WHERE rated_listing_id = {}".format(listing_id)))
    except IntegrityError:
        return jsonify({}), 400
    except:
        return jsonify({}), 500
    rows = result.fetchall()
    return jsonify(format_result(['username', 'rating'], rows)), 200

if __name__ == '__main__':
    app.run(debug=True)