from flask import Flask, render_template, request, redirect
import sqlite3
import uuid
import os

app = Flask(__name__)

DB_PATH = "database.db"

ROUTES = {
    "1": {"from": "Черкаси", "to": "Одеса"},
    "2": {"from": "Одеса", "to": "Черкаси"}
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_id TEXT,
            date TEXT,
            departure_time TEXT,
            arrival_time TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS buses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER,
            seats_count INTEGER,
            active INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id TEXT PRIMARY KEY,
            bus_id INTEGER,
            seat_number INTEGER,
            name TEXT,
            phone TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()


@app.route("/")
def index():
    return render_template("index.html", routes=ROUTES)


@app.route("/trips/<route_id>", methods=["GET", "POST"])
def trips(route_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if request.method == "POST":
        date = request.form["date"]
        departure_time = request.form["departure_time"]
        arrival_time = request.form["arrival_time"]

        c.execute("INSERT INTO trips (route_id, date, departure_time, arrival_time) VALUES (?, ?, ?, ?)",
                  (route_id, date, departure_time, arrival_time))
        conn.commit()

    c.execute("SELECT * FROM trips WHERE route_id=?", (route_id,))
    trips = c.fetchall()
    conn.close()

    return render_template("trips.html", trips=trips, route=ROUTES[route_id])


@app.route("/seats/<int:trip_id>")
def seats(trip_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT * FROM buses WHERE trip_id=? AND active=1", (trip_id,))
    buses = c.fetchall()

    bus_data = []

    for bus in buses:
        bus_id, _, seats_count, _ = bus
        c.execute("SELECT seat_number FROM bookings WHERE bus_id=?", (bus_id,))
        booked = [row[0] for row in c.fetchall()]

        bus_data.append({
            "id": bus_id,
            "seats_count": seats_count,
            "booked": booked
        })

    conn.close()

    return render_template("seats.html", buses=bus_data)


@app.route("/book", methods=["POST"])
def book():
    booking_id = str(uuid.uuid4())[:8]
    bus_id = request.form["bus_id"]
    seat = int(request.form["seat"])
    name = request.form["name"]
    phone = request.form["phone"]

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT * FROM bookings WHERE bus_id=? AND seat_number=?", (bus_id, seat))
    if c.fetchone():
        conn.close()
        return "Місце вже зайняте!"

    c.execute("INSERT INTO bookings VALUES (?, ?, ?, ?, ?)",
              (booking_id, bus_id, seat, name, phone))
    conn.commit()
    conn.close()

    return render_template("success.html", booking_id=booking_id)


@app.route("/admin")
def admin():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT * FROM bookings")
    data = c.fetchall()

    conn.close()

    return render_template("admin.html", data=data)


if __name__ == "__main__":
    app.run()
