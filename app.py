# app.py

from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "ecostars_secret_key"

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
        stars INTEGER DEFAULT 0
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
        stars_earned INTEGER
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
        role = request.form["role"]

        password = generate_password_hash(
            request.form["password"]
        )

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

            flash("Email already exists!")

        finally:

            conn.close()

    return render_template("register.html")

# ---------------- LOGIN ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = connect_db()
        cur = conn.cursor()

        cur.execute("""
        SELECT * FROM users
        WHERE email=?
        """, (email,))

        user = cur.fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            # DIFFERENT LOGIN REDIRECTS

            if user["role"] == "collector":
                return redirect("/collector_dashboard")

            else:
                return redirect("/dashboard")

        else:

            flash("Invalid Login Details!")

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

    stars = user["stars"]

    if stars >= 300:
        badge = "Responsible Citizen 🏆"

    elif stars >= 150:
        badge = "Eco Warrior 🌿"

    elif stars >= 50:
        badge = "Green Citizen ♻️"

    else:
        badge = "Beginner Recycler"

    return render_template(
        "dashboard.html",
        user=user,
        transactions=transactions,
        badge=badge
    )

# ---------------- PICKUP BOOKING ---------------- #

@app.route("/pickup", methods=["GET", "POST"])
def pickup():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        category = request.form["category"]
        pickup_date = request.form["pickup_date"]
        time_slot = request.form["time_slot"]

        # STAR SYSTEM

        stars_map = {
            "Mobile": 30,
            "Laptop": 50,
            "Battery": 20,
            "Charger": 10,
            "Earphones": 15,
            "Television": 60,
            "Printer": 40
        }

        stars = stars_map.get(category, 10)

        conn = connect_db()
        cur = conn.cursor()

        # SAVE TRANSACTION

        cur.execute("""
        INSERT INTO transactions
        (user_id,category,pickup_date,time_slot,stars_earned)
        VALUES(?,?,?,?,?)
        """, (
            session["user_id"],
            category,
            pickup_date,
            time_slot,
            stars
        ))

        # UPDATE STARS

        cur.execute("""
        UPDATE users
        SET stars = stars + ?
        WHERE id=?
        """, (
            stars,
            session["user_id"]
        ))

        conn.commit()
        conn.close()

        flash(f"Pickup booked successfully! You earned {stars} stars ⭐")

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

# ---------------- RUN APP ---------------- #

if __name__ == "__main__":
    app.run(debug=True)