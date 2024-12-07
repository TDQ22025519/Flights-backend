from flask import Flask, request, jsonify
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

application = Flask(__name__)

# Database connection parameters
DB_HOST = 'pg-27c1c731-dangquang22082004-c173.i.aivencloud.com'  # Change if your database is hosted elsewhere
DB_NAME = 'defaultdb'
DB_PORT = 11234
DB_USER = 'avnadmin'  # Replace with your PostgreSQL username
DB_PASSWORD = 'AVNS__gBahRug88lvOv4H3sb'  # Replace with your PostgreSQL password

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

def get_flights():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM flights;")
    flights = cursor.fetchall()
    flight_list = []
    for flight in flights:
        flight_dict = {
            "flightNumber": flight[0],
            "departure": flight[1],
            "destination": flight[2],
            "departureDate": flight[3].isoformat(),
            "departureTime": flight[4].isoformat() if flight[4] else None,
            "returnDate": flight[5].isoformat() if flight[5] else None,
            "returnTime": flight[6].isoformat() if flight[6] else None,
            "class": flight[7],
            "price": float(flight[8])
        }
        flight_list.append(flight_dict)
    cursor.close()
    conn.close()
    return flight_list

@application.route('/flights', methods=['GET'])
def flights():
    flight_data = get_flights()
    return jsonify(flight_data)

@application.route('/accounts', methods=['POST'])
def create_account():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password_hash = generate_password_hash(data.get('password_hash'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the user already exists
    cursor.execute("SELECT * FROM accounts WHERE username = %s OR email = %s;", (username, email))
    existing_user = cursor.fetchone()
    if existing_user:
        cursor.close()
        conn.close()
        return jsonify({'error': 'User already exists'}), 400

    # Create a new user
    cursor.execute(
        "INSERT INTO accounts (username, email, password_hash) VALUES (%s, %s, %s);",
        (username, email, password_hash)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Account created successfully'}), 201

@application.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the user exists
    cursor.execute("SELECT password_hash FROM accounts WHERE username = %s;", (username,))
    user = cursor.fetchone()

    if user is None:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Invalid username or password'}), 401

    password_hash = user[0]

    # Check the password
    if check_password_hash(password_hash, password):
        cursor.close()
        conn.close()
        return jsonify({'message': 'Login successful'}), 200
    else:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Invalid username or password'}), 401

if __name__ == '__main__':
    application.run(debug=True)
