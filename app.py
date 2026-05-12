# app.py

from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# app.py

app = Flask(__name__)

app.secret_key = "ecocycle_secret_key"

# ---------------- DATABASE ---------------- #

def connect_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():

    conn = connect_db()
    cur = conn.cursor()

    # USERS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT UNIQUE,
        phone TEXT,
        password TEXT,
        role TEXT,
        points INTEGER DEFAULT 0
    )
    """)

    # TRANSACTIONS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    category TEXT,
    pickup_date TEXT,
    time_slot TEXT,
    stars_earned INTEGER,
    status TEXT DEFAULT 'Pending'
)
""")

    conn.commit()
    conn.close()

create_tables()

# ---------------- HOME ---------------- #

@app.route("/")
def home():
    return render_template("index.html")

# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        role = request.form["role"]

        conn = connect_db()
        cur = conn.cursor()

        try:

            cur.execute("""
            INSERT INTO users
            (username,email,phone,password,role)
            VALUES(?,?,?,?,?)
            """, (
                username,
                email,
                phone,
                password,
                role
            ))

            conn.commit()

            flash("Registration Successful!")

            return redirect("/login")

        except:

            flash("Username already exists!")

        finally:

            conn.close()

    return render_template("register.html")
# ---------------- LOGIN ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = connect_db()
        cur = conn.cursor()

        cur.execute("""
        SELECT * FROM users
        WHERE username=? AND password=?
        """, (username, password))

        user = cur.fetchone()

        conn.close()

        if user:

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            # Collector Login

            if user["role"] == "collector":

                return redirect("/collector_dashboard")

            # User Login

            else:

                return redirect("/dashboard")

        else:

            flash("Invalid Username or Password!")

    return render_template("login.html")
# ---------------- USER DASHBOARD ---------------- #

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT * FROM users
    WHERE id=?
    """, (session["user_id"],))

    user = cur.fetchone()

    cur.execute("""
    SELECT * FROM transactions
    WHERE user_id=?
    """, (session["user_id"],))

    transactions = cur.fetchall()

    conn.close()

    # RESPONSIBLE CITIZEN LEVEL

    points = user["points"]

    if points >= 300:
        badge = "Responsible Citizen 🏆"

    elif points >= 150:
        badge = "Eco Warrior 🌿"

    elif points >= 50:
        badge = "Green Citizen ♻️"

    else:
        badge = "Beginner Recycler"

    return render_template(
        "dashboard.html",
        user=user,
        transactions=transactions,
        badge=badge
    )

# ---------------- PICKUP ---------------- #

@app.route("/pickup", methods=["GET", "POST"])
def pickup():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        categories = request.form.getlist("category")

        pickup_date = request.form["pickup_date"]

        time_slot = request.form["time_slot"]

        stars = {

    "Mobile": 25,
    "Laptop": 60,
    "Battery": 15,
    "Charger": 10,
    "Earphones": 10,
    "Television": 75,
    "Printer": 50,
    "Keyboard": 15,
    "Mouse": 10,
    "CPU": 90,
    "Tablet": 40,
    "Smart Watch": 20,
    "Router": 18,
    "Camera": 45,
    "Speaker": 20,
    "Power Bank": 15

}
        conn = connect_db()
        cur = conn.cursor()

        for category in categories:

            points = stars.get(category, 10)

            cur.execute("""
            INSERT INTO transactions
            (user_id,category,pickup_date,time_slot,stars_earned)
            VALUES(?,?,?,?,?)
            """, (

                session["user_id"],
                category,
                pickup_date,
                time_slot,
                points

            ))

        conn.commit()
        conn.close()

        flash("Pickup Request Submitted Successfully!")

        return redirect("/dashboard")

    return render_template("pickup.html")

# ---------------- COLLECTOR DASHBOARD ---------------- #
@app.route("/collector_dashboard")
def collector_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT
    transactions.*,
    users.username,
    users.phone

    FROM transactions

    JOIN users
    ON transactions.user_id = users.id
    """)

    pickups = cur.fetchall()

    conn.close()

    return render_template(
        "collector_dashboard.html",
        pickups=pickups
    )

# ---------------- SUPPORT ---------------- #

@app.route("/support")
def support():
    return render_template("support.html")

# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")
# ---------------- REDEEM PAGE ---------------- #

@app.route("/redeem")
def redeem():

    if "user_id" not in session:
        return redirect("/login")

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT * FROM users
    WHERE id=?
    """, (session["user_id"],))

    user = cur.fetchone()

    conn.close()

    return render_template(
        "redeem.html",
        user=user
    )

# ---------------- UPDATE STATUS ---------------- #

@app.route("/complete/<int:id>")
def complete(id):

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
    UPDATE transactions
    SET status='Done'
    WHERE id=?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect("/collector_dashboard")
# ---------------- RUN APP ---------------- #

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)