from flask import Flask, request, render_template
import redis
import mysql.connector
import os
import time

app = Flask(__name__)

# Redis setup
r = redis.StrictRedis(host=os.environ.get("REDIS_HOST", "redis"), port=6379, db=0)

# MySQL setup with retry logic
def get_db():
    attempts = 0
    while attempts < 5:
        try:
            conn = mysql.connector.connect(
                host=os.environ.get('DB_HOST', 'db'),
                user=os.environ.get('DB_USER', 'user'),
                password=os.environ.get('DB_PASSWORD', 'password'),
                database=os.environ.get('DB_NAME', 'mydatabase')
            )
            return conn
        except mysql.connector.Error as err:
            print(f"Database connection failed: {err}")
            attempts += 1
            time.sleep(5)  # Wait before retrying
    raise Exception("Could not connect to the database after multiple attempts.")

# Create users table if not exists
def init_db():
    print("Initializing database...")
    time.sleep(15)  # Initial wait to ensure DB readiness
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL
            )
        ''')
        conn.commit()
    print("Database initialized.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_user', methods=['POST'])
def add_user():
    username = request.form['username']
    
    # Add user to MySQL and get user ID
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username) VALUES (%s)', (username,))
        conn.commit()
        user_id = cursor.lastrowid  # Get the ID of the inserted user

    # Add user to Redis with user ID as the key
    r.set(user_id, username)
    
    return render_template('index.html', message=f"User {username} added with ID {user_id}")

@app.route('/user/<int:user_id>')
def user_info(user_id):
    # First, check Redis for the user
    username = r.get(user_id)
    
    if username:
        return render_template('user.html', user_id=user_id, name=username.decode('utf-8'), source='Redis')
    
    # If not found in Redis, check MySQL
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
    
    if user:
        return render_template('user.html', user_id=user[0], name=user[1], source='MySQL')
    else:
        return "User not found", 404

if __name__ == '__main__':
    init_db()  # Make sure table exists before starting the app
    app.run(host='0.0.0.0', port=7070, debug=True)
