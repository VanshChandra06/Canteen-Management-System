# app.py
import os
import sqlite3
import datetime
from flask import Flask, request, jsonify, g
from flask_cors import CORS

DATABASE = 'canteen.db'

app = Flask(__name__, static_folder='static', static_url_path='/')
CORS(app)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def row_to_dict(row):
    return {k: row[k] for k in row.keys()}

# --------------------------
# Database creation + seeding
# --------------------------
def create_and_seed_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create tables (your schema)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        category_id INT PRIMARY KEY,
        category_name VARCHAR(50),
        description TEXT
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        product_id INT PRIMARY KEY,
        product_name VARCHAR(100),
        description TEXT,
        price DECIMAL(10,2),
        stock INT,
        category_id INT,
        FOREIGN KEY (category_id) REFERENCES categories(category_id)
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INT PRIMARY KEY,
        first_name VARCHAR(50),
        last_name VARCHAR(50),
        email VARCHAR(100),
        phone VARCHAR(15),
        address TEXT,
        created_at TIMESTAMP
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        order_id INT PRIMARY KEY,
        customer_id INT,
        order_date TIMESTAMP,
        total DECIMAL(10,2),
        status TEXT CHECK(status IN ('Pending', 'Completed', 'Cancelled')),
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orderitems (
        order_item_id INT PRIMARY KEY,
        order_id INT,
        product_id INT,
        quantity INT,
        price DECIMAL(10,2),
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        payment_id INT PRIMARY KEY,
        order_id INT,
        amount DECIMAL(10,2),
        payment_date TIMESTAMP,
        payment_method TEXT CHECK(payment_method IN ('Cash', 'Card', 'UPI', 'Cash on Delivery')),
        status TEXT CHECK(status IN ('Success', 'Failed', 'Pending')),
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    );
    ''')

    conn.commit()

    # Seed data only if tables appear empty (safer): check categories count
    cursor.execute('SELECT COUNT(1) FROM categories')
    if cursor.fetchone()[0] == 0:
        # Categories (5 entries)
        categories = [
            (1, 'Chinese', 'Noodles, fried rice and Chinese-style mains.'),
            (2, 'Indian', 'Curries, biryanis, and Indian staples.'),
            (3, 'Continental', 'Sandwiches, pasta, and continental mains.'),
            (4, 'Snacks', 'Quick bites and small-plates.'),
            (5, 'Beverages', 'Hot & cold drinks, juices and shakes.')
        ]
        cursor.executemany('INSERT OR IGNORE INTO categories (category_id, category_name, description) VALUES (?, ?, ?)', categories)
        conn.commit()

    cursor.execute('SELECT COUNT(1) FROM products')
    if cursor.fetchone()[0] == 0:
        # Products (10 entries)
        products = [
            (101, 'Veg Noodles', 'Stir-fried noodles with veggies', 80.00, 30, 1),
            (102, 'Chicken Fried Rice', 'Wok-fried rice with chicken', 120.00, 20, 1),
            (201, 'Paneer Butter Masala', 'Creamy paneer curry with butter', 150.00, 15, 2),
            (202, 'Chicken Biryani', 'Aromatic basmati biryani with chicken', 180.00, 10, 2),
            (301, 'Club Sandwich', 'Multi-layer sandwich with veggies and chicken', 140.00, 25, 3),
            (302, 'Penne Alfredo', 'Pasta in creamy alfredo sauce', 130.00, 18, 3),
            (401, 'French Fries', 'Crispy golden fries', 60.00, 40, 4),
            (402, 'Veg Spring Roll', 'Crispy rolls with mixed veg', 70.00, 35, 4),
            (501, 'Masala Chai', 'Hot spiced tea', 30.00, 100, 5),
            (502, 'Iced Lemon Tea', 'Refreshing iced lemon tea', 45.00, 80, 5)
        ]
        cursor.executemany('INSERT OR IGNORE INTO products (product_id, product_name, description, price, stock, category_id) VALUES (?, ?, ?, ?, ?, ?)', products)
        conn.commit()

    cursor.execute('SELECT COUNT(1) FROM customers')
    if cursor.fetchone()[0] == 0:
        # Customers (6 entries)
        now = datetime.datetime.utcnow().isoformat()
        customers = [
            (1, 'Aarav', 'Sharma', 'aarav.sharma@example.com', '9876543210', 'Block A, Hostel 1', now),
            (2, 'Isha', 'Verma', 'isha.verma@example.com', '9123456780', 'Block B, Hostel 2', now),
            (3, 'Rohan', 'Singh', 'rohan.singh@example.com', '9988776655', 'Block C, Hostel 3', now),
            (4, 'Priya', 'Kaur', 'priya.kaur@example.com', '9012345678', 'Block D, Hostel 4', now),
            (5, 'Vikram', 'Patel', 'vikram.patel@example.com', '8899001122', 'Block E, Hostel 5', now),
            (6, 'Neha', 'Gupta', 'neha.gupta@example.com', '7766554433', 'Block F, Hostel 6', now)
        ]
        cursor.executemany('INSERT OR IGNORE INTO customers (customer_id, first_name, last_name, email, phone, address, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)', customers)
        conn.commit()

    # Orders + orderitems + payments
    cursor.execute('SELECT COUNT(1) FROM orders')
    if cursor.fetchone()[0] == 0:
        # We'll build a few orders and compute totals
        now = datetime.datetime.utcnow().isoformat()
        # Orders: (order_id, customer_id, order_date, total, status)
        orders = [
            (1001, 1, now, None, 'Completed'),
            (1002, 2, now, None, 'Pending'),
            (1003, 3, now, None, 'Completed'),
            (1004, 4, now, None, 'Cancelled'),
            (1005, 5, now, None, 'Pending')
        ]

        # Order items: (order_item_id, order_id, product_id, quantity, price)
        # note: price is per-unit at time of order
        orderitems = [
            (5001, 1001, 101, 2, 80.00),   # 2x Veg Noodles = 160
            (5002, 1001, 501, 2, 30.00),   # 2x Masala Chai = 60  => total 220

            (5003, 1002, 202, 1, 180.00),  # Chicken Biryani = 180
            (5004, 1002, 401, 1, 60.00),   # Fries = 60 => total 240

            (5005, 1003, 201, 1, 150.00),  # Paneer Butter Masala = 150
            (5006, 1003, 301, 1, 140.00),  # Club Sandwich = 140 => total 290

            (5007, 1004, 302, 1, 130.00),  # Penne Alfredo = 130
            (5008, 1004, 402, 2, 70.00),   # 2x Spring Roll = 140 => total 270 (but order cancelled)

            (5009, 1005, 102, 1, 120.00),  # Chicken Fried Rice = 120
            (5010, 1005, 501, 1, 30.00)    # Masala Chai = 30 => total 150
        ]

        # Calculate totals per order
        totals = {}
        for oi in orderitems:
            _, oid, _, qty, price = oi
            totals.setdefault(oid, 0.0)
            totals[oid] += qty * float(price)

        # Insert orders with computed totals
        orders_to_insert = []
        for order in orders:
            oid = order[0]
            total = round(totals.get(oid, 0.0), 2)
            orders_to_insert.append((order[0], order[1], order[2], total, order[4]))

        cursor.executemany('INSERT OR IGNORE INTO orders (order_id, customer_id, order_date, total, status) VALUES (?, ?, ?, ?, ?)', orders_to_insert)
        conn.commit()

        cursor.executemany('INSERT OR IGNORE INTO orderitems (order_item_id, order_id, product_id, quantity, price) VALUES (?, ?, ?, ?, ?)', orderitems)
        conn.commit()

        # Reduce product stock according to the seeded order quantities (only for non-cancelled orders)
        # We will reduce for orders with status != 'Cancelled'
        for oi in orderitems:
            order_item_id, oid, pid, qty, price = oi
            cursor.execute('SELECT status FROM orders WHERE order_id=?', (oid,))
            status = cursor.fetchone()[0]
            if status != 'Cancelled':
                cursor.execute('UPDATE products SET stock = stock - ? WHERE product_id=?', (qty, pid))
        conn.commit()

    cursor.execute('SELECT COUNT(1) FROM payments')
    if cursor.fetchone()[0] == 0:
        now = datetime.datetime.utcnow().isoformat()
        # Payments (5 entries) - link to orders above
        payments = [
            (9001, 1001, 220.00, now, 'UPI', 'Success'),   # order 1001 paid
            (9002, 1002, 240.00, now, 'Cash', 'Pending'),  # pending payment
            (9003, 1003, 290.00, now, 'Card', 'Success'),  # paid
            (9004, 1004, 270.00, now, 'Cash', 'Failed'),   # failed (order cancelled anyway)
            (9005, 1005, 150.00, now, 'UPI', 'Pending')    # pending
        ]
        cursor.executemany('INSERT OR IGNORE INTO payments (payment_id, order_id, amount, payment_date, payment_method, status) VALUES (?, ?, ?, ?, ?, ?)', payments)
        conn.commit()

    conn.close()
    print("Database created/seeded (if empty).")

# ------ API endpoints (same as previous full app) ------
@app.route('/')
def serve_index():
    # Serve index.html if you have static frontend; otherwise simple message
    try:
        return app.send_static_file('index.html')
    except Exception:
        return "Sea Canteen API is running."

# --- Categories ---
@app.route('/api/categories', methods=['GET'])
def list_categories():
    db = get_db()
    cur = db.execute('SELECT * FROM categories')
    rows = [row_to_dict(r) for r in cur.fetchall()]
    return jsonify(rows)

@app.route('/api/categories', methods=['POST'])
def create_category():
    data = request.json
    db = get_db()
    db.execute('INSERT INTO categories (category_id, category_name, description) VALUES (?, ?, ?)',
               (data.get('category_id'), data['category_name'], data.get('description')))
    db.commit()
    return jsonify({'ok': True}), 201

@app.route('/api/categories/<int:cid>', methods=['PUT'])
def update_category(cid):
    data = request.json
    db = get_db()
    db.execute('UPDATE categories SET category_name=?, description=? WHERE category_id=?',
               (data['category_name'], data.get('description'), cid))
    db.commit()
    return jsonify({'ok': True})

@app.route('/api/categories/<int:cid>', methods=['DELETE'])
def delete_category(cid):
    db = get_db()
    db.execute('DELETE FROM categories WHERE category_id=?', (cid,))
    db.commit()
    return jsonify({'ok': True})

# --- Products ---
@app.route('/api/products', methods=['GET'])
def list_products():
    db = get_db()
    cur = db.execute('SELECT p.*, c.category_name FROM products p LEFT JOIN categories c ON p.category_id=c.category_id')
    rows = [row_to_dict(r) for r in cur.fetchall()]
    return jsonify(rows)

@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.json
    db = get_db()
    db.execute('INSERT INTO products (product_id, product_name, description, price, stock, category_id) VALUES (?, ?, ?, ?, ?, ?)',
               (data.get('product_id'), data['product_name'], data.get('description'),
                data.get('price', 0.0), data.get('stock', 0), data.get('category_id')))
    db.commit()
    return jsonify({'ok': True}), 201

@app.route('/api/products/<int:pid>', methods=['PUT'])
def update_product(pid):
    data = request.json
    db = get_db()
    db.execute('UPDATE products SET product_name=?, description=?, price=?, stock=?, category_id=? WHERE product_id=?',
               (data['product_name'], data.get('description'), data.get('price', 0.0), data.get('stock', 0), data.get('category_id'), pid))
    db.commit()
    return jsonify({'ok': True})

@app.route('/api/products/<int:pid>', methods=['DELETE'])
def delete_product(pid):
    db = get_db()
    db.execute('DELETE FROM products WHERE product_id=?', (pid,))
    db.commit()
    return jsonify({'ok': True})

# --- Customers ---
@app.route('/api/customers', methods=['GET'])
def list_customers():
    db = get_db()
    cur = db.execute('SELECT * FROM customers')
    rows = [row_to_dict(r) for r in cur.fetchall()]
    return jsonify(rows)

@app.route('/api/customers', methods=['POST'])
def create_customer():
    data = request.json
    db = get_db()
    created_at = data.get('created_at') or datetime.datetime.utcnow().isoformat()
    db.execute('INSERT INTO customers (customer_id, first_name, last_name, email, phone, address, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
               (data.get('customer_id'), data['first_name'], data.get('last_name'), data.get('email'), data.get('phone'), data.get('address'), created_at))
    db.commit()
    return jsonify({'ok': True}), 201

# --- Orders (simplified) ---
@app.route('/api/orders', methods=['GET'])
def list_orders():
    db = get_db()
    cur = db.execute('''
        SELECT o.*, c.first_name || ' ' || c.last_name AS customer_name
        FROM orders o LEFT JOIN customers c ON o.customer_id = c.customer_id
        ORDER BY order_date DESC
    ''')
    orders = []
    for r in cur.fetchall():
        order = row_to_dict(r)
        # fetch items
        items_cur = db.execute('SELECT oi.*, p.product_name FROM orderitems oi LEFT JOIN products p ON oi.product_id=p.product_id WHERE order_id=?', (order['order_id'],))
        order['items'] = [row_to_dict(i) for i in items_cur.fetchall()]
        orders.append(order)
    return jsonify(orders)

@app.route('/api/orders', methods=['POST'])
def create_order():
    '''
    Expect JSON:
    {
      "order_id": 123,
      "customer_id": 1,
      "status": "Pending",
      "items": [
         {"product_id": 1, "quantity": 2, "price": 50.00},
         ...
      ]
    }
    '''
    data = request.json
    db = get_db()
    order_id = data.get('order_id')
    customer_id = data.get('customer_id')
    order_date = datetime.datetime.utcnow().isoformat()
    items = data.get('items', [])
    total = sum(float(it.get('price', 0.0)) * int(it.get('quantity', 1)) for it in items)

    db.execute('INSERT INTO orders (order_id, customer_id, order_date, total, status) VALUES (?, ?, ?, ?, ?)',
               (order_id, customer_id, order_date, total, data.get('status', 'Pending')))
    for idx, it in enumerate(items):
        # naive order_item_id creation if not provided
        order_item_id = it.get('order_item_id') or int(f"{order_id}{idx}")
        db.execute('INSERT INTO orderitems (order_item_id, order_id, product_id, quantity, price) VALUES (?, ?, ?, ?, ?)',
                   (order_item_id, order_id, it['product_id'], it.get('quantity', 1), it.get('price', 0.0)))
        # update stock (reduce)
        db.execute('UPDATE products SET stock = stock - ? WHERE product_id=?', (it.get('quantity', 1), it['product_id']))
    db.commit()
    return jsonify({'ok': True, 'total': total}), 201

# --- Payments ---
@app.route('/api/payments', methods=['GET'])
def list_payments():
    db = get_db()
    cur = db.execute('SELECT p.*, o.customer_id FROM payments p LEFT JOIN orders o ON p.order_id=o.order_id ORDER BY payment_date DESC')
    rows = [row_to_dict(r) for r in cur.fetchall()]
    return jsonify(rows)

@app.route('/api/payments', methods=['POST'])
def create_payment():
    data = request.json
    db = get_db()
    payment_date = data.get('payment_date') or datetime.datetime.utcnow().isoformat()
    db.execute('INSERT INTO payments (payment_id, order_id, amount, payment_date, payment_method, status) VALUES (?, ?, ?, ?, ?, ?)',
               (data.get('payment_id'), data['order_id'], data['amount'], payment_date, data.get('payment_method'), data.get('status', 'Success')))
    # update order status to Completed if payment success
    if data.get('status') == 'Success':
        db.execute('UPDATE orders SET status=? WHERE order_id=?', ('Completed', data['order_id']))
    db.commit()
    return jsonify({'ok': True}), 201

# ----------------------------
# Run: ensure DB exists + seed, then start
# ----------------------------
if __name__ == '__main__':
    # create and seed DB if needed
    create_and_seed_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
