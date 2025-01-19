from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
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

# --- Web Routes (Admin and User Interface) ---

@app.route('/', methods=['GET', 'POST'])
def set_day():
    """Landing page to select the day."""
    if request.method == 'POST':
        day = request.form.get('day')
        if day in ['thur', 'fri', 'sat', 'sun']:
            session['selected_day'] = day.lower()
            flash(f"Day set to {day.capitalize()}.", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid day selected. Please try again.", "error")
    return render_template('set_day.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    """Drone Entry page."""
    if 'selected_day' not in session:
        return redirect(url_for('set_day'))

    selected_day = session['selected_day']
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        car_id = request.form.get('car_id')
        notes = request.form.get('notes')
        drone_id = request.form.get('drone_id')

        cursor.execute("""
            INSERT INTO footage_entries (car_id, notes, drone_id, day)
            VALUES (%s, %s, %s, %s)
        """, (car_id, notes, drone_id, selected_day))

        day_column = f"entry_count_{selected_day[:2]}"
        cursor.execute(f"UPDATE cars SET {day_column} = {day_column} + 1 WHERE car_id = %s", (car_id,))
        conn.commit()

    cursor.execute("SELECT * FROM cars WHERE carbooked = 1 ORDER BY car_number")
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

@app.route('/otherentry', methods=['GET', 'POST'])
def otherentry():
    """Other handheld camera entry page."""
    if 'selected_day' not in session:
        return redirect(url_for('set_day'))

    selected_day = session['selected_day']
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        car_id = request.form.get('car_id')
        notes = request.form.get('notes')
        drone_id = request.form.get('drone_id')

        cursor.execute("SELECT DriverName FROM cars WHERE car_id = %s", (car_id,))
        driver_data = cursor.fetchone()
        driver_name = driver_data['DriverName'] if driver_data else None

        cursor.execute("""
            INSERT INTO footage_entries (car_id, notes, drone_id, day, driver)
            VALUES (%s, %s, %s, %s, %s)
        """, (car_id, notes, drone_id, selected_day, driver_name))

        cursor.execute("UPDATE cars SET driverinterview = driverinterview + 1 WHERE car_id = %s", (car_id,))
        conn.commit()

    cursor.execute("SELECT * FROM cars WHERE driverbooked = 1 ORDER BY DriverName")
    cars = cursor.fetchall()
    cursor.execute("SELECT * FROM drones WHERE isdrone = 0")
    drones = cursor.fetchall()

    conn.close()
    return render_template('otherentry.html', cars=cars, drones=drones, selected_day=selected_day)

@app.route('/manage_cars', methods=['GET', 'POST'])
def manage_cars():
    """Page to manage cars."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        # Loop through form data to find updated values
        for key, value in request.form.items():
            if key.startswith('driverbooked_') or key.startswith('carbooked_'):
            # Extract field name and car_id from the key
                field, car_id = key.split('_')
                car_id = int(car_id)

            # Convert value to integer, treating empty or whitespace-only input as 0
                value = int(value.strip()) if value.strip() else 0

            # Update the corresponding field in the database
                query = f"UPDATE cars SET {field} = %s WHERE car_id = %s"
                cursor.execute(query, (value, car_id))
    
    # Commit the changes
    conn.commit()

    # Fetch updated car data to display
    cursor.execute("SELECT * FROM cars ORDER BY Competitor")
    cars = cursor.fetchall()
    conn.close()

    return render_template('manage_cars.html', cars=cars)

@app.route('/view_entries', methods=['GET'])
def view_entries():
    """Page to view footage entries."""
    if 'selected_day' not in session:
        return redirect(url_for('set_day'))

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

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

@app.route('/admin', methods=['GET'])
def admin_page():
    """Admin page."""
    return render_template('admin.html')

# --- API Routes (Supplementary for Mobile Apps) ---

@app.route('/api/cars', methods=['GET'])
def api_get_cars():
    """API to get all cars."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cars WHERE carbooked = 1 ORDER BY DriverName")
    cars = cursor.fetchall()
    conn.close()
    return jsonify(cars)

@app.route('/api/footage', methods=['POST'])
def api_add_footage():
    """API to add footage."""
    data = request.get_json()
    car_id = data.get('car_id')
    notes = data.get('notes')
    drone_id = data.get('drone_id')
    day = data.get('day')

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO footage_entries (car_id, notes, drone_id, day)
        VALUES (%s, %s, %s, %s)
    """, (car_id, notes, drone_id, day))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Footage entry added successfully'}), 201

if __name__ == '__main__':
    app.run(debug=True)

