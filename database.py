import sqlite3
import os

def init_db():
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create Users table for Admin Panel
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Create Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL,
            description TEXT,
            gender TEXT,
            category TEXT,
            body_type_suitability TEXT,
            suggested_fit TEXT
        )
    ''')

    # Create Uploads table for Analytics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            predicted_size TEXT,
            body_type TEXT,
            gender TEXT
        )
    ''')

    # Create Reservations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            bust TEXT,
            waist TEXT,
            hips TEXT,
            height TEXT,
            suit_name TEXT NOT NULL,
            price INTEGER NOT NULL
        )
    ''')

    # Insert default admin user if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password) VALUES ('admin', 'admin')")
        print("Default admin user created (admin/admin)")

    # Insert sample products if table is empty
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    if count == 0:
        sample_products = [
            # Men
            ('Classic White Shirt', 'M-SHIRT-001', 'Premium cotton formal shirt', 'Men', 'Shirts', 'Regular, Slim', 'Slim Fit'),
            ('Navy Blue Blazer', 'M-JAC-001', 'Sharp navy blazer for party and office', 'Men', 'Jackets', 'Athletic, Regular', 'Tailored Fit'),
            ('Black Casual T-Shirt', 'M-TEE-001', 'Comfortable cotton casual tee', 'Men', 'T-Shirts', 'Slim, Regular, Athletic, Plus Size', 'Regular Fit'),
            ('Festive Maroon Kurta', 'M-KUR-001', 'Traditional silk kurta', 'Men', 'Kurta', 'Regular, Plus Size', 'Relaxed Fit'),
            # Women
            ('Elegant Red Saree', 'W-SAR-001', 'Georgette party wear saree', 'Women', 'Sarees', 'Slim, Regular, Plus Size', 'Free Size'),
            ('Floral Summer Dress', 'W-DRE-001', 'Breezy knee-length dress', 'Women', 'Dresses', 'Slim, Athletic', 'A-Line Fit'),
            ('Professional Grey Suit', 'W-SUI-001', '2-piece formal suit', 'Women', 'Suits', 'Regular, Athletic', 'Tailored Fit'),
            ('Embroidered Kurti', 'W-KUR-001', 'Cotton daily wear kurti', 'Women', 'Kurtis', 'Regular, Plus Size', 'Straight Fit')
        ]
        cursor.executemany('''
            INSERT INTO products (name, code, description, gender, category, body_type_suitability, suggested_fit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', sample_products)
        print("Sample products inserted.")

    conn.commit()
    conn.close()
    print("Database initialization complete.")

if __name__ == '__main__':
    init_db()
