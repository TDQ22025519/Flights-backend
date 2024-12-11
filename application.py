#AVNS__gBahRug88lvOv4H3sb

#sudo fuser -k 80/tcp
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

def get_planes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM planes;")
    planes = cursor.fetchall()
    plane_list = []
    for plane in planes:
        plane_dict = {
            "flightNumber": plane[0],
            "manufacturer": plane[1],
            "model": plane[2],
            "year": plane[3],
            "details": plane[4] if plane[4] else None,
            "max_seats": plane[5]
        }
        plane_list.append(plane_dict)
    cursor.close()
    conn.close()
    return plane_list

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
            SET booked_seats = booked_seats + %s 
            WHERE flightnumber = %s;
        """, [tickets_to_book, flight_number_input])

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

@application.route('/add_flight', methods=['POST'])
def add_flight():
    data = request.get_json()
    flightnumber = data.get('flightnumber')
    departure = data.get('departure')
    destination = data.get('destination')
    departuredate = data.get('departuredate')
    departuretime = data.get('departuretime')
    returndate = None if data.get('returndate') == '' else data.get('returndate')  # Optional
    returntime = None if data.get('returntime') == '' else data.get('returntime')  # Optional
    class_type = data.get('class')
    price = data.get('price')
    # Validate required fields
    if not all([flightnumber, departure, destination, departuredate, departuretime, class_type, price]):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM planes WHERE flightnumber = %s;", (flightnumber,))
        existing_plane = cursor.fetchone()
        if existing_plane:
            cursor.execute("""
                INSERT INTO flights (flightnumber, departure, destination, departuredate, departuretime, returndate, returntime, price, class)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """, (flightnumber, departure, destination, departuredate, departuretime, returndate, returntime, price, class_type))
            conn.commit()
            return jsonify({"message": "Flight added successfully!"}), 201
        else:
            return jsonify({"message": "This plane does not exist yet"}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@application.route('/modify_flight/<flightnumber>', methods=['PUT'])
def modify_flight(flightnumber):
    data = request.get_json()
    departure = data.get('departure')
    destination = data.get('destination')
    departuredate = data.get('departuredate')
    departuretime = data.get('departuretime')
    returndate = data.get('returndate')  # Optional
    returntime = data.get('returntime')  # Optional
    class_type = data.get('class')
    price = data.get('price')
    
    # Validate required fields (you can adjust this based on your requirements)
    if not any([departure, destination, departuredate, departuretime, price]):
        return jsonify({"error": "At least one field must be provided for modification"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Build the update query dynamically based on provided fields
        update_fields = []
        update_values = []

        if departure:
            update_fields.append("departure = %s")
            update_values.append(departure)
        if destination:
            update_fields.append("destination = %s")
            update_values.append(destination)
        if departuredate:
            update_fields.append("departuredate = %s")
            update_values.append(departuredate)
        if departuretime:
            update_fields.append("departuretime = %s")
            update_values.append(departuretime)
        if returndate:
            update_fields.append("returndate = %s")
            update_values.append(returndate)
        if returntime:
            update_fields.append("returntime = %s")
            update_values.append(returntime)
        if price:
            update_fields.append("price = %s")
            update_values.append(price)
        if class_type:
            update_fields.append("class = %s")
            update_values.append(price)

        # Add flightnumber to the end of the update values
        update_values.append(flightnumber)

        # Construct the SQL update statement
        update_query = f"""
            UPDATE flights
            SET {', '.join(update_fields)}
            WHERE flightnumber = %s
        """

        cursor.execute(update_query, update_values)
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Flight not found"}), 404

        return jsonify({"message": "Flight modified successfully!"}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@application.route('/delete_flight', methods=['POST'])
def delete_flight():
    data = request.get_json()
    flightnumber = data.get('flightnumber')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Delete booking
        cursor.execute('DELETE FROM flights WHERE flightnumber = %s', (flightnumber,))
        cursor.execute('DELETE FROM bookings WHERE flightnumber = %s', (flightnumber,))
        cursor.execute('DELETE FROM seats WHERE flightnumber = %s', (flightnumber,))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': 'This flight was not found.'}), 404

        return jsonify({'message': 'Flight deleted successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@application.route('/planes', methods=['GET'])
def planes():
    plane_data = get_planes()
    return jsonify(plane_data)

@application.route('/add_plane', methods=['POST'])
def add_plane():
    data = request.get_json()
    
    flightnumber = data.get('flightnumber')
    manufacturer = data.get('manufacturer')
    model = data.get('model')
    year = data.get('year')
    details = data.get('details')
    max_seats = data.get('max_seats')

    # Validate required fields
    if not all([flightnumber, manufacturer, model, year, max_seats]):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO planes (flightnumber, manufacturer, model, year, details, max_seats)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (flightnumber, manufacturer, model, year, details, max_seats))
        cursor.execute("""
            INSERT INTO seats (flightnumber, max_seats, booked_seats)
            VALUES (%s, %s, 0)
        """, (flightnumber, max_seats))
        conn.commit()
        return jsonify({"message": "Plane added successfully!"}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@application.route('/update_plane/<flightnumber>', methods=['PUT'])
def update_plane(flightnumber):
    data = request.get_json()
    
    manufacturer = data.get('manufacturer')
    model = data.get('model')
    year = data.get('year')
    details = data.get('details')
    max_seats = data.get('max_seats')

    # Prepare the update query
    update_fields = []
    update_values = []

    if manufacturer:
        update_fields.append("manufacturer = %s")
        update_values.append(manufacturer)
    if model:
        update_fields.append("model = %s")
        update_values.append(model)
    if year:
        update_fields.append("year = %s")
        update_values.append(year)
    if details:
        update_fields.append("details = %s")
        update_values.append(details)
    if max_seats:
        update_fields.append("max_seats = %s")
        update_values.append(max_seats)

    # If no fields are provided for update, return an error
    if not update_fields:
        return jsonify({"error": "No fields provided for update"}), 400

    # Add flightnumber to the end of the update values
    update_values.append(flightnumber)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Construct the SQL update statement
        update_query = f"""
            UPDATE planes
            SET {', '.join(update_fields)}
            WHERE flightnumber = %s
        """

        cursor.execute(update_query, update_values)
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Plane not found"}), 404

        return jsonify({"message": "Plane updated successfully!"}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@application.route('/delete_plane', methods=['DELETE'])
def delete_plane():
    data = request.get_json()
    flightnumber = data.get('flightnumber')

    if not flightnumber:
        return jsonify({"error": "Flight number is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # SQL query to delete the plane
        cursor.execute("""
            DELETE FROM flights
            WHERE flightnumber = %s
        """, (flightnumber,))
        
        cursor.execute("""
            DELETE FROM bookings
            WHERE flightnumber = %s
        """, (flightnumber,))

        cursor.execute("""
            DELETE FROM seats
            WHERE flightnumber = %s
        """, (flightnumber,))

        cursor.execute("""
            DELETE FROM planes
            WHERE flightnumber = %s
        """, (flightnumber,))

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Plane not found"}), 404

        return jsonify({"message": "Plane deleted successfully!"}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()


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
    age_group_input = data.get('age')  # Get the age group from the request

    if not user_name_input or not flight_number_input or not tickets_to_book or not age_group_input:
        return jsonify({"error": "Missing input values"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Start a transaction
    cursor.execute("""BEGIN;""")

    # Retrieve the current max_seats and booked_seats for the flight
    cursor.execute("""
        SELECT s.max_seats, s.booked_seats 
        FROM seats s 
        WHERE s.flightnumber = %s 
        FOR UPDATE;
    """, [flight_number_input])

    max_seats, bookedseats = cursor.fetchone()

    # Check if there are enough available seats
    if (max_seats - bookedseats) >= tickets_to_book:
        # Get account ID
        cursor.execute("""
            SELECT a.id 
            FROM accounts a 
            WHERE a.username = %s;
        """, [user_name_input])
        accountId = cursor.fetchone()[0]

        # Insert multiple booking records for each ticket booked
        cursor.execute("""
            INSERT INTO bookings (account_id, flightnumber, age)
            SELECT %s, %s, %s
            FROM generate_series(1, %s);
        """, [accountId, flight_number_input, age_group_input, tickets_to_book])

        # Commit the transaction
        conn.commit()
        return jsonify({'message': 'Tickets booked successfully'}), 200
    else:
        return jsonify({'error': f'Not enough available seats to book {tickets_to_book} tickets'}), 400

    cursor.close()
    conn.close()


@application.route('/bookings/<username>', methods=['GET'])
def get_bookings(username):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('''
            SELECT f.flightnumber, f.departure, f.destination, b.booking_time, b.booking_id, b.age
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
                'booking_id': booking[4],
                'age': booking[5]
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
