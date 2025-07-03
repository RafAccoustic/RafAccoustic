from flask import Flask, render_template, jsonify,request, flash ,session ,redirect ,url_for
from database import get_connection
import base64
import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import re

class Order:
    def __init__(self):
        self.conn = None

    def database_connection(self):
        self.conn = get_connection()
        return self.conn

    def create_order(self, user_id, product_ids, total_cost, product_quantities):
        try:
            conn = self.database_connection()
            cursor = conn.cursor()
            conn.begin()

            cursor.execute("INSERT INTO orders (user_id, total) VALUES (%s, %s)",
                           (user_id, total_cost))
            order_id = cursor.lastrowid

            for product_id in product_ids:
                cursor.execute("SELECT price FROM products WHERE product_id = %s",
                               (product_id,))
                price_data = cursor.fetchone()
                if not price_data:
                    conn.rollback()
                    return False, f"Product with ID {product_id} not found"

                price = price_data['price']
                quantity = product_quantities.get(str(product_id), 1)

                cursor.execute(
                    """INSERT INTO order_details (order_id, product_id, quantity, price) 
                    VALUES (%s, %s, %s, %s)""",
                    (order_id, product_id, quantity, price)
                )

                cursor.execute("UPDATE products SET category_id = 4 WHERE product_id = %s",
                               (product_id,))

            conn.commit()
            return True, None
        except Exception as e:
            conn.rollback()
            return False, str(e)
        # finally:
        #     if self.conn:
        #         self.conn.close()

    def get_user_orders(self, user_id):
        query = """
            SELECT p.product_id, p.name, p.description, p.price, p.image_data
            FROM products p
            JOIN order_details od ON p.product_id = od.product_id
            JOIN orders o ON od.order_id = o.order_id
            WHERE p.category_id = 4 AND o.user_id = %s
        """
        try:
            conn = self.database_connection()
            with conn.cursor() as cursor:
                cursor.execute(query, (user_id,))
                products = cursor.fetchall()
                for product in products:
                    if product["image_data"]:
                        product["image_data"] = base64.b64encode(product["image_data"]).decode('utf-8')
                return products
        finally:
            if self.conn:
                self.conn.close()
