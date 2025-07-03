from flask import Flask, render_template, jsonify, request, flash, session, redirect, url_for
from database import get_connection
import base64
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import re


class Product:
    def __init__(self):
        self.conn = None

    def _get_connection(self):
        self.conn = get_connection()
        return self.conn

    def _fetch_products(self, query, params=None):
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                products = cursor.fetchall()

                for product in products:
                    if product["image_data"]:
                        product["image_data"] = base64.b64encode(product["image_data"]).decode('utf-8')
                return products
        except Exception as e:
            print(f"Error fetching products: {e}")
            return []
        finally:
            if self.conn:
                self.conn.close()

    def get_all_products(self):
        query = "SELECT product_id, name, description, image_data, price, category_id FROM products"
        return self._fetch_products(query)

    def get_product_details(self, product_id):
        query = """
            SELECT product_id, name, description, image_data, price
            FROM products WHERE product_id = %s
        """
        return self._fetch_products(query, (product_id,))

    def get_products_by_category(self, category_id):
        query = """
            SELECT product_id, name, description, image_data, price 
            FROM products 
            WHERE category_id = %s
        """
        return self._fetch_products(query, (category_id,))

    def get_flash_sale_products(self):
        query = "SELECT product_id, name, description, image_data, price FROM products WHERE on_flash_sale = 1"
        return self._fetch_products(query)


class Auth:
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


class Order:
    def __init__(self):
        self.conn = None

    def _get_connection(self):
        self.conn = get_connection()
        return self.conn

    def create_order(self, user_id, product_ids, total_cost, product_quantities):
        try:
            conn = self._get_connection()
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
        finally:
            if self.conn:
                self.conn.close()

    def get_user_orders(self, user_id):
        query = """
            SELECT p.product_id, p.name, p.description, p.price, p.image_data
            FROM products p
            JOIN order_details od ON p.product_id = od.product_id
            JOIN orders o ON od.order_id = o.order_id
            WHERE p.category_id = 4 AND o.user_id = %s
        """
        try:
            conn = self._get_connection()
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


class FlaskApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'Raphael'
        CORS(self.app)

        self.product_manager = Product()
        self.auth_manager = Auth()
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

    def index(self):
        banners = self.product_manager.get_products_by_category(1)
        small_banners = self.product_manager.get_products_by_category(3)
        flash_sale_products = self.product_manager.get_flash_sale_products()
        multiple_slider = self.product_manager.get_products_by_category(5)

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
        product_ids_str = request.args.get('product_ids', '')
        if not product_ids_str:
            return "No product IDs provided", 400

        product_ids_list = list(map(int, product_ids_str.split(',')))
        order_details = self.product_manager.get_product_details(product_ids_list)

        if order_details:
            return render_template('order_details.html', order_details=order_details)
        return "Products not found", 404

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
        return jsonify({"message": "Login successful", "redirect_url": url_for(redirect_url)}), 200

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
        small_banners = self.product_manager.get_products_by_category(3)
        return jsonify(small_banners)

    def api_all_products(self):
        products = self.product_manager.get_all_products()
        return jsonify(products)

    def run(self, host='0.0.0.0', port=5000, debug=True):
        self.app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    app = FlaskApp()
    app.run()