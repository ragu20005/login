from flask import Flask, request, redirect, render_template, session, flash, url_for, jsonify
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from flask_wtf.csrf import CSRFProtect
import re
import MySQLdb.cursors
import os
from datetime import datetime, timedelta
from scraping.scraper import Scraper
import json
import pandas as pd
from pydantic import BaseModel, HttpUrl, ValidationError
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import csv
from io import StringIO
import asyncio
import requests
from dotenv import load_dotenv
from scraping.serp_scraper import SERPScraper
from config.serp_config import SERP_PROVIDERS, SERP_TEMPLATES

load_dotenv()  # Load environment variables

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))
csrf = CSRFProtect(app)

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
app.config['MAIL_PASSWORD'] = 'zieh tkhl tfzd lzcs'
app.config['MAIL_DEFAULT_SENDER'] = 'ragunanthan570@gmail.com'
mail = Mail(app)

# Scraper Configuration
proxies = ["proxy1", "proxy2", "proxy3"]
user_agents = ["user-agent1", "user-agent2", "user-agent3"]
captcha_api_key = "your_2captcha_api_key"
scraper = Scraper(proxies, user_agents, captcha_api_key)

# Add this with your other configurations
serp_api_key = os.environ.get('SERP_API_KEY')
serp_scraper = SERPScraper(serp_api_key)

predefined_templates = {
    'example.com': {'static': True},
    'dynamic-site.com': {'static': False},
    'quotes.toscrape.com': {'static': True}
}

def is_dynamic_website(url):
    response = requests.get(url)
    return 'javascript' in response.text.lower()

def scrape_static_website(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    quotes = soup.find_all('div', class_='quote')
    return [{'text': quote.find('span', class_='text').get_text(),
             'author': quote.find('small', class_='author').get_text(),
             'tags': [tag.get_text() for tag in quote.find_all('a', class_='tag')]}
            for quote in quotes]

def scrape_dynamic_website(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        content = page.content()
        soup = BeautifulSoup(content, 'html.parser')
        browser.close()
        return scrape_static_website(url)  # Reuse static scraping logic after loading dynamic content

def get_db_cursor():
    try:
        return mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    except Exception as e:
        flash("Database connection error!", "danger")
        return None

def validate_url(url):
    try:
        parsed = HttpUrl(url=url)
        return parsed
    except ValidationError:
        flash("Invalid URL format!", "danger")
        return None

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
            return redirect(url_for('scrape'))
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
        # Store both token and email in session
        session['reset_token'] = token
        session['reset_email'] = email
        reset_link = url_for('reset_password', token=token, _external=True)
        msg = Message("Password Reset Request", recipients=[email])
        msg.body = f"Click the link below to reset your password:\n{reset_link}"
        mail.send(msg)

        flash("Password reset link sent to your email!", "success")
        return redirect(url_for('login'))

    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Verify token and check if reset_email exists in session
    if 'reset_token' not in session or 'reset_email' not in session or session['reset_token'] != token:
        flash("Invalid or expired reset link!", "danger")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form['password'].strip()

        if len(new_password) < 8 or not re.search(r"[A-Za-z]", new_password) or not re.search(r"[0-9]", new_password):
            flash("Password must be at least 8 characters long and contain both letters and numbers!", "danger")
            return redirect(url_for('reset_password', token=token))

        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, session['reset_email']))
        mysql.connection.commit()
        cursor.close()

        # Clear reset token and email from session
        session.pop('reset_token', None)
        session.pop('reset_email', None)

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
def add_security_headers(response):
    response.headers.update({
        'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
        'Pragma': 'no-cache',
        'Expires': '0',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block'
    })
    return response

# ==================== DASHBOARD ROUTES ==================== #
@app.route('/ecommerce-analysis')
def ecommerce_analysis():
    if 'user_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))
    return render_template('ecommerce_analysis.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))

    cursor = get_db_cursor()
    if not cursor:
        return redirect(url_for('home'))

    # Get user's scraping statistics
    cursor.execute("""
        SELECT COUNT(*) as total_scrapes 
        FROM scraping_history 
        WHERE user_id = %s
    """, (session['user_id'],))
    scraping_stats = cursor.fetchone()

    cursor.execute("""
        SELECT COUNT(*) as total_searches 
        FROM serp_searches 
        WHERE user_id = %s
    """, (session['user_id'],))
    serp_stats = cursor.fetchone()

    cursor.execute("""
        SELECT * FROM scraping_history 
        WHERE user_id = %s 
        ORDER BY date DESC LIMIT 5
    """, (session['user_id'],))
    recent_searches = cursor.fetchall()

    cursor.close()

    return render_template('dashboard.html',
                         username=session['username'],
                         scraping_stats=scraping_stats,
                         serp_stats=serp_stats,
                         recent_searches=recent_searches)

# ==================== WEB SCRAPING ==================== #
@app.route('/scrape', methods=['GET', 'POST'])
def scrape():
    if 'user_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        url = request.form['url'].strip()
        validated_url = validate_url(url)
        if not validated_url:
            return redirect(url_for('scrape'))

        try:
            # Extract domain from the URL string directly
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            template = predefined_templates.get(domain)

            results = (scrape_static_website(url) if template and template['static'] 
                      else scrape_dynamic_website(url) if template 
                      else scrape_dynamic_website(url) if is_dynamic_website(url) 
                      else scrape_static_website(url))

            if results:
                cursor = get_db_cursor()
                if cursor:
                    cursor.execute(
                        "INSERT INTO scraping_history (user_id, url, results, date) VALUES (%s, %s, %s, NOW())",
                        (session['user_id'], url, json.dumps(results))
                    )
                    mysql.connection.commit()
                    history_id = cursor.lastrowid
                    cursor.close()
                    
                    flash("Scraping completed successfully!", "success")
                    return render_template('results.html', results=results, url=url, history_id=history_id)
            
            flash("No results found from the website!", "warning")
            return redirect(url_for('scrape'))
            
        except Exception as e:
            flash(f"Failed to scrape the website: {str(e)}", "danger")
            return redirect(url_for('scrape'))

    return render_template('scrape.html')

# ==================== REAL-TIME SCRAPING ==================== #
@app.route('/real_time_scrape', methods=['GET', 'POST'])
def real_time_scrape():
    if 'user_id' not in session:  # Add authentication check
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            url = request.form['url'].strip()
            if not url:
                flash("URL is required!", "danger")
                return redirect(url_for('real_time_scrape'))

            websocket_url = "ws://localhost:5000/scraping_updates"
            asyncio.run(scraper.real_time_scrape(url, websocket_url))
            return render_template('scrape.html')
        except Exception as e:
            flash(f"Scraping failed: {str(e)}", "danger")
            return redirect(url_for('real_time_scrape'))

    return render_template('scrape.html')

# ==================== SCRAPING HISTORY ==================== #
@app.route('/history', methods=['GET'])
def history():
    if 'user_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))

    cursor = get_db_cursor()
    if not cursor:
        return redirect(url_for('home'))

    user_id = session['user_id']
    sort = request.args.get('sort', 'date')
    order = request.args.get('order', 'desc')

    # Validate sort and order parameters to prevent SQL injection
    allowed_sort_fields = {'date', 'url'}
    allowed_order_types = {'asc', 'desc'}

    if sort not in allowed_sort_fields:
        sort = 'date'
    if order not in allowed_order_types:
        order = 'desc'

    # Use parameterized query with format strings for column names
    if sort == 'date':
        query = "SELECT * FROM scraping_history WHERE user_id = %s ORDER BY date " + order
    else:
        query = "SELECT * FROM scraping_history WHERE user_id = %s ORDER BY url " + order
    
    cursor.execute(query, [user_id])
    history = cursor.fetchall()
    cursor.close()

    # Format dates for display
    for entry in history:
        if entry['date']:
            entry['date'] = entry['date'].strftime('%Y-%m-%d %H:%M:%S')
        try:
            # Parse JSON results for better display
            entry['results'] = json.loads(entry['results'])
        except (json.JSONDecodeError, TypeError):
            # Keep original results if JSON parsing fails
            pass

    return render_template('history.html', 
                         history=history,
                         current_sort=sort,
                         current_order=order)

# ==================== EXPORT DATA ==================== #
@app.route('/export', methods=['POST'])
def export():
    if 'user_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))

    try:
        data_format = request.form.get('format')
        data_str = request.form.get('data')
        
        if not data_str:
            flash("No data to export!", "warning")
            return redirect(url_for('history'))

        data = json.loads(data_str)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if data_format == 'json':
            response = app.response_class(
                response=json.dumps(data, indent=2),
                mimetype='application/json'
            )
            filename = f'scraping_results_{timestamp}.json'
            
        elif data_format == 'csv':
            si = StringIO()
            cw = csv.writer(si)
            
            # Handle different data structures
            if isinstance(data, list):
                if all(isinstance(item, str) for item in data):
                    cw.writerow(["Result"])
                    for item in data:
                        cw.writerow([item])
                elif all(isinstance(item, dict) for item in data):
                    headers = set().union(*(d.keys() for d in data))
                    cw.writerow(headers)
                    for item in data:
                        cw.writerow([item.get(header, '') for header in headers])
            elif isinstance(data, dict):
                cw.writerows(data.items())
            
            response = app.response_class(
                response=si.getvalue(),
                mimetype='text/csv'
            )
            filename = f'scraping_results_{timestamp}.csv'
            
        else:
            flash("Invalid export format!", "danger")
            return redirect(url_for('history'))

        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

    except json.JSONDecodeError:
        flash("Error processing data for export!", "danger")
        return redirect(url_for('history'))
    except Exception as e:
        flash(f"Export failed: {str(e)}", "danger")
        return redirect(url_for('history'))

@app.route('/preview/<int:history_id>')
def preview(history_id):
    if 'user_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))
    
    try:
        # Fetch the specific scraping result from database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT url, results, date 
            FROM scraping_history 
            WHERE id = %s AND user_id = %s
        """, (history_id, session['user_id']))
        
        result = cursor.fetchone()
        cursor.close()
        
        if not result:
            flash("Preview not found or unauthorized access!", "danger")
            return redirect(url_for('history'))
        
        # Parse the JSON results
        try:
            parsed_results = json.loads(result['results'])
            formatted_date = result['date'].strftime('%Y-%m-%d %H:%M:%S')
            
            return render_template('preview.html', 
                                 results=parsed_results,
                                 url=result['url'],
                                 date=formatted_date)
        except json.JSONDecodeError:
            flash("Error parsing results data!", "danger")
            return redirect(url_for('history'))
            
    except Exception as e:
        flash(f"Error accessing preview: {str(e)}", "danger")
        return redirect(url_for('history'))

@app.route('/api/preview/<int:history_id>')
def api_preview(history_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    cursor = get_db_cursor()
    if not cursor:
        return jsonify({'error': 'Database error'}), 500
        
    cursor.execute("""
        SELECT results 
        FROM scraping_history 
        WHERE id = %s AND user_id = %s
    """, (history_id, session['user_id']))
    
    result = cursor.fetchone()
    cursor.close()
    
    if not result:
        return jsonify({'error': 'Not found'}), 404
        
    try:
        return jsonify(json.loads(result['results']))
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid data format'}), 500

@app.route('/export/<int:history_id>/<format>')
def export_data(history_id, format):
    if 'user_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))

    cursor = get_db_cursor()
    if not cursor:
        return redirect(url_for('history'))

    cursor.execute("""
        SELECT results, url 
        FROM scraping_history 
        WHERE id = %s AND user_id = %s
    """, (history_id, session['user_id']))
    
    result = cursor.fetchone()
    cursor.close()

    if not result:
        flash("Data not found!", "error")
        return redirect(url_for('history'))

    try:
        data = json.loads(result['results'])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'json':
            response = app.response_class(
                response=json.dumps(data, indent=2),
                mimetype='application/json'
            )
            filename = f'scraping_results_{timestamp}.json'
            
        elif format == 'csv':
            si = StringIO()
            writer = csv.writer(si)
            
            # Handle different data structures
            if isinstance(data, list):
                if data and isinstance(data[0], dict):
                    headers = list(data[0].keys())
                    writer.writerow(headers)
                    for row in data:
                        writer.writerow([row.get(header, '') for header in headers])
                else:
                    writer.writerow(['Data'])
                    writer.writerows([[item] for item in data])
            elif isinstance(data, dict):
                writer.writerow(['Key', 'Value'])
                writer.writerows(data.items())
            
            response = app.response_class(
                response=si.getvalue(),
                mimetype='text/csv'
            )
            filename = f'scraping_results_{timestamp}.csv'
        else:
            flash("Invalid export format!", "error")
            return redirect(url_for('history'))

        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        flash(f"Export failed: {str(e)}", "error")
        return redirect(url_for('history'))

# ==================== SERP SEARCH ==================== #
@app.route('/serp', methods=['GET'])
def serp_search_page():
    if 'user_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))
    
    return render_template('serp_search.html', 
                         serp_templates=SERP_TEMPLATES)

@app.route('/api/serp_search', methods=['POST'])
def serp_search():
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400

        search_type = data.get('searchType')
        query = data.get('searchQuery')
        location = data.get('location', '')

        if not search_type or not query:
            return jsonify({'error': 'Missing required parameters'}), 400

        if search_type in ['product_search', 'local_business'] and not location:
            return jsonify({'error': 'Location is required for this search type'}), 400

        results = None
        try:
            if search_type == 'product_search':
                results = asyncio.run(serp_scraper.get_shopping_results(query, location))
            elif search_type == 'news_search':
                results = asyncio.run(serp_scraper.get_news_results(query))
            elif search_type == 'local_business':
                results = asyncio.run(serp_scraper.get_local_results(query, location))

            if not results:
                return jsonify({'error': 'No results found'}), 404

            # Store the search results in the database
            cursor = get_db_cursor()
            if cursor:
                cursor.execute(
                    "INSERT INTO serp_searches (user_id, search_type, query, results, date) VALUES (%s, %s, %s, %s, NOW())",
                    (session['user_id'], search_type, query, json.dumps(results))
                )
                mysql.connection.commit()
                cursor.close()

            return jsonify(results)

        except Exception as e:
            return jsonify({'error': f'Search failed: {str(e)}'}), 500

    except Exception as e:
        return jsonify({'error': f'Invalid request: {str(e)}'}), 400

@app.route('/news-monitoring')
def news_monitoring():
    if 'user_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))
    return render_template('news_monitoring.html')

if __name__ == '__main__':
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )
    app.run(debug=True)