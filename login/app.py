from flask import Flask, request, redirect, render_template, session, flash, url_for
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
import re
import MySQLdb.cursors
import os
from datetime import timedelta

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(minutes=30)  # Session timeout after 30 minutes of inactivity

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'jennifer'
app.config['MYSQL_DB'] = 'scraper_project'
mysql = MySQL(app)
bcrypt = Bcrypt(app)

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ragunanthan570@gmail.com'
app.config['MAIL_PASSWORD'] = 'zieh tkhl tfzd lzcs'  # Use App Password
app.config['MAIL_DEFAULT_SENDER'] = 'ragunanthan570@gmail.com'
mail = Mail(app)

# ==================== HOME PAGE ==================== #
@app.route('/')
def home():
    return render_template('home.html')

# ==================== USER REGISTRATION ==================== #
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid email format!", "danger")
            return redirect(url_for('register'))

        if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
            flash("Password must be at least 8 characters long and contain both letters and numbers!", "danger")
            return redirect(url_for('register'))

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE email = %s OR username = %s", (email, username))
        user = cursor.fetchone()
        if user:
            if user['email'] == email:
                flash("Email already registered!", "warning")
            if user['username'] == username:
                flash("Username already taken!", "warning")
            cursor.close()
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, hashed_password))
        mysql.connection.commit()
        cursor.close()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# ==================== USER LOGIN ==================== #
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        if not email or not password:
            flash("All fields are required!", "danger")
            return redirect(url_for('login'))

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE email = %s", [email])
        user = cursor.fetchone()
        cursor.close()

        if user and bcrypt.check_password_hash(user['password'], password):
            session.permanent = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password!", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

# ==================== PASSWORD RESET ==================== #
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email'].strip()

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE email = %s", [email])
        user = cursor.fetchone()
        cursor.close()

        if not user:
            flash("No account found with that email!", "warning")
            return redirect(url_for('forgot_password'))

        token = os.urandom(16).hex()
        reset_link = url_for('reset_password', token=token, _external=True)
        msg = Message("Password Reset Request", recipients=[email])
        msg.body = f"Click the link below to reset your password:\n{reset_link}"
        mail.send(msg)

        flash("Password reset link sent to your email!", "success")
        return redirect(url_for('login'))

    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        new_password = request.form['password'].strip()

        if len(new_password) < 8 or not re.search(r"[A-Za-z]", new_password) or not re.search(r"[0-9]", new_password):
            flash("Password must be at least 8 characters long and contain both letters and numbers!", "danger")
            return redirect(url_for('reset_password', token=token))

        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, email))
        mysql.connection.commit()
        cursor.close()

        flash("Password reset successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('reset_password.html')

# ==================== USER LOGOUT ==================== #
@app.route('/logout')
def logout():
    session.clear()  # Clears entire session
    flash("You have been logged out!", "info")
    return render_template('logout.html')

@app.after_request
def add_no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# ==================== DASHBOARD ==================== #
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))
    
    return f"Welcome, {session['username']}! <br><a href='/logout'>Logout</a>"

if __name__ == '__main__':
    app.run(debug=True)
