from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

# Database connection setup
db_config = {
    'user': 'flask_user',
    'password': 'Wh1t3b0x',
    'host': 'localhost',
    'database': 'car_race'
}

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Get car ID, notes, and drone ID from the form
        car_id = request.form.get('car_id')
        notes = request.form.get('notes')
        drone_id = request.form.get('drone_id')
        day = request.form.get('day')

        # Insert new footage entry with notes, timestamp, and drone ID
        cursor.execute("""
            INSERT INTO footage_entries (car_id, notes, drone_id) 
            VALUES (%s, %s, %s)
        """, (car_id, notes, drone_id))
        
        # Update entry count for the car
        if day == 'thur':

            cursor.execute("UPDATE cars SET entry_count_th = entry_count_th + 1 WHERE car_id = %s", (car_id,))
        elif day == 'fri':
            cursor.execute("UPDATE cars SET entry_count_fr = entry_count_fr + 1 WHERE car_id = %s", (car_id,))
        elif day == 'sat':
            cursor.execute("UPDATE cars SET entry_count_sa = entry_count_sa + 1 WHERE car_id = %s", (car_id,))
        elif day == 'sun':
            cursor.execute("UPDATE cars SET entry_count_su = entry_count_su + 1 WHERE car_id = %s", (car_id,))


        conn.commit()
    
    # Fetch all cars and drones to display in the form
    cursor.execute("SELECT * FROM cars")
    cars = cursor.fetchall()
    cursor.execute("SELECT * FROM drones where isdrone = 1")
    drones = cursor.fetchall()
    
    conn.close()
    return render_template('index.html', cars=cars, drones=drones)

@app.route('/otherentry', methods=['GET', 'POST'])
def otherentry():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        # Get car ID, notes, and drone ID from the form
        car_id = request.form.get('car_id')
        notes = request.form.get('notes')
        drone_id = request.form.get('drone_id')

        # Insert new footage entry with notes, timestamp, and drone ID
        cursor.execute("""
            INSERT INTO footage_entries (car_id, notes, drone_id)
            VALUES (%s, %s, %s)
        """, (car_id, notes, drone_id))

        # Update entry count for the car
        cursor.execute("UPDATE cars SET entry_count = entry_count + 1 WHERE car_id = %s", (car_id,))

        conn.commit()

    # Fetch all cars and drones to display in the form
    cursor.execute("SELECT * FROM cars order by DriverName")
    cars = cursor.fetchall()
    cursor.execute("SELECT * FROM drones where isdrone = 0")
    drones = cursor.fetchall()

    conn.close()
    return render_template('otherentry.html', cars=cars, drones=drones)


@app.route('/mark/<int:car_id>', methods=['POST'])
def mark_car(car_id):
    notes = request.form.get('notes')
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    # Insert new entry with notes
    cursor.execute("INSERT INTO footage_entries (car_id, notes) VALUES (%s, %s)", (car_id, notes))
    
    # Update the entry count in the cars table
    cursor.execute("UPDATE cars SET entry_count = entry_count + 1 WHERE car_id = %s", (car_id,))
    
    conn.commit()
    conn.close()
    return redirect(url_for('index'))
@app.route('/manage_cars', methods=['GET', 'POST'])
def manage_cars():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Get the car number from the form submission
        car_number = request.form.get('car_number')
        
        # Insert the new car into the database
        cursor.execute("INSERT INTO cars (car_number) VALUES (%s)", (car_number,))
        conn.commit()

    # Fetch all cars from the database to display
    cursor.execute("SELECT * FROM cars")
    cars = cursor.fetchall()
    
    conn.close()
    return render_template('manage_cars.html', cars=cars)
@app.route('/view_entries', methods=['GET'])
def view_entries():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    # Fetch all entries, ordered by drone and timestamp
    cursor.execute("""
        SELECT e.entry_id, e.timestamp, e.notes, c.car_number, d.drone_name 
        FROM footage_entries e
        JOIN cars c ON e.car_id = c.car_id
        JOIN drones d ON e.drone_id = d.drone_id
        ORDER BY e.entry_id, e.timestamp
    """)
    entries = cursor.fetchall()
    
    # Debugging: Print the entries to check the output
    print("Entries:", entries)  # This will print to your terminal

    conn.close()
    return render_template('view_entries.html', entries=entries)

