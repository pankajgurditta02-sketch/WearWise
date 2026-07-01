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
        # Existing Party Suit
        ('Evening Velvet Tuxedo', 'SUI-003', 'Exquisite designer velvet tuxedo set for evening events.', 'Women', 'Party', 2049, 'suit3.jpg', 5, 'S, M, L, XL'),
        
        # Formals for Women
        ('Executive Tailored Pantsuit', 'FOR-001', 'Premium wool-blend structured double-breasted pantsuit for contemporary formal wear.', 'Women', 'Formals', 2499, 'formals_women_1.avif', 10, 'S, M, L, XL'),
        ('Corporate Blazer Set', 'FOR-002', 'Elegant corporate blazer coupled with matching slim trousers for boardroom meetings.', 'Women', 'Formals', 2599, 'formals_women_2.avif', 8, 'M, L, XL, XXL'),
        ('Signature Slim-Fit Suit', 'FOR-003', 'Sharp single-breasted blazer and trousers styled for a clean professional look.', 'Women', 'Formals', 2699, 'formals_women_3.avif', 12, 'S, M, L, XL'),
        ('Executive Power Suit', 'FOR-004', 'Classic formal pantsuit featuring a tailored waist and notched lapels.', 'Women', 'Formals', 2799, 'formals_women_4.webp', 15, 'S, M, L, XL, XXL'),
        ('Classic Formal Blazer Set', 'FOR-005', 'Chic corporate blazer set designed for professional styling.', 'Women', 'Formals', 2899, 'formals_women_5.avif', 10, 'S, M, L'),
        ('Boardroom Classic Suit', 'FOR-006', 'Sophisticated formal blazer and trouser ensemble.', 'Women', 'Formals', 2999, 'formals_women_6.webp', 7, 'S, M, L, XL'),
        ('Modern Power Suit Set', 'FOR-007', 'Empowering tailored pantsuit set with a streamlined silhouette.', 'Women', 'Formals', 3099, 'formals_women_7.jpg', 9, 'S, M, L, XL, XXL'),
        ('Luxury Business Suit', 'FOR-008', 'Exquisite textured business suit for executive presentation.', 'Women', 'Formals', 3199, 'formals_women_8.jpg', 6, 'M, L, XL'),
        ('Classic Business Blazer Set', 'FOR-009', 'Timeless structured trouser suit tailored for comfort and elegance.', 'Women', 'Formals', 3299, 'formals_women_9.webp', 11, 'S, M, L, XL'),
        ('Designer Evening Suit Set', 'FOR-010', 'Luxury formal coordinates suitable for upscale corporate events.', 'Women', 'Formals', 3399, 'formals_women_10.jpg', 5, 'S, M, L, XL, XXL'),

        # Wedding Outfits
        ('Wedding Outfit #1', 'WED-001', 'Premium elegant wedding designer wear coordinate set.', 'Women', 'Wedding', 2099, 'wedding_1.jpg', 10, 'S, M, L, XL, XXL'),
        ('Wedding Outfit #2', 'WED-002', 'Premium elegant wedding designer wear coordinate set.', 'Women', 'Wedding', 2199, 'wedding_2.jpg', 10, 'S, M, L, XL, XXL'),
        ('Wedding Outfit #3', 'WED-003', 'Premium elegant wedding designer wear coordinate set.', 'Women', 'Wedding', 2299, 'wedding_3.jpg', 10, 'S, M, L, XL, XXL'),
        ('Wedding Outfit #4', 'WED-004', 'Premium elegant wedding designer wear coordinate set.', 'Women', 'Wedding', 2399, 'wedding_4.jpg', 10, 'S, M, L, XL, XXL'),
        ('Wedding Outfit #5', 'WED-005', 'Premium elegant wedding designer wear coordinate set.', 'Women', 'Wedding', 2499, 'wedding_5.jpg', 10, 'S, M, L, XL, XXL'),
        ('Wedding Outfit #6', 'WED-006', 'Premium elegant wedding designer wear coordinate set.', 'Women', 'Wedding', 2599, 'wedding_6.jpg', 10, 'S, M, L, XL, XXL'),
        ('Wedding Outfit #7', 'WED-007', 'Premium elegant wedding designer wear coordinate set.', 'Women', 'Wedding', 2699, 'wedding_7.jpg', 10, 'S, M, L, XL, XXL'),
        ('Wedding Outfit #8', 'WED-008', 'Premium elegant wedding designer wear coordinate set.', 'Women', 'Wedding', 2799, 'wedding_8.jpg', 10, 'S, M, L, XL, XXL'),
        ('Wedding Outfit #9', 'WED-009', 'Premium elegant wedding designer wear coordinate set.', 'Women', 'Wedding', 2899, 'wedding_9.jpg', 10, 'S, M, L, XL, XXL'),
        ('Wedding Outfit #10', 'WED-010', 'Premium elegant wedding designer wear coordinate set.', 'Women', 'Wedding', 2999, 'wedding_10.jpg', 10, 'S, M, L, XL, XXL'),
        ('Wedding Outfit #11', 'WED-011', 'Premium elegant wedding designer wear coordinate set.', 'Women', 'Wedding', 3099, 'wedding_11.png', 10, 'S, M, L, XL, XXL'),
        ('Wedding Outfit #12', 'WED-012', 'Premium elegant wedding designer wear coordinate set.', 'Women', 'Wedding', 3199, 'wedding_12.png', 10, 'S, M, L, XL, XXL'),
        ('Wedding Outfit #13', 'WED-013', 'Premium elegant wedding designer wear coordinate set.', 'Women', 'Wedding', 3299, 'wedding_13.jpg', 10, 'S, M, L, XL, XXL'),
        ('Wedding Outfit #14', 'WED-014', 'Premium elegant wedding designer wear coordinate set.', 'Women', 'Wedding', 3399, 'wedding_14.avif', 10, 'S, M, L, XL, XXL'),

        # Festive Outfits
        ('Festive Outfit #1', 'FES-001', 'Premium elegant festive designer wear coordinate set.', 'Women', 'Festive', 2099, 'festive_1.jpg', 10, 'S, M, L, XL, XXL'),
        ('Festive Outfit #2', 'FES-002', 'Premium elegant festive designer wear coordinate set.', 'Women', 'Festive', 2199, 'festive_2.jpg', 10, 'S, M, L, XL, XXL'),
        ('Festive Outfit #3', 'FES-003', 'Premium elegant festive designer wear coordinate set.', 'Women', 'Festive', 2299, 'festive_3.jpg', 10, 'S, M, L, XL, XXL'),
        ('Festive Outfit #4', 'FES-004', 'Premium elegant festive designer wear coordinate set.', 'Women', 'Festive', 2399, 'festive_4.jpg', 10, 'S, M, L, XL, XXL'),
        ('Festive Outfit #5', 'FES-005', 'Premium elegant festive designer wear coordinate set.', 'Women', 'Festive', 2499, 'festive_5.jpg', 10, 'S, M, L, XL, XXL'),
        ('Festive Outfit #6', 'FES-006', 'Premium elegant festive designer wear coordinate set.', 'Women', 'Festive', 2599, 'festive_6.jpg', 10, 'S, M, L, XL, XXL'),
        ('Festive Outfit #7', 'FES-007', 'Premium elegant festive designer wear coordinate set.', 'Women', 'Festive', 2699, 'festive_7.jpg', 10, 'S, M, L, XL, XXL'),
        ('Festive Outfit #8', 'FES-008', 'Premium elegant festive designer wear coordinate set.', 'Women', 'Festive', 2799, 'festive_8.jpg', 10, 'S, M, L, XL, XXL'),
        ('Festive Outfit #9', 'FES-009', 'Premium elegant festive designer wear coordinate set.', 'Women', 'Festive', 2899, 'festive_9.jpg', 10, 'S, M, L, XL, XXL'),
        ('Festive Outfit #10', 'FES-010', 'Premium elegant festive designer wear coordinate set.', 'Women', 'Festive', 2999, 'festive_10.jpg', 10, 'S, M, L, XL, XXL'),
        ('Festive Outfit #11', 'FES-011', 'Premium elegant festive designer wear coordinate set.', 'Women', 'Festive', 3099, 'festive_11.png', 10, 'S, M, L, XL, XXL'),
        ('Festive Outfit #12', 'FES-012', 'Premium elegant festive designer wear coordinate set.', 'Women', 'Festive', 3199, 'festive_12.png', 10, 'S, M, L, XL, XXL'),
        ('Festive Outfit #13', 'FES-013', 'Premium elegant festive designer wear coordinate set.', 'Women', 'Festive', 3299, 'festive_13.jpg', 10, 'S, M, L, XL, XXL'),

        # College Outfits
        ('College Outfit #1', 'COL-001', 'Premium elegant college designer wear coordinate set.', 'Women', 'College', 2099, 'college_1.png', 10, 'S, M, L, XL, XXL'),
        ('College Outfit #2', 'COL-002', 'Premium elegant college designer wear coordinate set.', 'Women', 'College', 2199, 'college_2.jfif', 10, 'S, M, L, XL, XXL'),
        ('College Outfit #3', 'COL-003', 'Premium elegant college designer wear coordinate set.', 'Women', 'College', 2299, 'college_3.jpg', 10, 'S, M, L, XL, XXL'),
        ('College Outfit #4', 'COL-004', 'Premium elegant college designer wear coordinate set.', 'Women', 'College', 2399, 'college_4.jpg', 10, 'S, M, L, XL, XXL'),
        ('College Outfit #5', 'COL-005', 'Premium elegant college designer wear coordinate set.', 'Women', 'College', 2499, 'college_5.jpg', 10, 'S, M, L, XL, XXL'),
        ('College Outfit #6', 'COL-006', 'Premium elegant college designer wear coordinate set.', 'Women', 'College', 2599, 'college_6.jpg', 10, 'S, M, L, XL, XXL'),
        ('College Outfit #7', 'COL-007', 'Premium elegant college designer wear coordinate set.', 'Women', 'College', 2699, 'college_7.jpg', 10, 'S, M, L, XL, XXL'),
        ('College Outfit #8', 'COL-008', 'Premium elegant college designer wear coordinate set.', 'Women', 'College', 2799, 'college_8.jpg', 10, 'S, M, L, XL, XXL'),
        ('College Outfit #9', 'COL-009', 'Premium elegant college designer wear coordinate set.', 'Women', 'College', 2899, 'college_9.png', 10, 'S, M, L, XL, XXL')
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
    ]
    cursor.executemany('''
        INSERT INTO reviews (product_id, user_name, rating, comment)
        VALUES (?, ?, ?, ?)
    ''', sample_reviews)
    print("Sample reviews inserted.")

    # Insert some sample orders (reservations) for analytics
    sample_orders = [
        ('Karan Malhotra', 'karan@gmail.com', '9876543210', 'Executive Tailored Pantsuit', 2499, 'M', 'Pending'),
        ('Sarah Khan', 'sarah@gmail.com', '9812345670', 'Wedding Outfit #1', 2099, 'S', 'Completed'),
        ('Amit Verma', 'amit@gmail.com', '9988776655', 'Evening Velvet Tuxedo', 2049, 'L', 'Processing'),
        ('Rita Roy', 'rita@gmail.com', '9123456789', 'Evening Velvet Tuxedo', 2049, 'XL', 'Completed'),
        ('Jatin Paul', 'jatin@gmail.com', '8877665544', 'Executive Tailored Pantsuit', 2499, 'M', 'Completed'),
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
        ("What is the Fabric Visualizer?", "The Fabric Visualizer is an interactive page on our website where you can select luxury fabric swatches (like Emerald Satin Silk, Ruby Raw Silk, Midnight Velvet, Champagne Brocade, or Georgette) to dynamically preview fabric coordinates and drapes on our style mannequin model!"),
        ("How does the fabric visualizer work?", "Navigate to the 'Fabric Visualizer' page in the top menu and click on any colored swatch. The visualizer overlay will update the dress color on the model mannequin and display detailed information about the fabric weave, composition, wash care instructions, and link matching garments from the WearWise collection!"),
        ("How can I track my order?", "Click the highlighted 'Track Order' button in the top navigation bar or navigate to /track. Enter the email address or phone number you used during reservation and your complete order status will be shown instantly with a live step-by-step progress tracker!"),
        ("Where is my order?", "To check your order status, click 'Track Order' in the navbar or visit /track and enter your registered email or phone number. You will see a live progress timeline showing whether your order is Pending, Processing, Approved, or Completed and dispatched."),
        ("track my order", "You can track your reservation from the Track Order page! Just enter your email or phone number to see the live status of all your orders.")
    ]
    cursor.executemany("INSERT OR IGNORE INTO chatbot_qa (question, answer) VALUES (?, ?)", predefined_qa)
    print("Chatbot QA table seeded.")

    conn.commit()
    conn.close()
    print("Database initialization complete.")

if __name__ == '__main__':
    init_db()
