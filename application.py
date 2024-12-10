from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

application = Flask(__name__)
CORS(application)

# Database connection parameters
DB_HOST = 'pg-27c1c731-dangquang22082004-c173.i.aivencloud.com'  # Change if your database is hosted elsewhere
DB_NAME = 'defaultdb'
DB_PORT = 11234
DB_USER = 'avnadmin'  # Replace with your PostgreSQL username
DB_PASSWORD = 'AVNS__gBahRug88lvOv4H3sb'

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

def book_tickets(user_name_input, flight_number_input, tickets_to_book):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.max_seats, s.booked_seats 
        FROM seats s 
        WHERE s.flightnumber = %s 
        FOR UPDATE;
    """, [flight_number_input])
    
    max_seats, booked_seats = cursor.fetchone()

    # Check if there are enough available seats
    if (max_seats - booked_seats) >= tickets_to_book:
        # Update the booked_seats
        cursor.execute("""
            UPDATE seats 
            SET booked_seats = %s + %s 
            WHERE flightnumber = %s;
        """, [booked_seats, tickets_to_book, flight_number_input])

        # Get account ID
        cursor.execute("""
            SELECT a.id 
            FROM accounts a 
            WHERE a.username = %s;
        """, [user_name_input])
        account_id = cursor.fetchone()[0]

        # Insert bookings
        cursor.execute("""
            INSERT INTO bookings (account_id, flightnumber) 
            SELECT %s, %s 
            FROM generate_series(1, %s);
        """, [account_id, flight_number_input, tickets_to_book])

        # Commit the transaction
        conn.commit()
        return {"message": "Tickets booked successfully!"}
    else:
        raise Exception(f'Not enough available seats to book {tickets_to_book} tickets')

    cursor.close()
    conn.close()

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

@application.route('/book', methods=['POST'])
def book_tickets_route():
    data = request.json
    user_name_input = data.get('username')
    flight_number_input = data.get('flightnumber')
    tickets_to_book = data.get('numberoftickets')

    if not user_name_input or not flight_number_input or not tickets_to_book:
        return jsonify({"error": "Missing input values"}), 400

    result = book_tickets(user_name_input, flight_number_input, tickets_to_book)
    return jsonify(result)

@application.route('/bookings/<username>', methods=['GET'])
def get_bookings(username):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('''
            SELECT f.flightnumber, f.departure, f.destination, b.booking_time, b.booking_id
            FROM bookings b
            JOIN accounts a ON b.account_id = a.id
            JOIN flights f ON b.flightnumber = f.flightnumber
            WHERE a.username = %s
        ''', (username,))
        bookings = cur.fetchall()

        if not bookings:
            return jsonify({'message': 'No bookings found for this user.'}), 404

        booking_list = []
        for booking in bookings:
            booking_list.append({
                'flightnumber': booking[0],
                'departure': booking[1],
                'destination': booking[2],
                'booking_time': booking[3].isoformat(),
                'booking_id': booking[4]
            })

        return jsonify(booking_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cur.close()
        conn.close()


@application.route('/cancel', methods=['POST'])
def cancel_booking():
    data = request.get_json()
    booking_id = data.get('booking_id')
    username = data.get('username')
    flightnumber = data.get('flightnumber')

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Get account_id based on username
        cur.execute('SELECT id FROM accounts WHERE username = %s', (username,))
        account = cur.fetchone()
        if account is None:
            return jsonify({'error': 'User not found!'}), 404

        account_id = account[0]

        # Delete booking
        cur.execute('DELETE FROM bookings WHERE account_id = %s AND flightnumber = %s AND booking_id = %s', (account_id, flightnumber, booking_id))
        conn.commit()

        if cur.rowcount == 0:
            return jsonify({'error': 'No booking found for this user and flight.'}), 404

        return jsonify({'message': 'Booking canceled successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    application.run(debug=True)
