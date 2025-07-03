from flask import Flask, render_template, jsonify, request, flash, session, redirect, url_for
from database import get_connection
import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
import re

class Authenticate:
    def __init__(self):
        self.conn = None

    def _get_connection(self):
        self.conn = get_connection()
        return self.conn

    @staticmethod
    def validate_email(email):
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(email_regex, email)

    @staticmethod
    def validate_password(password, repeat_password):
        errors = []
        if password != repeat_password:
            errors.append("Passwords do not match.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        if not re.search(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', password):
            errors.append("Password must contain at least one letter and one number.")
        return errors

    def login(self, email, password):
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()

                if not user:
                    return None, "User not found"

                if user['status'] != 'approved':
                    return None, "Account not approved. Contact admin."

                if check_password_hash(user['password'], password):
                    return user, None

                return None, "Invalid password"
        finally:
            if self.conn:
                self.conn.close()

    def register(self, username, email, password, repeat_password):
        errors = []
        if not username or not email or not password or not repeat_password:
            errors.append("All fields are required.")

        if email and not self.validate_email(email):
            errors.append("Email is not valid.")

        password_errors = self.validate_password(password, repeat_password)
        errors.extend(password_errors)

        if errors:
            return False, errors

        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    return False, ["Email already exists!"]

                password_hash = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                    (username, email, password_hash)
                )
                conn.commit()
                return True, None
        finally:
            if self.conn:
                self.conn.close()

