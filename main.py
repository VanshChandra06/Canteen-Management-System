import sqlite3

conn=sqlite3.connect("canteen.db")
cursor = conn.cursor()

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
conn.close()
print("Connection closed.")