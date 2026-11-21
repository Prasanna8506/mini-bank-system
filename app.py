from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- CREATE TABLES ----------------
def create_tables():
    conn = get_db()

    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        coins INTEGER DEFAULT 0)""")

    conn.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        amount INTEGER)""")

    conn.commit()
    conn.close()

create_tables()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["admin"] = True
            return redirect("/admin")

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            return redirect("/user")
        else:
            return render_template("login.html", error="Invalid Credentials")

    return render_template("login.html", error=None)

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
        except:
            return "User already exists"
        conn.close()

        return redirect("/")

    return render_template("register.html")

# ---------------- ADMIN ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "admin" not in session:
        return redirect("/")

    conn = get_db()

    if request.method == "POST":
        user_id = request.form["user_id"]
        amount = int(request.form["amount"])

        conn.execute("UPDATE users SET coins = coins + ? WHERE id=?",
                     (amount, user_id))

        conn.execute("INSERT INTO transactions (user_id, type, amount) VALUES (?, ?, ?)",
                     (user_id, "ADD", amount))

        conn.commit()

    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()

    return render_template("admin.html", users=users)

# ---------------- ADMIN TRANSACTIONS ----------------
@app.route("/admin/transactions")
def admin_transactions():
    if "admin" not in session:
        return redirect("/")

    conn = get_db()
    transactions = conn.execute("SELECT * FROM transactions").fetchall()
    conn.close()

    return render_template("admin_transactions.html", transactions=transactions)

# ---------------- ADMIN USERS ----------------
@app.route("/admin/users", methods=["GET", "POST"])
def admin_users():
    if "admin" not in session:
        return redirect("/")

    conn = get_db()

    if request.method == "POST":
        user_id = request.form["user_id"]

        conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.execute("DELETE FROM transactions WHERE user_id=?", (user_id,))
        conn.commit()

    users = conn.execute("SELECT * FROM users").fetchall()
    total_users = len(users)

    conn.close()

    return render_template("admin_users.html", users=users, total_users=total_users)

# ---------------- USER ----------------
@app.route("/user", methods=["GET", "POST"])
def user():
    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]
    conn = get_db()

    if request.method == "POST":
        amount = int(request.form["amount"])

        conn.execute("UPDATE users SET coins = coins - ? WHERE id=?",
                     (amount, user_id))

        conn.execute("INSERT INTO transactions (user_id, type, amount) VALUES (?, ?, ?)",
                     (user_id, "SPEND", amount))

        conn.commit()

    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    transactions = conn.execute("SELECT * FROM transactions WHERE user_id=?", (user_id,)).fetchall()

    conn.close()

    return render_template("user.html", user=user, transactions=transactions)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)