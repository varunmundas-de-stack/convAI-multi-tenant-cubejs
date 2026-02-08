"""
Authentication and RBAC for multi-client system
"""
import sqlite3
import bcrypt
from typing import Optional, Dict
from flask_login import UserMixin


class User(UserMixin):
    """User class for Flask-Login"""

    def __init__(self, user_id: int, username: str, email: str,
                 full_name: str, client_id: str, role: str):
        self.id = user_id  # Required by Flask-Login
        self.username = username
        self.email = email
        self.full_name = full_name
        self.client_id = client_id
        self.role = role

    def get_id(self):
        """Required by Flask-Login"""
        return str(self.id)

    def __repr__(self):
        return f"<User {self.username} (client={self.client_id})>"


class AuthManager:
    """Manage user authentication and authorization"""

    def __init__(self, db_path: str = "database/users.db"):
        self.db_path = db_path

    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password
        Returns User object if successful, None otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get user from database
        cursor.execute("""
            SELECT user_id, username, password_hash, email, full_name,
                   client_id, role, is_active
            FROM users
            WHERE username = ?
        """, (username,))

        result = cursor.fetchone()
        conn.close()

        if not result:
            return None

        user_id, username, password_hash, email, full_name, client_id, role, is_active = result

        # Check if user is active
        if not is_active:
            return None

        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
            return None

        # Update last login
        self._update_last_login(user_id)

        return User(user_id, username, email, full_name, client_id, role)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID (for Flask-Login user_loader)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, username, email, full_name, client_id, role
            FROM users
            WHERE user_id = ? AND is_active = 1
        """, (user_id,))

        result = cursor.fetchone()
        conn.close()

        if not result:
            return None

        return User(*result)

    def get_client_config(self, client_id: str) -> Optional[Dict]:
        """Get client configuration"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT client_id, client_name, schema_name, database_path, config_path
            FROM clients
            WHERE client_id = ? AND is_active = 1
        """, (client_id,))

        result = cursor.fetchone()
        conn.close()

        if not result:
            return None

        return {
            'client_id': result[0],
            'client_name': result[1],
            'schema_name': result[2],
            'database_path': result[3],
            'config_path': result[4]
        }

    def _update_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET last_login = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (user_id,))
        conn.commit()
        conn.close()

    def log_query(self, user_id: int, username: str, client_id: str,
                  question: str, sql_query: str, success: bool,
                  error_message: str = None):
        """Log user query to audit log"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO audit_log
            (user_id, username, client_id, question, sql_query, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, client_id, question, sql_query, success, error_message))

        conn.commit()
        conn.close()
