from flask import Flask, render_template, jsonify, request, flash, session, redirect, url_for
from database import get_connection
import base64
import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import re
from typing import List, Optional

class Product:
    def __init__(self):
        self.conn = None

    def database_connection(self):
        self.conn = get_connection()
        return self.conn

    def fetch_products(self, query, params=None):
        try:
            conn = self.database_connection()
            with conn.cursor() as cursor:
                # Ensure params is a tuple
                if params:
                    print(f"Executing query with params: {params}")
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                products = cursor.fetchall()

                # Convert image_data to Base64
                for product in products:
                    if product["image_data"]:
                        product["image_data"] = base64.b64encode(product["image_data"]).decode('utf-8')
                return products
        except Exception as e:
            print(f"Error fetching products: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_products(self):
        query = """SELECT product_id, name, description, image_data, price, category_id FROM products"""
        return self.fetch_products(query)

    def get_product_details(self, product_ids: list) -> list:
        if not isinstance(product_ids, list):
            product_ids = [product_ids]

        conn = self.database_connection()
        with conn.cursor() as cursor:
            try:
                placeholders = ','.join(['%s'] * len(product_ids))
                query = f"""
                    SELECT product_id, name, description, image_data, price 
                    FROM products 
                    WHERE product_id IN ({placeholders})
                """
                cursor.execute(query, product_ids)
                products = cursor.fetchall()
                for product in products:
                    if product["image_data"]:
                        product["image_data"] = base64.b64encode(product["image_data"]).decode('utf-8')
                return products
                # return cursor.fetchall()
            except Exception as e:
                print(f"Database error: {e}")
                return []

    def get_product_by_category(self, category_id):
        query = "SELECT product_id, name, description, image_data, price FROM products WHERE category_id = %s"
        return self.fetch_products(query, (category_id,))

    def get_flash_sale_products(self):
        query = "SELECT product_id, name, description, image_data, price FROM products WHERE on_flash_sale = 1"
        return self.fetch_products(query)

    def get_all_products(self):
        query = "SELECT product_id, name, description, image_data, price, category_id FROM products"
        return self.fetch_products(query)

    def get_product_by_barcode(self, barcode):
        print(f"Looking up product with barcode: {barcode}")
        query = "SELECT * FROM products WHERE barcode = %s AND barcode IS NOT NULL"
        return self.fetch_products(query, (barcode,))
    
    def search_product_by_id(self, product_id):
        query = "SELECT * FROM products WHERE product_id = %s"
        return self.fetch_products(query, product_id)
