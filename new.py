#!/usr/bin/env python3
# canteen_final.py
# Ultra simple flat beginner script with DB/tables/data/menu + ASCII table output.
#to start xampp:
#cd /opt/lampp
#sudo ./lampp start

import mysql.connector
from mysql.connector import Error

# ---- MYSQL CONFIG ----
host = "localhost"
user = "root"
password = ""
db = "canteen"
# -----------------------

# BASIC ASCII TABLE PRINTER
def print_table(rows, cur):
    if not rows:
        print("(no rows)")
        return

    cols = cur.column_names
    str_rows = [[str(x) for x in r] for r in rows]
    widths = [max(len(str(col)), max(len(r[i]) for r in str_rows)) for i, col in enumerate(cols)]

    line = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    print(line)

    header = "|" + "|".join(" " + str(col).ljust(widths[i]) + " " for i, col in enumerate(cols)) + "|"
    print(header)
    print(line)

    for r in str_rows:
        row_line = "|" + "|".join(" " + r[i].ljust(widths[i]) + " " for i in range(len(cols))) + "|"
        print(row_line)

    print(line)


# -----------------------------------------
# CONNECT TO MYSQL SERVER
# -----------------------------------------
try:
    conn = mysql.connector.connect(host=host, user=user, password=password)
    cur = conn.cursor()
except Exception as e:
    print("Could not connect:", e)
    raise SystemExit

# CREATE DATABASE + USE IT
cur.execute(f"CREATE DATABASE IF NOT EXISTS {db};")
cur.execute(f"USE {db};")

# -----------------------------------------
# CREATE TABLES
# -----------------------------------------
cur.execute("""
CREATE TABLE IF NOT EXISTS categories (
    category_id INT PRIMARY KEY,
    category_name VARCHAR(50),
    description TEXT
);""")

cur.execute("""
CREATE TABLE IF NOT EXISTS products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(100),
    description TEXT,
    price DECIMAL(10,2),
    stock INT,
    category_id INT,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);""")

cur.execute("""
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    phone VARCHAR(15),
    address TEXT,
    created_at TIMESTAMP
);""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    order_date TIMESTAMP,
    total DECIMAL(10,2),
    status TEXT CHECK(status IN ('Pending','Completed','Cancelled')),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orderitems (
    order_item_id INT PRIMARY KEY,
    order_id INT,
    product_id INT,
    quantity INT,
    price DECIMAL(10,2),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);""")

cur.execute("""
CREATE TABLE IF NOT EXISTS payments (
    payment_id INT PRIMARY KEY,
    order_id INT,
    amount DECIMAL(10,2),
    payment_date TIMESTAMP,
    payment_method TEXT CHECK(payment_method IN ('Cash','Card','UPI','Cash on Delivery')),
    status TEXT CHECK(status IN ('Success','Failed','Pending')),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);""")

conn.commit()
print("Tables created or already exist.")

# -----------------------------------------
# INSERT DUMMY DATA
# -----------------------------------------

try:
    # Categories
    cur.execute("INSERT IGNORE INTO categories VALUES (1,'Chinese','Chinese dishes');")
    cur.execute("INSERT IGNORE INTO categories VALUES (2,'Indian','Indian dishes');")
    cur.execute("INSERT IGNORE INTO categories VALUES (3,'Beverages','Drinks');")
    cur.execute("INSERT IGNORE INTO categories VALUES (4,'Snacks','Light snacks');")

    # Products
    cur.execute("INSERT IGNORE INTO products VALUES (1,'Chow Mein','Veg noodles',80,30,1);")
    cur.execute("INSERT IGNORE INTO products VALUES (2,'Gobi Manchurian','Crispy gobi',90,20,1);")
    cur.execute("INSERT IGNORE INTO products VALUES (3,'Paneer Butter Masala','Paneer curry',150,60,2);")
    cur.execute("INSERT IGNORE INTO products VALUES (4,'Masala Dosa','Dosa',70,45,2);")
    cur.execute("INSERT IGNORE INTO products VALUES (5,'Coke','Drink',30,100,3);")
    cur.execute("INSERT IGNORE INTO products VALUES (6,'Chips','Snack',25,10,4);")
    cur.execute("INSERT IGNORE INTO products VALUES (7,'Chicken Fried Rice','Rice',120,40,1);")
    cur.execute("INSERT IGNORE INTO products VALUES (8,'Spring Roll','Roll',60,35,4);")

    # Customers
    cur.execute("INSERT IGNORE INTO customers VALUES (1,'John','Doe','john@example.com','1111','A St',NOW());")
    cur.execute("INSERT IGNORE INTO customers VALUES (2,'Jane','Smith','jane@example.com','2222','B St',NOW());")
    cur.execute("INSERT IGNORE INTO customers VALUES (3,'Bob','Brown','bob@example.com','3333','C St',NOW());")

    # Orders
    cur.execute("INSERT IGNORE INTO orders VALUES (1,1,NOW(),250,'Pending');")
    cur.execute("INSERT IGNORE INTO orders VALUES (2,1,NOW(),150,'Completed');")
    cur.execute("INSERT IGNORE INTO orders VALUES (3,2,NOW(),120,'Pending');")
    cur.execute("INSERT IGNORE INTO orders VALUES (4,3,NOW(),80,'Completed');")

    # Orderitems
    cur.execute("INSERT IGNORE INTO orderitems VALUES (1,1,1,1,80);")
    cur.execute("INSERT IGNORE INTO orderitems VALUES (2,1,2,2,90);")
    cur.execute("INSERT IGNORE INTO orderitems VALUES (3,2,7,1,120);")
    cur.execute("INSERT IGNORE INTO orderitems VALUES (4,2,5,1,30);")
    cur.execute("INSERT IGNORE INTO orderitems VALUES (5,3,3,1,120);")
    cur.execute("INSERT IGNORE INTO orderitems VALUES (6,4,6,2,25);")

    # Payments (FIXED LINE → "Cash on Delivery")
    cur.execute("INSERT IGNORE INTO payments VALUES (1,1,250,NOW(),'UPI','Pending');")
    cur.execute("INSERT IGNORE INTO payments VALUES (2,2,150,NOW(),'Card','Success');")
    cur.execute("INSERT IGNORE INTO payments VALUES (3,3,120,NOW(),'Cash','Pending');")
    cur.execute("INSERT IGNORE INTO payments VALUES (4,4,80,NOW(),'Cash on Delivery','Failed');")  
    cur.execute("INSERT IGNORE INTO payments VALUES (5,2,50,NOW(),'UPI','Pending');")

    conn.commit()
    print("Dummy data inserted.")
except Exception as e:
    print("Dummy data error:", e)
    raise SystemExit


# -----------------------------------------
# MENU LOOP WITH TABLE OUTPUT
# -----------------------------------------

while True:
    print("\nChoose (1-6), or q to quit:")
    print("1 - Chinese products")
    print("2 - Orders by john@example.com")
    print("3 - Total spent by each customer")
    print("4 - Items in order 1")
    print("5 - Pending payments")
    print("6 - Products stock < 50")

    choice = input("Your choice: ").strip()

    if choice.lower() in ("q", "quit", "exit"):
        break

    try:
        if choice == "1":
            cur.execute("""
            SELECT p.product_id, p.product_name, p.description, p.price, p.stock
            FROM products p JOIN categories c ON p.category_id = c.category_id
            WHERE LOWER(c.category_name)='chinese';
            """)
            print_table(cur.fetchall(), cur)

        elif choice == "2":
            cur.execute("""
            SELECT o.order_id, o.order_date, o.total, o.status
            FROM orders o JOIN customers cu ON o.customer_id=cu.customer_id
            WHERE cu.email="john@example.com";
            """)
            print_table(cur.fetchall(), cur)

        elif choice == "3":
            cur.execute("""
            SELECT cu.first_name, cu.last_name,
                   COALESCE(SUM(o.total),0) AS total_spent
            FROM customers cu
            LEFT JOIN orders o ON cu.customer_id=o.customer_id
            GROUP BY cu.customer_id;
            """)
            print_table(cur.fetchall(), cur)

        elif choice == "4":
            cur.execute("""
            SELECT p.product_name, oi.quantity, oi.price
            FROM orderitems oi JOIN products p
            ON oi.product_id=p.product_id
            WHERE oi.order_id=1;
            """)
            print_table(cur.fetchall(), cur)

        elif choice == "5":
            cur.execute("""
            SELECT payment_id, order_id, amount, payment_date, payment_method
            FROM payments
            WHERE status='Pending';
            """)
            print_table(cur.fetchall(), cur)

        elif choice == "6":
            cur.execute("""
            SELECT p.product_name, p.stock, c.category_name
            FROM products p LEFT JOIN categories c
            ON p.category_id=c.category_id
            WHERE p.stock < 50;
            """)
            print_table(cur.fetchall(), cur)

        else:
            print("Invalid option.")

    except Exception as e:
        print("Query error:", e)

cur.close()
conn.close()
print("Finished!")