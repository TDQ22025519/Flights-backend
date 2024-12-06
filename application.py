from flask import Flask, jsonify
import psycopg2

application = Flask(__name__)

# Database connection parameters
DB_HOST = 'pg-27c1c731-dangquang22082004-c173.i.aivencloud.com'  # Change if your database is hosted elsewhere
DB_NAME = 'defaultdb'
DB_PORT = 11234
DB_USER = 'avnadmin'  # Replace with your PostgreSQL username
DB_PASSWORD = 'AVNS__gBahRug88lvOv4H3sb'  # Replace with your PostgreSQL password

def get_flights():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD
    )
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
            "returnDate": flight[4].isoformat() if flight[4] else None,
            "class": flight[5],
            "price": float(flight[6])
        }
        flight_list.append(flight_dict)
    cursor.close()
    conn.close()
    return flight_list

@application.route('/flights', methods=['GET'])
def flights():
    flight_data = get_flights()
    return jsonify(flight_data)

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=5000)
