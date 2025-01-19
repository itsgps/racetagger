from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import logging

app = Flask(__name__)
app.secret_key = 'sClxGIz9LkWPgo9HiJM5nvwBin2CWhxU'  # Replace with a secure key

# Database connection setup
db_config = {
    'user': 'flask_user',
    'password': 'Wh1t3b0x',
    'host': 'localhost',
    'database': 'car_race'
}

@app.route('/', methods=['GET', 'POST'])
def set_day():
    """Landing page to select the day."""
    if request.method == 'POST':
        # Get selected day from the form
        day = request.form.get('day')
        if day in ['thur', 'fri', 'sat', 'sun']:
            session['selected_day'] = day.lower()  # Store day as lowercase in session
            flash(f"Day set to {day.capitalize()}.", "success")  # Capitalize for user-friendly message
            # Log the session and selected day for debugging
            logging.debug(f"Selected Day Stored in Session: {session['selected_day']}")

            return redirect(url_for('index'))  # Redirect to Drone Entry page
        else:
            flash("Invalid day selected. Please try again.", "error")

    return render_template('set_day.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    """Drone Entry page."""
    if 'selected_day' not in session:
        return redirect(url_for('set_day'))  # Redirect if day is not set

    selected_day = session['selected_day']  # Retrieve the selected day

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        # Get car ID, notes, and drone ID from the form
        car_id = request.form.get('car_id')
        notes = request.form.get('notes')
        drone_id = request.form.get('drone_id')

        # Insert new footage entry including the day
        cursor.execute("""
            INSERT INTO footage_entries (car_id, notes, drone_id, day)
            VALUES (%s, %s, %s, %s)
        """, (car_id, notes, drone_id, selected_day))

        # Update the entry count for the specific day
        day_column = f"entry_count_{selected_day[:2]}"  # Maps day to column (e.g., "entry_count_th")
        cursor.execute(f"UPDATE cars SET {day_column} = {day_column} + 1 WHERE car_id = %s", (car_id,))

        conn.commit()

    # Fetch cars and drones to display in the form
    cursor.execute("SELECT * FROM cars WHERE carbooked = 1")
    cars = cursor.fetchall()
    cursor.execute("SELECT * FROM drones WHERE isdrone = 1")
    drones = cursor.fetchall()

    conn.close()
    return render_template('index.html', cars=cars, drones=drones, selected_day=selected_day)

@app.route('/reset_day')
def reset_day():
    """Clear the session and reset the day."""
    session.clear()
    flash("Day selection reset. Please select a day again.", "info")
    return redirect(url_for('set_day'))

@app.route('/admin')
def admin_page():
    """Admin page with links to admin functionality."""
    return render_template('admin.html')

@app.route('/otherentry', methods=['GET', 'POST'])
def otherentry():
    """Other handheld camera entry page."""
    if 'selected_day' not in session:
        return redirect(url_for('set_day'))  # Redirect if day is not set

    selected_day = session['selected_day']  # Retrieve the selected day

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        # Get form data
        car_id = request.form.get('car_id')
        notes = request.form.get('notes')
        drone_id = request.form.get('drone_id')  # Keep as 'drone_id'

        # Fetch the DriverName for the selected car_id
        cursor.execute("SELECT DriverName FROM cars WHERE car_id = %s", (car_id,))
        driver_data = cursor.fetchone()
        driver_name = driver_data['DriverName'] if driver_data else None

        # Insert new footage entry including the day and driver name
        cursor.execute("""
            INSERT INTO footage_entries (car_id, notes, drone_id, day, driver)
            VALUES (%s, %s, %s, %s, %s)
        """, (car_id, notes, drone_id, selected_day, driver_name))

        # Update the driver interview count
        cursor.execute("UPDATE cars SET driverinterview = driverinterview + 1 WHERE car_id = %s", (car_id,))

        conn.commit()

    # Fetch cars ordered by Driver Name and handheld cameras
    cursor.execute("SELECT * FROM cars WHERE driverbooked = 1 ORDER BY DriverName")
    cars = cursor.fetchall()
    cursor.execute("SELECT * FROM drones WHERE isdrone = 0")  # Filter handheld cameras
    drones = cursor.fetchall()

    conn.close()
    return render_template('otherentry.html', cars=cars, drones=drones, selected_day=selected_day)

@app.route('/manage_cars', methods=['GET', 'POST'])
def manage_cars():
    """Page to manage cars."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        car_number = request.form.get('car_number')

        # Insert the new car into the database
        cursor.execute("INSERT INTO cars (car_number) VALUES (%s)", (car_number,))
        conn.commit()

    # Fetch all cars
    cursor.execute("SELECT * FROM cars")
    cars = cursor.fetchall()

    conn.close()
    return render_template('manage_cars.html', cars=cars)

@app.route('/view_entries', methods=['GET'])
def view_entries():
    """Page to view footage entries."""
    if 'selected_day' not in session:
        return redirect(url_for('set_day'))  # Redirect if day is not set

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Fetch all entries, ordered by drone and timestamp
    cursor.execute("""
        SELECT e.entry_id, e.timestamp, e.notes, e.day, c.car_number, d.drone_name
        FROM footage_entries e
        JOIN cars c ON e.car_id = c.car_id
        JOIN drones d ON e.drone_id = d.drone_id
        ORDER BY e.entry_id, e.timestamp
    """)
    entries = cursor.fetchall()

    conn.close()
    return render_template('view_entries.html', entries=entries)

if __name__ == '__main__':
    app.run(debug=True)

