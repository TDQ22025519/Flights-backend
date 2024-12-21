#AVNS__gBahRug88lvOv4H3sb

#sudo fuser -k 80/tcp
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

application = Flask(__name__)
CORS(application)

def verify_credentials(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the user exists
    cursor.execute("SELECT password_hash FROM accounts WHERE username = %s;", (username,))
    user = cursor.fetchone()

    if user is None:
        cursor.close()
        conn.close()
        return False  # User not found

    password_hash = user[0]

    # Check the password
    if check_password_hash(password_hash, password):
        cursor.close()
        conn.close()
        return True  # Credentials are valid
    else:
        cursor.close()
        conn.close()
        return False  # Invalid password

def verify_admin_credentials(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the user exists
    cursor.execute("SELECT password_hash FROM admin_accounts WHERE username = %s;", (username,))
    user = cursor.fetchone()

    if user is None:
        cursor.close()
        conn.close()
        return False  # User not found

    password_hash = user[0]

    # Check the password
    if check_password_hash(password_hash, password):
        cursor.close()
        conn.close()
        return True  # Credentials are valid
    else:
        cursor.close()
        conn.close()
        return False  # Invalid password

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

@application.route('/flights', methods=['GET'])
def flights():
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
            "price": float(flight[7]),
            "distance": float(flight[8]),
            "duration": flight[9].isoformat(),
            "status": flight[10]
        }
        flight_list.append(flight_dict)
    cursor.close()
    conn.close()
    return jsonify(flight_list)

@application.route('/add_flight', methods=['POST'])
def add_flight():
    data = request.get_json()
    adminname = data.get('adminname')
    adminpass = data.get('adminpass')
    flightnumber = data.get('flightnumber')
    departure = data.get('departure')
    destination = data.get('destination')
    departuredate = data.get('departuredate')
    departuretime = data.get('departuretime')
    returndate = None if data.get('returndate') == '' else data.get('returndate')  # Optional
    returntime = None if data.get('returntime') == '' else data.get('returntime')  # Optional
    price = data.get('price')
    distance = data.get('distance')
    duration = data.get('duration')
    status = data.get('status') # Optional

    if not (verify_admin_credentials(adminname, adminpass)):
        return jsonify({"error": "Invalid credentials"}), 400 
    # Validate required fields
    if not all([flightnumber, departure, destination, departuredate, departuretime, price, distance, duration]):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM planes WHERE flightnumber = %s;", (flightnumber,))
        existing_plane = cursor.fetchone()
        if existing_plane:
            cursor.execute("""
                INSERT INTO flights (flightnumber, departure, destination, departuredate, departuretime, returndate, returntime, price, distance, duration, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (flightnumber, departure, destination, departuredate, departuretime, returndate, returntime, price, distance, duration, status))
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
    adminname = data.get('adminname')
    adminpass = data.get('adminpass')
    departure = data.get('departure')
    destination = data.get('destination')
    departuredate = data.get('departuredate')
    departuretime = data.get('departuretime')
    returndate = data.get('returndate')  # Optional
    returntime = data.get('returntime')  # Optional
    price = data.get('price')
    distance = data.get('distance')
    duration = data.get('duration')
    status = data.get('status')
    
    if not (verify_admin_credentials(adminname, adminpass)):
        return jsonify({"error": "Invalid credentials"}), 400 
    
    # Validate required fields (you can adjust this based on your requirements)
    if not any([departure, destination, departuredate, departuretime, price, distance, duration]):
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
        if distance:
            update_fields.append("distance = %s")
            update_values.append(distance)
        if duration:
            update_fields.append("duration = %s")
            update_values.append(duration)
        if status:
            update_fields.append("status = %s")
            update_values.append(status)

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
    adminname = data.get('adminname')
    adminpass = data.get('adminpass')
    flightnumber = data.get('flightnumber')
    conn = get_db_connection()
    cursor = conn.cursor()

    if not (verify_admin_credentials(adminname, adminpass)):
        return jsonify({"error": "Invalid credentials"}), 400 
    
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
            "max_seats": plane[5],
            "max_eco": plane[6],
            "max_bus": plane[7],
            "max_first": plane[8]
        }
        plane_list.append(plane_dict)
    cursor.close()
    conn.close()
    return jsonify(plane_list)

@application.route('/add_plane', methods=['POST'])
def add_plane():
    data = request.get_json()
    adminname = data.get('adminname')
    adminpass = data.get('adminpass')
    flightnumber = data.get('flightnumber')
    manufacturer = data.get('manufacturer')
    model = data.get('model')
    year = data.get('year')
    details = data.get('details')
    max_seats = data.get('max_seats')
    max_eco = data.get('max_eco')
    max_bus = data.get('max_bus')
    max_first = data.get('max_first')

    if not (verify_admin_credentials(adminname, adminpass)):
        return jsonify({"error": "Invalid credentials"}), 400 

    # Validate required fields
    if not all([flightnumber, manufacturer, model, year, max_seats, max_eco, max_bus, max_first]):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO planes (flightnumber, manufacturer, model, year, details, max_seats, max_eco, max_bus, max_first)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (flightnumber, manufacturer, model, year, details, max_seats, max_eco, max_bus, max_first))
        cursor.execute("""
            INSERT INTO seats (flightnumber, max_eco, booked_seats_eco, max_bus, booked_seats_bus, max_first, booked_seats_first)
            VALUES (%s, %s, 0, %s, 0, %s, 0)
        """, (flightnumber, max_eco, max_bus, max_first))
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
    adminname = data.get('adminname')
    adminpass = data.get('adminpass')
    manufacturer = data.get('manufacturer')
    model = data.get('model')
    year = data.get('year')
    details = data.get('details')
    max_seats = data.get('max_seats')
    max_eco = data.get('max_eco')
    max_bus = data.get('max_bus')
    max_first = data.get('max_first')

    if not (verify_admin_credentials(adminname, adminpass)):
        return jsonify({"error": "Invalid credentials"}), 400 

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
    if max_eco:
        update_fields.append("max_eco = %s")
        update_values.append(max_eco)
    if max_bus:
        update_fields.append("max_bus = %s")
        update_values.append(max_bus)
    if max_first:
        update_fields.append("max_first = %s")
        update_values.append(max_first)

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
        cursor.execute("""
            UPDATE seats
            SET 
                max_eco = p.max_eco,
                max_bus = p.max_bus,
                max_first = p.max_first
            FROM planes p
            WHERE seats.flightnumber = p.flightnumber
            AND seats.flightnumber = %s;
        """, (flightnumber,))

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
    adminname = data.get('adminname')
    adminpass = data.get('adminpass')
    flightnumber = data.get('flightnumber')

    if not (verify_admin_credentials(adminname, adminpass)):
        return jsonify({"error": "Invalid credentials"}), 400 

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
    realname = data.get('realname')
    gender = data.get('gender')
    birthdate = data.get('birthdate')
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
        "INSERT INTO accounts (username, email, password_hash, realname, gender, birthdate) VALUES (%s, %s, %s, %s, %s, %s);",
        (username, email, password_hash, realname, gender, birthdate)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Account created successfully'}), 201

@application.route('/account_details/<username>', methods=['POST'])
def account_details(username):
    data = request.get_json()
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()

    if not (verify_credentials(username, password)):
        return jsonify({'error': 'Invalid credentials'}), 400

    # Check if the username exists in the accounts_data
    cursor.execute("SELECT * FROM accounts WHERE username = %s;", (username,))
    existing_user = cursor.fetchone()
    if not existing_user:
        cursor.close()
        conn.close()
        return jsonify({'error': 'User not found'}), 404
        
    cursor.execute("""SELECT username, email, realname, birthdate, gender FROM accounts
    WHERE username = %s;""", (username,))
    details = cursor.fetchall()
    detail_list = []
    for detail in details:
        detail_dict = {
            "username": detail[0],
            "email": detail[1],
            "realname": detail[2],
            "birthdate": detail[3].isoformat(),
            "gender": detail[4]
        }
        detail_list.append(detail_dict)
    cursor.close()
    conn.close()
    return jsonify(detail_list)

@application.route('/modify_accounts/<username>', methods=['PUT'])
def update_account(username):
    data = request.get_json()
    password = data.get('password')
    newusername = data.get('newusername')
    email = data.get('email')
    realname = data.get('realname')
    birthdate = data.get('birthdate')
    gender = data.get('gender')
    newpassword = data.get('newpassword')

    if not (verify_credentials(username, password)):
        return jsonify({"error": "Invalid credentials"}), 400 

    cursor.execute("SELECT id FROM accounts WHERE username = %s;", (username,))
    user_id = cursor.fetchone()
    # Initialize a list to hold the fields to update
    updates = []
    params = []

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if the user exists
        cursor.execute("SELECT * FROM accounts WHERE id = %s;", (user_id,))
        existing_user = cursor.fetchone()
        if not existing_user:
            cursor.close()
            conn.close()
            return jsonify({'error': 'User not found'}), 404

        # Check for username and email conflicts
        if 'newusername' in data or 'email' in data:
            cursor.execute("SELECT * FROM accounts WHERE (username = %s OR email = %s) AND id != %s;", (newusername, email, user_id))
            conflicting_user = cursor.fetchone()
            if conflicting_user:
                cursor.close()
                conn.close()
                return jsonify({'error': 'Username or email already in use'}), 400

        # Check and prepare updates
        if 'newusername' in data:
            updates.append("username = %s")
            params.append(username)
        if 'email' in data:
            updates.append("email = %s")
            params.append(email)
        if 'realname' in data:
            updates.append("realname = %s")
            params.append(realname)
        if 'gender' in data:
            updates.append("gender = %s")
            params.append(gender)
        if 'birthdate' in data:
            updates.append("birthdate = %s")
            params.append(birthdate)
        if 'newpassword' in data:
            password_hash = generate_password_hash(newpassword)
            updates.append("password_hash = %s")
            params.append(password_hash)

        # If no fields to update, return an error
        if not updates:
            cursor.close()
            conn.close()
            return jsonify({'error': 'No fields to update'}), 400

        # Construct the update query
        update_query = "UPDATE accounts SET " + ", ".join(updates) + " WHERE id = %s;"
        params.append(user_id)

        # Execute the update
        cursor.execute(update_query, params)
        conn.commit()
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()

    return jsonify({'message': 'Account updated successfully'}), 200

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

@application.route('/admin_login', methods=['POST'])
def admin_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the user exists
    cursor.execute("SELECT password_hash FROM admin_accounts WHERE username = %s;", (username,))
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
    username = data.get('username')
    password = data.get('password')
    flightnumber = data.get('flightnumber')
    ticket = data.get('ticket_type_id')
    seatclass = data.get('seat_class_id')
    quantity = data.get('numberoftickets')

    if not (verify_credentials(username, password)):
        return jsonify({"error": "Invalid credentials"}), 400 

    if not all ([username, flightnumber, ticket, seatclass, quantity]):
        return jsonify({"error": "Missing input values"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    if (ticket == 1): 
        cursor.execute("""
            SELECT max_eco, booked_seats_eco
            FROM seats 
            WHERE flightnumber = %s
            FOR UPDATE;
        """, [flightnumber])
    elif (ticket == 2):
        cursor.execute("""
            SELECT max_bus, booked_seats_bus
            FROM seats 
            WHERE flightnumber = %s
            FOR UPDATE;
        """, [flightnumber])
    else:
        cursor.execute("""
            SELECT max_first, booked_seats_first
            FROM seats  
            WHERE flightnumber = %s
            FOR UPDATE;
        """, [flightnumber])

    max_seats, booked_seats = cursor.fetchone()

    # Check if there are enough available seats
    if int(max_seats - booked_seats) >= int(quantity):
        # Get account ID
        cursor.execute("""
            SELECT a.id 
            FROM accounts a 
            WHERE a.username = %s;
        """, [username])
        accountId = cursor.fetchone()[0]

        #Get price
        cursor.execute("""
            SELECT price
            FROM flights
            WHERE flightnumber = %s;
        """, [flightnumber])
        flightprice = cursor.fetchone()[0]

        cursor.execute("""
            SELECT discount
            FROM tickets
            WHERE id = %s;
        """, [ticket])
        discount = cursor.fetchone()[0]

        cursor.execute("""
            SELECT multiplier
            FROM seatclasses
            WHERE id = %s;
        """, [seatclass])
        multiplier = cursor.fetchone()[0]

        #calculate total price
        totalPrice = flightprice * discount * multiplier * int(quantity)

        # Insert multiple booking records for each ticket booked
        cursor.execute("""
            INSERT INTO bookings (account_id, flightnumber, ticket_type_id, seat_class_id, quantity, price)
            SELECT %s, %s, %s, %s, %s, %s
        """, [accountId, flightnumber, ticket, seatclass, quantity, totalPrice])

        # Commit the transaction
        conn.commit()
        return jsonify({'message': 'Tickets booked successfully'}), 200
    else:
        return jsonify({'error': f'Not enough available seats to book {quantity} tickets'}), 400

    cursor.close()
    conn.close()


@application.route('/price', methods=['POST'])
def see_price():
    data = request.json
    flightnumber = data.get('flightnumber')
    ticket = data.get('ticket_type_id')
    seatclass = data.get('seat_class_id')
    quantity = data.get('quantity')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        #Get price
        cursor.execute("""
            SELECT price
            FROM flights
            WHERE flightnumber = %s;
        """, [flightnumber])
        flightprice = cursor.fetchone()[0]

        cursor.execute("""
            SELECT discount
            FROM tickets
            WHERE id = %s;
        """, [ticket])
        discount = cursor.fetchone()[0]

        cursor.execute("""
            SELECT multiplier
            FROM seatclasses
            WHERE id = %s;
        """, [seatclass])
        multiplier = cursor.fetchone()[0]

        #calculate total price
        totalPrice = flightprice * discount * multiplier * int(quantity)
        
        conn.commit()
        return jsonify({'totalPrice': totalPrice}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()
        
@application.route('/bookings/<username>', methods=['GET'])
def get_bookings(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT f.flightnumber, f.departure, f.destination, f.distance, f.duration, 
            b.booking_time, b.booking_id, b.quantity, b.price, t.type_name, s.class_name
            FROM bookings b
            JOIN accounts a ON b.account_id = a.id
            JOIN flights f ON b.flightnumber = f.flightnumber
            JOIN tickets t ON b.ticket_type_id = t.id
            JOIN seatclasses s ON b.seat_class_id = s.id
            WHERE a.username = %s
        ''', (username,))
        bookings = cursor.fetchall()

        if not bookings:
            return jsonify({'message': 'No bookings found for this user.'}), 404

        booking_list = []
        for booking in bookings:
            booking_list.append({
                'flightnumber': booking[0],
                'departure': booking[1],
                'destination': booking[2],
                'distance': booking[3],
                'duration':booking[4].isoformat(),
                'booking_time': booking[5].isoformat(),
                'booking_id': booking[6],
                'quantity': booking[7],
                'price': booking[8],
                'type_name': booking[9],
                'class_name': booking[10]
            })

        return jsonify(booking_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()


@application.route('/cancel', methods=['POST'])
def cancel_booking():
    data = request.get_json()
    booking_id = data.get('booking_id')
    username = data.get('username')
    password = data.get('password')
    flightnumber = data.get('flightnumber')

    if not (verify_credentials(username, password)):
        return jsonify({"error": "Invalid credentials"}), 400 

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get account_id based on username
        cursor.execute('SELECT id FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account is None:
            return jsonify({'error': 'User not found!'}), 404

        account_id = account[0]

        # Delete booking
        cursor.execute('DELETE FROM bookings WHERE account_id = %s AND flightnumber = %s AND booking_id = %s', (account_id, flightnumber, booking_id))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': 'No booking found for this user and flight.'}), 404

        return jsonify({'message': 'Booking canceled successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Route to fetch messages for a specific thread
@application.route('/fetch_posts/<int:thread_id>', methods=['GET'])
def fetch_messages(thread_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT post_id, user_id, content, title, created_at FROM Posts WHERE thread_id = %s ORDER BY created_at;", (thread_id,))
    messages = cur.fetchall()
    cur.close()
    conn.close()

    # Format the messages into a list of dictionaries
    message_list = []
    for message in messages:
        message_list.append({
            'post_id': message[0],
            'user_id': message[1],
            'content': message[2],
            'title': message[3],
            'created_at': message[4].isoformat()  # Convert timestamp to ISO format
            
        })

    return jsonify(message_list), 200

# Route to add a message
@application.route('/upload_post', methods=['POST'])
def add_message():
    data = request.json
    adminname = data.get('adminname')
    adminpass = data.get('adminpass')
    thread_id = data.get('thread_id')
    user_id = data.get('user_id')
    content = data.get('content')
    title = data.get('title')

    if not (verify_admin_credentials(adminname, adminpass)):
        return jsonify({"error": "Invalid credentials"}), 400 

    if not thread_id or not user_id or not content or not title:
        return jsonify({'error': 'Missing data'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO Posts (thread_id, user_id, content, title) VALUES (%s, %s, %s, %s) RETURNING post_id;",
        (thread_id, user_id, content, title)
    )
    post_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'post_id': post_id}), 201

# Route to remove a message
@application.route('/delete_post/<int:post_id>', methods=['DELETE'])
def remove_message(post_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Posts WHERE post_id = %s;", (post_id,))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'message': 'Post deleted successfully'}), 200

# Route to upload a thread
@application.route('/upload_thread', methods=['POST'])
def upload_thread():
    data = request.json
    adminname = data.get('adminname')
    adminpass = data.get('adminpass')
    title = data.get('title')
    user_id = data.get('user_id')

    if not (verify_admin_credentials(adminname, adminpass)):
        return jsonify({"error": "Invalid credentials"}), 400 

    if not title or not user_id:
        return jsonify({'error': 'Missing data'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO Threads (title, user_id) VALUES (%s, %s) RETURNING thread_id;",
        (title, user_id)
    )
    thread_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'thread_id': thread_id}), 201

# Route to delete a thread
@application.route('/delete_thread/<int:thread_id>', methods=['DELETE'])
def delete_thread(thread_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Threads WHERE thread_id = %s;", (thread_id,))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'message': 'Thread deleted successfully'}), 200

# Route to fetch all threads
@application.route('/fetch_threads', methods=['GET'])
def fetch_threads():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT thread_id, title, user_id, created_at FROM Threads ORDER BY created_at DESC;")
    threads = cur.fetchall()
    cur.close()
    conn.close()

    # Format the threads into a list of dictionaries
    thread_list = []
    for thread in threads:
        thread_list.append({
            'thread_id': thread[0],
            'title': thread[1],
            'user_id': thread[2],
            'created_at': thread[3].isoformat()  # Convert timestamp to ISO format
        })

    return jsonify(thread_list), 200

@application.route('/fetch_news', methods=['GET'])
def fetch_news():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""select t.title as Thread_title, p.title as Post_title, p.content 
    from threads as t, posts as p 
    where t.thread_id = p.thread_id
    order by p.created_at DESC
    """)
    posts = cursor.fetchall()
    post_list = []
    for post in posts:
        post_dict = {
            "thread_title": post[0],
            "post_title": post[1],
            "content": post[2],
        }
        post_list.append(post_dict)
    cursor.close()
    conn.close()
    return jsonify(post_list)

if __name__ == '__main__':
    application.run(debug=True)
