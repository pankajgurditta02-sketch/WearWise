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

    # Create Chatbot QA table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chatbot_qa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT UNIQUE NOT NULL,
            answer TEXT NOT NULL
        )
    ''')

    # Seed predefined Q&A
    predefined_qa = [
        ("What is WearWise AI?", "WearWise AI is a premium styling platform that analyzes your skin tone, gender, and preferences to provide personalized outfit suggestions and virtual try-ons."),
        ("How does virtual try-on work?", "Simply upload a full-body photo or use our simulated scanner. The system overlays the selected garment onto your silhouette so you can preview the look instantly!"),
        ("How do I place an order?", "Browse our collection, select your size, and click 'Reserve Outfit' or 'Add to Cart' to complete the checkout form. The administrator will approve your request."),
        ("What are the default admin credentials?", "You can log in to the admin panel using username: 'Pankaj_Gurditta' and password: 'Pankaj$02'."),
        ("Can I add a review to a product?", "Yes, you can write reviews and rate products from the Collection page to share your experience with other users."),
        ("What payment methods are supported?", "Currently, WearWise supports Reservation Booking. Once secured, you will receive payment details and cash on delivery/dispatch coordination via email or phone."),
        ("How can I access the Admin Dashboard?", "Click on the 'Admin Panel' link in the top navigation bar and log in with your admin credentials."),
        ("What sizes are available?", "Our collections are available in sizes S, M, L, XL, and XXL. You can view size availability for each product on its details modal."),
        ("Do you have clothes for men?", "No, WearWise is a boutique styling platform exclusively dedicated to premium designer collections and recommendations for women."),
        ("How does color matching work?", "Our AI scanner matches your skin tone profile to a complementary color palette (e.g., warm gold/bronze for dark tones, navy/emerald for fair tones)."),
        ("What is the return policy?", "We offer a 7-day easy exchange and return policy for all unworn garments with original styling tags intact."),
        ("Who developed WearWise?", "WearWise was developed by Pankaj, Dishika, Abhinav, and Bhupesh."),
        ("How do I contact support?", "You can reach out to our team at support@wearwise.ai or through the contact channels listed in the footer."),
        ("Are the products authentic?", "Yes, all products in the WearWise catalog are 100% authentic, luxury-tailored designer apparel."),
        ("Can I schedule a live styling consultation?", "Yes! You can coordinate virtual stylist video sessions by filling out the checkout reservation form, or contact support directly to book a session."),
        ("How do I reset my account password?", "If you need to reset your password, please contact the site administrator or register a new account on our portal."),
        ("Is custom tailoring available?", "Yes! We offer custom alterations and tailored fitting services for reserved outfits to match your specific measurements perfectly."),
        ("How long does delivery take?", "Standard dispatch takes 2-3 business days. Delivery dates are confirmed once the admin approves your reserved order."),
        ("Can I cancel a reservation?", "Yes, orders can be cancelled or modified from your customer portal prior to final dispatch approval by the admin."),
        ("Is there a loyalty program?", "Yes, recurring customers receive points for every completed outfit reservation, which can be redeemed for exclusive designer discounts."),
        ("What fabrics do you use?", "We utilize only premium luxury fabrics, including georgette, silk, velvet, premium cotton, and custom-embroidered blends."),
        ("Can I track my order status?", "You can view your order status directly from the Admin control panel or request live email status updates from support."),
        ("Do you ship internationally?", "Currently, we only ship nationwide. We are working on international logistics to support global shipping soon!"),
        ("What is the AI Capsule Wardrobe Quiz?", "You can access our interactive AI Capsule Wardrobe Quiz from the top navigation bar. Answer 3 styling questions and the AI will curate a cohesive 3-piece coordinates capsule wardrobe collection for your specific occasion!"),
        ("How do I plan a capsule wardrobe?", "Navigate to the 'Style Quiz' page, choose your occasion, select a color palette, and pick your preferred silhouette fit. The system will automatically construct a customized capsule wardrobe for you!"),
        ("What is the Fabric Visualizer?", "The Fabric Visualizer is an interactive page on our website where you can select luxury fabric swatches (like Emerald Satin Silk, Ruby Raw Silk, Midnight Velvet, Champagne Brocade, or Georgette) to dynamically preview fabric coordinates and drapes on our style mannequin model!"),
        ("How does the fabric visualizer work?", "Navigate to the 'Fabric Visualizer' page in the top menu and click on any colored swatch. The visualizer overlay will update the dress color on the model mannequin and display detailed information about the fabric weave, composition, wash care instructions, and link matching garments from the WearWise collection!"),
        ("How can I track my order?", "Visit the 'Track My Order' page from the footer or navigate to /track. Enter the email address or phone number you used during reservation and your complete order status will be shown instantly with a live step-by-step progress tracker!"),
        ("Where is my order?", "To check your order status, visit the Track My Order page and enter your registered email or phone number. You will see a live progress timeline showing whether your order is Pending, Processing, Approved, or Completed and dispatched."),
        ("track my order", "You can track your reservation from our Track My Order page! Just enter your email or phone number to see the live status of all your orders.")
    ]
    cursor.executemany("INSERT OR IGNORE INTO chatbot_qa (question, answer) VALUES (?, ?)", predefined_qa)
    print("Chatbot QA table seeded.")

    conn.commit()
    conn.close()
    print("Database initialization complete.")

if __name__ == '__main__':
    init_db()
