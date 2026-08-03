import sqlite3
conn = sqlite3.connect("D:\Dehemi\Python\ecommerce_django\db.sqlite3")
c = conn.cursor()

# Check sqlite_sequence for original auto-increment values
c.execute("SELECT name, seq FROM sqlite_sequence WHERE name IN ('orders_order', 'orders_orderproduct', 'orders_payment')")
rows = c.fetchall()
print("sqlite_sequence:")
for row in rows:
    print(f"  {row[0]}: seq={row[1]}")

# Check actual row counts
c.execute("SELECT COUNT(*) FROM orders_order")
print(f"orders_order count: {c.fetchone()[0]}")
c.execute("SELECT COUNT(*) FROM orders_orderproduct")
print(f"orders_orderproduct count: {c.fetchone()[0]}")
c.execute("SELECT COUNT(*) FROM orders_payment")
print(f"orders_payment count: {c.fetchone()[0]}")

conn.close()
