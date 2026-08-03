import sqlite3
conn = sqlite3.connect('D:\\Dehemi\\Python\\ecommerce_django\\db.sqlite3')
c = conn.cursor()

# Check current state
c.execute('SELECT name FROM sqlite_master WHERE type=''table'' AND name LIKE ''%payment%''')
tables = c.fetchall()
print('Payment-related tables:', [t[0] for t in tables])

# Check for orders_payment_old
c.execute('SELECT name FROM sqlite_master WHERE type=''table'' AND name=''orders_payment_old''')
old = c.fetchone()
print('orders_payment_old exists:', old is not None)

# Check FK references
c.execute('SELECT sql FROM sqlite_master WHERE sql LIKE ?', ('%orders_payment_old%',))
refs = c.fetchall()
print('FK references to orders_payment_old:', len(refs))

# Check all tables
c.execute('SELECT name FROM sqlite_master WHERE type=''table'' ORDER BY name')
all_tables = c.fetchall()
print('All tables:', [t[0] for t in all_tables])

conn.close()
