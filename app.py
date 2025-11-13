# app.py
from flask import Flask, request, jsonify, g
from flask_cors import CORS
import sqlite3
import datetime

DATABASE = 'canteen.db'

app = Flask(__name__, static_folder='static')
CORS(app)

@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def serve_static(path):
    # this will serve static files from static/ or return index.html for unknown routes (SPA-friendly)
    try:
        return app.send_static_file(path)
    except Exception:
        return app.send_static_file('index.html')

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

if __name__ == '__main__':
    app.run(debug=True)
