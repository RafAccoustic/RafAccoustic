from flask import Flask, render_template, jsonify,request, flash ,session ,redirect ,url_for
from database import get_connection
import base64
import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import re

app = Flask(__name__)
app.secret_key = 'Raphael'
CORS(app)  #

def fetch_products(query):
    """
    Fetch products from the database based on the query, encode image_data to Base64,
    and return the products as a list of dictionaries.
    """
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
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

def get_products():
    """
        Fetch small banners from the database.
        """
    query = """
            SELECT product_id, name, description, image_data, price, category_id
            FROM products
        """
    return fetch_products(query)

@app.route('/product/<int:product_id>')
def get_products_details(product_id):
    """
        Fetch small banners from the database.
        """
    query = f"""
            SELECT product_id, name, description, image_data, price
            FROM products WHERE product_id = {product_id}
            """
    product_details = fetch_products(query)
    if product_details:
        return render_template('product_details.html', product_details=product_details)
    else:
        return "Product not found", 404

@app.route('/order_details', methods=['GET'])
def get_orders_details():
    product_ids_str = request.args.get('product_ids', '')
    if product_ids_str:
        product_ids_list = list(map(int, product_ids_str.split(',')))
        query = f"SELECT product_id, name, description, image_data, price FROM products WHERE product_id IN ({','.join(map(str, product_ids_list))})"
        order_details = fetch_products(query)

        if order_details:
            return render_template('order_details.html', order_details=order_details)
        else:
            return "Products not found", 404
    else:
        return "No product IDs provided", 400

def get_banners():
    """
        Fetch small banners from the database.
        """
    query = """
            SELECT product_id, name, description, image_data, price 
            FROM products 
            WHERE category_id = 1
        """
    return fetch_products(query)

def get_small_banners():
    """
    Fetch small banners from the database.
    """
    query = """
        SELECT product_id, name, description, image_data, price 
        FROM products 
        WHERE category_id = 3
    """
    return fetch_products(query)

def get_flash_sale_products():
    """
    Fetch products on flash sale from the database.
    """
    query = """
        SELECT product_id, name, description, image_data, price 
        FROM products 
        WHERE on_flash_sale = 1
    """
    return fetch_products(query)

def get_multiple_slider():
    """
    Fetch multiple slider products from the database.
    """
    query = """
        SELECT product_id, name, description, image_data, price 
        FROM products 
        WHERE category_id = 5
    """
    return fetch_products(query)

@app.route('/')
def index():
    """
    Render the homepage with flash sale products, small banners, and multiple slider.
    """
    banners = get_banners()
    small_banners = get_small_banners()
    flash_sale_products = get_flash_sale_products()
    multiple_slider = get_multiple_slider()
    return render_template(
        'index.html',
        products=flash_sale_products,
        small_banners=small_banners,
        multiple_slider=multiple_slider,
        banners=banners
    )

@app.route('/api/small_banners', methods=['GET'])
def api_small_banners():
    """
    API endpoint to fetch small banners.
    """
    small_banners = get_small_banners()
    return jsonify(small_banners)

@app.route('/api/all_products', methods=['GET'])
def api_all_products():
    """
    API endpoint to fetch small banners.
    """
    flash_sales = get_products()
    return jsonify(flash_sales)

# Route to display the login page
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')  # Create this HTML template

# Login route for form submission
@app.route('/login', methods=['POST'])
def login():
    print("Received login request")  # Debug print

    if not request.is_json:
        print("Request is not JSON")  # Debug print
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    print(f"Received data: {data}")  # Debug print

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        print("Missing email or password")  # Debug print
        return jsonify({"error": "Email and Password are required"}), 400

    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            print(f"Found user: {user}")  # Debug print

        if user:
            if user['status'] != 'approved':
                return jsonify({"error": "Account not approved. Contact admin."}), 403

            if check_password_hash(user['password'], password):
                session['user_id'] = user['user_id']
                session['user_type'] = user['role']
                redirect_url = 'index' if user['role'] == 'admin' else 'index'
                return jsonify({"message": "Login successful", "redirect_url": url_for(redirect_url)}), 200
            else:
                return jsonify({"error": "Invalid password"}), 401
        else:
            return jsonify({"error": "User not found"}), 404

    except Exception as e:
        print(f"Error occurred: {str(e)}")  # Debug print
        return jsonify({"error": "An error occurred", "details": str(e)}), 500
    finally:
        if 'connection' in locals() and connection:
            connection.close()

# Registration
@app.route('/register', methods=['POST'])
def register():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    print(f"Received data: {data}")  # Debug log
    username = data.get('username')
    email = data.get('reg_email')
    password = data.get('reg_password')
    # print(len(password))
    password_repeat = data.get('repeat_password')

    errors = []

    # Validation checks
    if not username or not email or not password or not password_repeat:
        errors.append("All fields are required.")

    if email and not validate_email(email):
        errors.append("Email is not valid.")

    validate_password(errors, password ,password_repeat)
    # Check if the email already exists in the database
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if user:
        errors.append("Email already exists!")

    if errors:
        print(f"Validation errors: {errors}")  # Debug log
        return jsonify({"errors": errors}), 400
    else:
        # Hash the password
        password_hash = generate_password_hash(password)

        # Insert the user into the database
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                       (username, email, password_hash))
        connection.commit()

        redirect_url = 'index'
        return jsonify({"message": "Registration Successful", "redirect_url": url_for(redirect_url)}), 200

def validate_email(email):
    """Validate email format using regular expression."""
    import re
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email)

def validate_password(errors, password, repeat_password):
    """Validate password against complexity requirements."""
    if password != repeat_password:
        errors.append("Passwords do not match.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', password):
        errors.append("Password must contain at least one letter and one number.")
    return errors

# Route to handle order and payment
@app.route('/checkout', methods=['POST'])
def checkout():
    try:
        # Ensure the request is JSON
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()

        # Extract data from the JSON payload
        user_id = session.get('user_id')  # Assuming user_id is stored in session
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        product_ids = data.get('product_ids', [])
        total_cost = data.get('total_cost', 0.0)
        product_quantities = data.get('product_quantities', {})

        # Validate input
        if not product_ids or total_cost <= 0:
            return jsonify({"error": "Invalid product data"}), 400

        # Connect to the database
        conn = get_connection()
        cursor = conn.cursor()

        # Begin transaction
        conn.begin()

        # Insert the order into the orders table
        cursor.execute("INSERT INTO orders (user_id, total) VALUES (%s, %s)", (user_id, total_cost))
        order_id = cursor.lastrowid

        # Process each product
        for product_id in product_ids:
            cursor.execute("SELECT price FROM products WHERE product_id = %s", (product_id,))
            price_data = cursor.fetchone()
            if not price_data:
                conn.rollback()
                return jsonify({"error": f"Product with ID {product_id} not found"}), 400

            price = price_data['price']
            quantity = product_quantities.get(str(product_id), 1)

            cursor.execute(
                "INSERT INTO order_details (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
                (order_id, product_id, quantity, price)
            )

            # Mark product as sold
            cursor.execute("UPDATE products SET category_id = 4 WHERE product_id = %s", (product_id,))

        # Commit transaction
        conn.commit()

        cursor.close()
        conn.close()

        # Redirect to orders page
        return jsonify({"message": "Order placed successfully", "redirect_url": url_for('my_orders')}), 200

    except Exception as e:
        # Rollback on error
        conn.rollback()
        return jsonify({"error": str(e)}), 500

def get_access_token():
    consumer_key = 'mW9pv9rEIzZb0hcwmlAdfMuARAP89i0nYQlFMwPxkbGSVhwW'
    consumer_secret = 'DaA4rdhYz4Ju0Qke1QeHdJ0EiBtxRJtMVRP9XbQPXDItwtHpZpisvNCz4gnomj8N'

    url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    credentials = f"{consumer_key}:{consumer_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        'Authorization': f'Basic {encoded_credentials}'
    }
    response = requests.get(url, headers=headers)
    response_data = response.json()
    return response_data['access_token']

def initiate_mpesa_payment(access_token, amount):
    shortcode = '174379'
    passkey = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'
    phone_number = '254704648873'
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode()

    url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    payload = {
        'BusinessShortCode': shortcode,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': amount,
        'PartyA': phone_number,
        'PartyB': shortcode,
        'PhoneNumber': phone_number,
        'CallBackURL': 'http://abcd1234.ngrok.io/callback/mpesa_callback.php',
        'AccountReference': '123456',
        'TransactionDesc': 'Payment description'
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()

@app.route('/my_orders', methods=['GET', 'POST'])
def my_orders():
    # Check if the user is logged in
    if "user_id" not in session:
        return redirect("/login")

    # Get the logged-in user ID
    user_id = session.get("user_id")

    # Check if product IDs are passed (optional)
    product_ids = request.args.getlist("product_ids")  # Use `getlist` for array-like query params
    if product_ids:
        print("Product IDs:", product_ids)

    # SQL query to fetch sold products for the logged-in user
    query = """
        SELECT p.product_id, p.name, p.description, p.price, p.image_data
        FROM products p
        JOIN order_details od ON p.product_id = od.product_id
        JOIN orders o ON od.order_id = o.order_id
        WHERE p.category_id = 4 AND o.user_id = %s
    """

    try:
        # Connect to the database
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query, (user_id,))
            products = cursor.fetchall()  # Fetch all matching rows
            # Convert image_data to Base64
            for product in products:
                if product["image_data"]:
                    product["image_data"] = base64.b64encode(product["image_data"]).decode('utf-8')
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({"error": "An error occurred while fetching sold products."}), 500
    finally:
        conn.close()

    # Return the products as a JSON response
    return render_template('my_orders.html', products=products)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

