# app.py
import os
import sqlite3
import datetime
from flask import Flask, request, jsonify, g
from flask_cors import CORS

os.remove("canteen.db")
DATABASE = 'canteen.db'

app = Flask(__name__, static_folder='static', static_url_path='/')
CORS(app)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # Use per-request connection. check_same_thread=False helps when Flask runs threaded.
        db = g._database = sqlite3.connect(DATABASE, check_same_thread=False)
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

    # Use INTEGER PRIMARY KEY AUTOINCREMENT where IDs are created by DB
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name VARCHAR(50),
        description TEXT
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INT,
        order_date TIMESTAMP,
        total DECIMAL(10,2),
        status TEXT CHECK(status IN ('Pending', 'Completed', 'Cancelled')),
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orderitems (
        order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INT,
        amount DECIMAL(10,2),
        payment_date TIMESTAMP,
        payment_method TEXT CHECK(payment_method IN ('Cash', 'Card', 'UPI', 'Cash on Delivery')),
        status TEXT CHECK(status IN ('Success', 'Failed', 'Pending')),
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    );
    ''')
    conn.commit()

    # Seed only when empty
    cursor.execute('SELECT COUNT(1) FROM categories')
    if cursor.fetchone()[0] == 0:
        categories = [
            ('Chinese', 'Noodles, fried rice and Chinese-style mains.'),
            ('Indian', 'Curries, biryanis, and Indian staples.'),
            ('Continental', 'Sandwiches, pasta, and continental mains.'),
            ('Snacks', 'Quick bites and small-plates.'),
            ('Beverages', 'Hot & cold drinks, juices and shakes.')
        ]
        cursor.executemany('INSERT INTO categories (category_name, description) VALUES (?, ?)', categories)
        conn.commit()

    cursor.execute('SELECT COUNT(1) FROM products')
    if cursor.fetchone()[0] == 0:
        # If you prefer fixed product IDs, set them explicitly; here we let DB assign product_id
        products = [
            ('Veg Noodles', 'Stir-fried noodles with veggies', 80.00, 30, 1),
            ('Chicken Fried Rice', 'Wok-fried rice with chicken', 120.00, 20, 1),
            ('Paneer Butter Masala', 'Creamy paneer curry with butter', 150.00, 15, 2),
            ('Chicken Biryani', 'Aromatic basmati biryani with chicken', 180.00, 10, 2),
            ('Club Sandwich', 'Multi-layer sandwich with veggies and chicken', 140.00, 25, 3),
            ('Penne Alfredo', 'Pasta in creamy alfredo sauce', 130.00, 18, 3),
            ('French Fries', 'Crispy golden fries', 60.00, 40, 4),
            ('Veg Spring Roll', 'Crispy rolls with mixed veg', 70.00, 35, 4),
            ('Masala Chai', 'Hot spiced tea', 30.00, 100, 5),
            ('Iced Lemon Tea', 'Refreshing iced lemon tea', 45.00, 80, 5)
        ]
        cursor.executemany('INSERT INTO products (product_name, description, price, stock, category_id) VALUES (?, ?, ?, ?, ?)', products)
        conn.commit()

    cursor.execute('SELECT COUNT(1) FROM customers')
    if cursor.fetchone()[0] == 0:
        now = datetime.datetime.utcnow().isoformat()
        customers = [
            ('Aarav', 'Sharma', 'aarav.sharma@example.com', '9876543210', 'Block A, Hostel 1', now),
            ('Isha', 'Verma', 'isha.verma@example.com', '9123456780', 'Block B, Hostel 2', now),
            ('Rohan', 'Singh', 'rohan.singh@example.com', '9988776655', 'Block C, Hostel 3', now),
            ('Priya', 'Kaur', 'priya.kaur@example.com', '9012345678', 'Block D, Hostel 4', now),
            ('Vikram', 'Patel', 'vikram.patel@example.com', '8899001122', 'Block E, Hostel 5', now),
            ('Neha', 'Gupta', 'neha.gupta@example.com', '7766554433', 'Block F, Hostel 6', now)
        ]
        cursor.executemany('INSERT INTO customers (first_name, last_name, email, phone, address, created_at) VALUES (?, ?, ?, ?, ?, ?)', customers)
        conn.commit()

    # Seed simple orders/payments only if no orders exist
    cursor.execute('SELECT COUNT(1) FROM orders')
    if cursor.fetchone()[0] == 0:
        now = datetime.datetime.utcnow().isoformat()
        # We'll insert some orders and items manually to keep example data; using explicit IDs is not necessary
        # Insert orders
        orders_data = [
            (1, now, 220.00, 'Completed'),  # customer_id 1
            (2, now, 240.00, 'Pending'),
            (3, now, 290.00, 'Completed'),
            (4, now, 270.00, 'Cancelled'),
            (5, now, 150.00, 'Pending'),
        ]
        # orders_data tuples: (customer_id, order_date, total, status)
        cursor.executemany('INSERT INTO orders (customer_id, order_date, total, status) VALUES (?, ?, ?, ?)', orders_data)
        conn.commit()

        # Insert orderitems (map product names to product_id)
        # For simplicity, fetch product_ids by name
        def pid(name):
            cursor.execute('SELECT product_id FROM products WHERE product_name=?', (name,))
            r = cursor.fetchone()
            return r[0] if r else None

        orderitems = [
            (1, pid('Veg Noodles'), 2, 80.00),   # order_id 1
            (1, pid('Masala Chai'), 2, 30.00),
            (2, pid('Chicken Biryani'), 1, 180.00),
            (2, pid('French Fries'), 1, 60.00),
            (3, pid('Paneer Butter Masala'), 1, 150.00),
            (3, pid('Club Sandwich'), 1, 140.00),
            (4, pid('Penne Alfredo'), 1, 130.00),
            (4, pid('Veg Spring Roll'), 2, 70.00),
            (5, pid('Chicken Fried Rice'), 1, 120.00),
            (5, pid('Masala Chai'), 1, 30.00),
        ]
        # orderitems: (order_id, product_id, quantity, price)
        cursor.executemany('INSERT INTO orderitems (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)', orderitems)
        conn.commit()

        # Reduce stock for non-cancelled orders
        cursor.execute('SELECT order_id, status FROM orders')
        for order_id, status in cursor.fetchall():
            if status != 'Cancelled':
                cursor.execute('SELECT product_id, quantity FROM orderitems WHERE order_id=?', (order_id,))
                for prod_id, qty in cursor.fetchall():
                    cursor.execute('UPDATE products SET stock = stock - ? WHERE product_id=?', (qty, prod_id))
        conn.commit()

    cursor.execute('SELECT COUNT(1) FROM payments')
    if cursor.fetchone()[0] == 0:
        now = datetime.datetime.utcnow().isoformat()
        # Link payments to orders inserted above (we assume sequential order_ids start at 1)
        payments = [
            (1, 220.00, now, 'UPI', 'Success'),
            (2, 240.00, now, 'Cash', 'Pending'),
            (3, 290.00, now, 'Card', 'Success'),
            (4, 270.00, now, 'Cash', 'Failed'),
            (5, 150.00, now, 'UPI', 'Pending'),
        ]
        cursor.executemany('INSERT INTO payments (order_id, amount, payment_date, payment_method, status) VALUES (?, ?, ?, ?, ?)', payments)
        conn.commit()

    conn.close()
    print("Database created/seeded (if empty).")

# -------------------
# API Endpoints
# -------------------
@app.route('/')
def serve_index():
    try:
        return app.send_static_file('index.html')
    except Exception:
        return "Sea Canteen API is running."

# --- Categories ---
@app.route('/api/categories', methods=['GET'])
def list_categories():
    db = get_db()
    cur = db.execute('SELECT * FROM categories ORDER BY category_name ASC')
    categories = []
    for r in cur.fetchall():
        cat = row_to_dict(r)
        # embed products for convenience
        pcur = db.execute('SELECT product_id, product_name, description, price, stock, category_id FROM products WHERE category_id=? ORDER BY product_name ASC', (cat['category_id'],))
        cat['products'] = [row_to_dict(p) for p in pcur.fetchall()]
        categories.append(cat)
    return jsonify(categories)

@app.route('/api/categories', methods=['POST'])
def create_category():
    data = request.json or {}
    db = get_db()
    name = data.get('category_name')
    desc = data.get('description')
    if not name:
        return jsonify({'error': 'category_name required'}), 400
    cur = db.execute('INSERT INTO categories (category_name, description) VALUES (?, ?)', (name, desc))
    db.commit()
    return jsonify({'ok': True, 'category_id': cur.lastrowid}), 201

@app.route('/api/categories/<int:cid>', methods=['PUT'])
def update_category(cid):
    data = request.json or {}
    db = get_db()
    db.execute('UPDATE categories SET category_name=?, description=? WHERE category_id=?',
               (data.get('category_name'), data.get('description'), cid))
    db.commit()
    return jsonify({'ok': True})

@app.route('/api/categories/<int:cid>', methods=['DELETE'])
def delete_category(cid):
    db = get_db()
    db.execute('DELETE FROM categories WHERE category_id=?', (cid,))
    db.commit()
    return jsonify({'ok': True})

@app.route('/api/categories/<int:cid>/products', methods=['GET'])
def list_products_by_category(cid):
    db = get_db()
    pcur = db.execute('SELECT product_id, product_name, description, price, stock, category_id FROM products WHERE category_id=? ORDER BY product_name ASC', (cid,))
    rows = [row_to_dict(r) for r in pcur.fetchall()]
    return jsonify(rows)

# --- Products ---
@app.route('/api/products', methods=['GET'])
def list_products():
    db = get_db()
    cur = db.execute('SELECT p.*, c.category_name FROM products p LEFT JOIN categories c ON p.category_id=c.category_id')
    rows = [row_to_dict(r) for r in cur.fetchall()]
    return jsonify(rows)

@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.json or {}
    db = get_db()
    name = data.get('product_name')
    if not name:
        return jsonify({'error': 'product_name required'}), 400
    cur = db.execute('INSERT INTO products (product_name, description, price, stock, category_id) VALUES (?, ?, ?, ?, ?)',
                     (name, data.get('description'), data.get('price', 0.0), data.get('stock', 0), data.get('category_id')))
    db.commit()
    return jsonify({'ok': True, 'product_id': cur.lastrowid}), 201

@app.route('/api/products/<int:pid>', methods=['PUT'])
def update_product(pid):
    data = request.json or {}
    db = get_db()
    db.execute('UPDATE products SET product_name=?, description=?, price=?, stock=?, category_id=? WHERE product_id=?',
               (data.get('product_name'), data.get('description'), data.get('price', 0.0), data.get('stock', 0), data.get('category_id'), pid))
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
    cur = db.execute('SELECT * FROM customers ORDER BY created_at DESC')
    rows = [row_to_dict(r) for r in cur.fetchall()]
    return jsonify(rows)

@app.route('/api/customers', methods=['POST'])
def create_customer():
    data = request.json or {}
    db = get_db()
    created_at = data.get('created_at') or datetime.datetime.utcnow().isoformat()
    cur = db.execute('INSERT INTO customers (first_name, last_name, email, phone, address, created_at) VALUES (?, ?, ?, ?, ?, ?)',
               (data.get('first_name'), data.get('last_name'), data.get('email'), data.get('phone'), data.get('address'), created_at))
    db.commit()
    return jsonify({'ok': True, 'customer_id': cur.lastrowid}), 201

# --- Orders ---
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
        items_cur = db.execute('SELECT oi.*, p.product_name FROM orderitems oi LEFT JOIN products p ON oi.product_id=p.product_id WHERE order_id=?', (order['order_id'],))
        order['items'] = [row_to_dict(i) for i in items_cur.fetchall()]
        orders.append(order)
    return jsonify(orders)

@app.route('/api/orders', methods=['POST'])
def create_order():
    """
    Expect JSON:
    {
      "customer_id": 1,           # optional
      "status": "Pending",        # optional
      "items": [ { product_id, quantity, price }, ... ]
    }
    Returns: { ok: True, order_id: <id>, total: <total> }
    """
    data = request.json or {}
    items = data.get('items', [])
    if not items:
        return jsonify({'error': 'items required'}), 400

    db = get_db()
    order_date = datetime.datetime.utcnow().isoformat()
    status = data.get('status', 'Pending')

    # compute total
    total = 0.0
    for it in items:
        qty = int(it.get('quantity', 1))
        price = float(it.get('price', 0.0))
        total += qty * price

    # Insert order (let DB assign order_id)
    cur = db.execute('INSERT INTO orders (customer_id, order_date, total, status) VALUES (?, ?, ?, ?)',
                     (data.get('customer_id'), order_date, round(total, 2), status))
    order_id = cur.lastrowid

    # Insert items and update product stock atomically (simple approach)
    for it in items:
        pid = it['product_id']
        qty = int(it.get('quantity', 1))
        price = float(it.get('price', 0.0))
        db.execute('INSERT INTO orderitems (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
                   (order_id, pid, qty, price))
        # reduce stock, but keep it >= 0 (do not allow negative stock)
        db.execute('UPDATE products SET stock = MAX(stock - ?, 0) WHERE product_id=?', (qty, pid))

    db.commit()
    return jsonify({'ok': True, 'order_id': order_id, 'total': round(total, 2)}), 201

# --- Payments ---
@app.route('/api/payments', methods=['GET'])
def list_payments():
    db = get_db()
    cur = db.execute('SELECT p.*, o.customer_id FROM payments p LEFT JOIN orders o ON p.order_id=o.order_id ORDER BY payment_date DESC')
    rows = [row_to_dict(r) for r in cur.fetchall()]
    return jsonify(rows)

@app.route('/api/payments', methods=['POST'])
def create_payment():
    data = request.json or {}
    db = get_db()
    payment_date = data.get('payment_date') or datetime.datetime.utcnow().isoformat()
    order_id = data.get('order_id')
    if order_id is None:
        return jsonify({'error': 'order_id required'}), 400

    # Fetch order total and use that as payment amount
    cur_order = db.execute('SELECT total FROM orders WHERE order_id=?', (order_id,))
    order_row = cur_order.fetchone()
    if not order_row:
        return jsonify({'error': 'Invalid order_id'}), 400

    amount = float(order_row['total'])

    if order_id is None:
        return jsonify({'error': 'order_id required'}), 400
    cur = db.execute('INSERT INTO payments (order_id, amount, payment_date, payment_method, status) VALUES (?, ?, ?, ?, ?)',
               (order_id, amount, payment_date, data.get('payment_method'), data.get('status', 'Success')))
    payment_id = cur.lastrowid
    # update order status to Completed if payment success
    if data.get('status') == 'Success':
        db.execute('UPDATE orders SET status=? WHERE order_id=?', ('Completed', order_id))
    db.commit()
    return jsonify({'ok': True, 'payment_id': payment_id}), 201

# ----------------------------
# Run: ensure DB exists + seed, then start
# ----------------------------
if __name__ == '__main__':
    create_and_seed_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
