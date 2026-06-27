import sqlite3
import os

def init_db():
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    
    # Remove existing database if present to ensure fresh schema
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("Resetting database for new schema...")
        except Exception as e:
            print(f"Could not remove database: {e}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create Users table for Admin and Customers Panel
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'customer'
        )
    ''')

    # Create Products table (updated schema)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL,
            description TEXT,
            gender TEXT,
            category TEXT,
            price INTEGER DEFAULT 2999,
            image TEXT,
            stock_quantity INTEGER DEFAULT 10,
            available_sizes TEXT DEFAULT 'S, M, L, XL, XXL'
        )
    ''')

    # Create Uploads table for Analytics (simplified, no body sizes/types)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            gender TEXT,
            skin_tone TEXT
        )
    ''')

    # Create Reservations (Orders) table (updated schema, no body sizes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            suit_name TEXT NOT NULL,
            price INTEGER NOT NULL,
            selected_size TEXT DEFAULT 'M',
            status TEXT DEFAULT 'Pending'
        )
    ''')

    # Create Reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')

    # Insert default admin and customer users
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('Pankaj_Gurditta', 'Pankaj$02', 'admin')")
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', 'admin', 'admin')")
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('customer', 'customer', 'customer')")
    print("Admin and customer users seeded successfully.")

    # Insert sample products
    sample_products = [
        # Men / Unisex/ Women Suits
        ('Classic Suit Collection #1', 'SUI-001', 'Sharp 2-piece modern suit perfect for business corporate settings.', 'Women', 'Office', 1949, 'suit1.jpg', 12, 'S, M, L, XL'),
        ('Premium Royal Suit #2', 'SUI-002', 'High-end designer formal suit with premium textured finish.', 'Women', 'Office', 1999, 'suit2.jpg', 8, 'M, L, XL, XXL'),
        ('Midnight Tuxedo Suit #3', 'SUI-003', 'Exquisite black satin velvet tuxedo suit for evening events.', 'Women', 'Party', 2049, 'suit3.jpg', 5, 'S, M, L, XL'),
        ('Warm Burgundy Kurta #4', 'SUI-004', 'Beautiful crimson ethnic traditional drape for festive wear.', 'Women', 'Wedding', 2099, 'suit5.jpg', 15, 'S, M, L, XL, XXL'),
        ('Golden Velvet Suit #5', 'SUI-005', 'Luxury embroidery festive suit set for social occasions.', 'Women', 'Festive', 2149, 'suit6.jpg', 10, 'S, M, L'),
        ('Emerald Green Blazer #6', 'SUI-006', 'Tailored casual blazer suitable for colleges and brunch dates.', 'Women', 'College', 2199, 'suit9.jpg', 2, 'S, M, L, XL'),
        ('Champagne Saree Dress #7', 'SUI-007', 'Elegant draped ethnic evening gown styled saree set.', 'Women', 'Casual', 2249, 'suit10.jpg', 14, 'S, M, L, XL, XXL'),
        ('Double Breasted Grey Suit #8', 'SUI-008', 'Classic check pattern grey formal executive suit set.', 'Women', 'Office', 2299, 'suit11.jpg', 7, 'M, L, XL'),
    ]
    cursor.executemany('''
        INSERT OR IGNORE INTO products (name, code, description, gender, category, price, image, stock_quantity, available_sizes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_products)
    print("Sample products inserted.")

    # Insert some sample reviews
    sample_reviews = [
        (1, 'Aarav Mehta', 5, 'Absolutely beautiful fit and high quality fabric!'),
        (1, 'Neha Sharma', 4, 'Very elegant corporate suit, matches description perfectly.'),
        (2, 'Kabir Malhotra', 5, 'Highly recommend this suit set. Rich texture.'),
        (3, 'Tanya Sen', 5, 'Tuxedo fit is stunning. Fabric is soft and comfortable.'),
        (4, 'Priya Das', 4, 'Traditional look matches well with festive season.'),
    ]
    cursor.executemany('''
        INSERT INTO reviews (product_id, user_name, rating, comment)
        VALUES (?, ?, ?, ?)
    ''', sample_reviews)
    print("Sample reviews inserted.")

    # Insert some sample orders (reservations) for analytics
    sample_orders = [
        ('Karan Malhotra', 'karan@gmail.com', '9876543210', 'Classic Suit Collection #1', 1949, 'M', 'Pending'),
        ('Sarah Khan', 'sarah@gmail.com', '9812345670', 'Premium Royal Suit #2', 1999, 'S', 'Completed'),
        ('Amit Verma', 'amit@gmail.com', '9988776655', 'Midnight Tuxedo Suit #3', 2049, 'L', 'Processing'),
        ('Rita Roy', 'rita@gmail.com', '9123456789', 'Midnight Tuxedo Suit #3', 2049, 'XL', 'Completed'),
        ('Jatin Paul', 'jatin@gmail.com', '8877665544', 'Classic Suit Collection #1', 1949, 'M', 'Completed'),
    ]
    cursor.executemany('''
        INSERT INTO reservations (name, email, phone, suit_name, price, selected_size, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', sample_orders)
    print("Sample orders inserted.")

    conn.commit()
    conn.close()
    print("Database initialization complete.")

if __name__ == '__main__':
    init_db()
