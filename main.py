from flask import Flask, render_template, jsonify, request, flash, session, redirect, url_for
from database import get_connection
from flask_cors import CORS
import re
from order import Order
from product import Product
from authenticate import Authenticate
from typing import List, Optional

class FlaskApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'Raphael'
        CORS(self.app)

        self.product_manager = Product()
        self.auth_manager = Authenticate()
        self.order_manager = Order()

        self.register_routes()

    def register_routes(self):
        # Main routes
        self.app.route('/')(self.index)
        self.app.route('/product/<int:product_id>')(self.get_products_details)
        self.app.route('/order_details', methods=['GET'])(self.get_orders_details)

        # Auth routes
        self.app.route('/login', methods=['GET'])(self.login_page)
        self.app.route('/login', methods=['POST'])(self.login)
        self.app.route('/register', methods=['POST'])(self.register)

        # Order routes
        self.app.route('/checkout', methods=['POST'])(self.checkout)
        self.app.route('/my_orders', methods=['GET', 'POST'])(self.my_orders)

        # API routes
        self.app.route('/api/small_banners', methods=['GET'])(self.api_small_banners)
        self.app.route('/api/all_products', methods=['GET'])(self.api_all_products)
        self.app.route('/get_products_by_barcode', methods=['GET'])(self.get_products_by_barcode)
        self.app.route('/search', methods=['GET'])(self.get_searched_products)

    def index(self):
        banners = self.product_manager.get_product_by_category(1)
        small_banners = self.product_manager.get_product_by_category(3)
        flash_sale_products = self.product_manager.get_flash_sale_products()
        multiple_slider = self.product_manager.get_product_by_category(5)

        return render_template(
            'index.html',
            products=flash_sale_products,
            small_banners=small_banners,
            multiple_slider=multiple_slider,
            banners=banners
        )

    def get_products_details(self, product_id):
        product_details = self.product_manager.get_product_details(product_id)
        if product_details:
            return render_template('product_details.html', product_details=product_details)
        return "Product not found", 404

    def get_orders_details(self):
        try:
            product_ids_str = request.args.get('product_ids', '')
            if not product_ids_str:
                return "No product IDs provided", 400

            product_ids_list = [int(pid.strip()) for pid in product_ids_str.split(',')]
            order_details = self.product_manager.get_product_details(product_ids_list)

            if order_details:
                return render_template('order_details.html', order_details=order_details)
            return "Products not found", 404

        except ValueError:
            return "Invalid product IDs", 400
    
    def get_products_by_barcode(self):
        try:
            # Get the barcode from the request arguments
            barcode = request.args.get('barcode')
            if not barcode:
                return jsonify({"error": "Barcode is required"}), 400

            # Call the product manager to fetch the product
            product = self.product_manager.get_product_by_barcode(barcode)
            if product:
                return jsonify(product), 200
            else:
                return jsonify({"error": "Product not found"}), 404
        except Exception as e:
            print(f"Error fetching product: {e}")
            return jsonify({"error": "An error occurred"}), 500
    
    def get_searched_products(self):
        product_id = request.args.get('product_id')
        if not product_id:
            return jsonify({"error": "Product_id is required"}), 400
        
        # Call the product manger to fetch the searched product
        searched_product = self.product_manager.search_product_by_id(product_id)
        if searched_product:
            return jsonify(searched_product), 200
        else:
            return jsonify({"error": "Product not found"}), 400

    def login_page(self):
        return render_template('login.html')

    def login(self):
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and Password are required"}), 400

        user, error = self.auth_manager.login(email, password)
        if error:
            return jsonify({"error": error}), 401

        session['user_id'] = user['user_id']
        session['user_type'] = user['role']
        redirect_url = 'index' if user['role'] == 'admin' else 'index'
            # Return user data in response
        return jsonify({
            "message": "Login successful",
            "user_id": user['user_id'],  # Add this line
            "email": email,              # Add this line
            "role": user['role'],        # Add this line
            "redirect_url": url_for('index' if user['role'] == 'admin' else 'index')
        }), 200

    def register(self):
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        success, errors = self.auth_manager.register(
            data.get('username'),
            data.get('reg_email'),
            data.get('reg_password'),
            data.get('repeat_password')
        )

        if not success:
            return jsonify({"errors": errors}), 400

        return jsonify({
            "message": "Registration Successful",
            "redirect_url": url_for('index')
        }), 200

    def checkout(self):
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        data = request.get_json()
        product_ids = data.get('product_ids', [])
        total_cost = data.get('total_cost', 0.0)
        product_quantities = data.get('product_quantities', {})

        if not product_ids or total_cost <= 0:
            return jsonify({"error": "Invalid product data"}), 400

        success, error = self.order_manager.create_order(
            user_id, product_ids, total_cost, product_quantities)

        if not success:
            return jsonify({"error": error}), 500

        return jsonify({
            "message": "Order placed successfully",
            "redirect_url": url_for('my_orders')
        }), 200

    def my_orders(self):
        if "user_id" not in session:
            return redirect("/login")

        products = self.order_manager.get_user_orders(session["user_id"])
        return render_template('my_orders.html', products=products)

    def api_small_banners(self):
        small_banners = self.product_manager.get_product_by_category(3)
        return jsonify(small_banners)

    def api_all_products(self):
        products = self.product_manager.get_all_products()
        return jsonify(products)

    def run(self, host='0.0.0.0', port=5000, debug=True):
        self.app.run(host=host, port=port, debug=debug)
        
flask_app = FlaskApp()
app = flask_app.app  # Required for Gunicorn

if __name__ == '__main__':
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))