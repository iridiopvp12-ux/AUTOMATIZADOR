import sqlite3
import bcrypt
from .logger import log_action

DB_FILE = "contabilidade.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash BLOB NOT NULL,
        is_admin BOOLEAN NOT NULL DEFAULT 0,
        permissions TEXT
    )
    ''')

    conn.commit()
    conn.close()

def create_user(username, password, is_admin=False, permissions=""):
    """
    Creates a new user.
    permissions: comma-separated string, e.g. "dashboard,sped"
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

    try:
        cursor.execute('''
        INSERT INTO users (username, password_hash, is_admin, permissions)
        VALUES (?, ?, ?, ?)
        ''', (username, hashed, is_admin, permissions))
        conn.commit()
        log_action(f"User created: {username} (Admin: {is_admin})")
        return True
    except sqlite3.IntegrityError:
        log_action(f"Failed to create user: {username} already exists")
        return False
    finally:
        conn.close()

def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def verify_password(stored_hash, password):
    """
    Verifies a password against the stored hash.
    """
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

def initialize_db():
    create_tables()
    # Check if admin exists
    if not get_user_by_username("admin"):
        print("Creating default admin user...")
        create_user("admin", "admin", is_admin=True, permissions="all")
