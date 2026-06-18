from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
import os
import sqlite3
from werkzeug.utils import secure_filename
import pandas as pd
from models.body_analysis import analyze_body
from xhtml2pdf import pisa
from io import BytesIO
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Use environment variable for secret key, fallback to a generated one
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(32).hex())

UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Use environment variable for database path, fallback to current directory
DB_PATH = os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(__file__), 'database.db'))

def get_db_connection():
    """Get a database connection with proper error handling."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise

def init_db():
    """Initialize database with all required tables."""
    try:
        conn = sqlite3.connect(DB_PATH)
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

        # Insert default admin user if not exists
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password) VALUES ('admin', 'admin')")
            logger.info("Default admin user created (admin/admin)")

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
            logger.info("Sample products inserted.")

        conn.commit()
        conn.close()
        logger.info("Database initialization complete.")
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        raise

def get_current_analysis():
    """Get current body analysis from session."""
    if 'image_path' not in session:
        return None
    try:
        image_path = session['image_path']
        filepath = os.path.join(app.root_path, 'static', image_path)
        gender = session.get('gender', 'Women')
        skin_tone = session.get('skin_tone', 'Medium')
        
        # Calculate deterministically
        analysis = analyze_body(filepath, gender, skin_tone)
        if analysis and "error" not in analysis:
            analysis['body_type'] = analysis['body_type_detection']['type']
            analysis['predicted_size'] = analysis['size_prediction']['size']
            analysis['skin_tone'] = skin_tone
            return analysis
    except Exception as e:
        logger.error(f"Error getting current analysis: {e}")
    return None

class FakeSession(dict):
    """Custom session class to compute analysis on-demand."""
    def get(self, key, default=None):
        if key == 'analysis':
            return get_current_analysis()
        return super().get(key, default)
    
    def __getitem__(self, key):
        if key == 'analysis':
            analysis = get_current_analysis()
            if analysis is None:
                raise KeyError('analysis')
            return analysis
        return super().__getitem__(key)

@app.context_processor
def inject_session():
    """Inject session into template context."""
    if 'image_path' in session:
        return dict(session=FakeSession(session))
    return dict(session=session)

@app.route('/')
def index():
    """Home page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    """Handle file upload and body analysis."""
    try:
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        gender = request.form.get('gender', 'Women')
        skin_tone = request.form.get('skin_tone', 'Medium')
        
        if file.filename == '':
            return redirect(request.url)
            
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Analyze Body
            analysis = analyze_body(filepath, gender, skin_tone)
            if "error" in analysis:
                logger.error(f"Analysis error: {analysis['error']}")
                return f"Error: {analysis['error']}"
                
            # Log to analytics
            body_type = analysis['body_type_detection']['type']
            predicted_size = analysis['size_prediction']['size']
            
            conn = get_db_connection()
            conn.execute('INSERT INTO uploads (predicted_size, body_type, gender) VALUES (?, ?, ?)',
                         (predicted_size, body_type, gender))
            conn.commit()
            conn.close()
            
            # Store only metadata in session to stay within 4KB cookie limits
            session['image_path'] = f'uploads/{filename}'
            session['gender'] = gender
            session['skin_tone'] = skin_tone
            
            return redirect(url_for('result'))
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return f"Upload failed: {str(e)}", 500

@app.route('/result')
def result():
    """Display analysis results."""
    if 'image_path' not in session:
        return redirect(url_for('index'))
    return render_template('result.html')

@app.route('/recommendations')
def recommendations():
    """Get product recommendations based on analysis."""
    try:
        if 'image_path' not in session:
            return redirect(url_for('index'))
            
        analysis = get_current_analysis()
        if not analysis:
            return redirect(url_for('index'))
            
        predicted_size = analysis['size_prediction']['size']
        style_dna = analysis.get('style_dna', {})
        top_style = max(style_dna, key=style_dna.get) if style_dna else "Luxury"
        
        csv_path = os.path.join(os.path.dirname(__file__), 'wearwise_products.csv')
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            logger.warning(f"Could not load products CSV: {e}")
            df = pd.DataFrame()

        if not df.empty:
            # Sort by style_match score descending
            df = df.sort_values(by='style_match', ascending=False)
            products = df.to_dict('records')
        else:
            products = []
        
        return render_template('recommendations.html', products=products)
    except Exception as e:
        logger.error(f"Recommendations error: {e}")
        return f"Error loading recommendations: {str(e)}", 500

@app.route('/api/bmi', methods=['POST'])
def bmi_api():
    """BMI calculation API (deprecated/mocked)."""
    return jsonify({"bmi": 0, "category": "N/A"})

@app.route('/api/chat', methods=['POST'])
def chat_api():
    """Chat API for styling advice."""
    try:
        data = request.json or {}
        msg = data.get('message', '').lower()
        
        # Retrieve user analysis context if available
        analysis = get_current_analysis()
        predicted_size = None
        body_type = None
        
        if analysis:
            predicted_size = analysis.get('size_prediction', {}).get('size')
            body_type = analysis.get('body_type_detection', {}).get('type')
            
        # Smart keyword matching
        if 'size' in msg or 'measure' in msg:
            if predicted_size:
                reply = f"Based on your photo analysis, your predicted size is **{predicted_size}**. This size corresponds to your shoulder-to-hip proportions."
            else:
                reply = "I recommend uploading a full-body photo on the home page so I can precisely calculate your premium size using computer vision."
                
        elif 'body type' in msg or 'shape' in msg:
            if body_type:
                reply = f"Your analyzed body silhouette is **{body_type}**. For this shape, we recommend structured tailoring that accentuates your natural frame."
            else:
                reply = "Upload a photo first so I can detect your body type (e.g., Rectangle, Oval, Triangle) and suggest optimized fits!"
                
        elif 'color' in msg or 'skin' in msg or 'palette' in msg:
            skin_tone = session.get('skin_tone', 'Medium')
            reply = f"Since your skin tone profile is analyzed as {skin_tone}, we recommend rich jewel tones (like Emerald or Maroon) and luxury neutrals (like Charcoal, Cream, and Gold)."
            
        elif 'wedding' in msg or 'formal' in msg or 'party' in msg:
            reply = "For formal occasions, a tailored luxury suit in Navy or deep Charcoal is timeless. We've matched some premium suits in your Collection page!"
            
        elif 'fit' in msg or 'cut' in msg:
            if body_type:
                reply = f"With your **{body_type}** silhouette, a structured slim or tailored fit works beautifully to keep your lines clean and premium."
            else:
                reply = "A tailored slim fit is highly recommended for luxury suits. Once you upload your photo, I can give you fit recommendations tailored to your silhouette."
                
        elif 'hello' in msg or 'hi' in msg or 'hey' in msg:
            if predicted_size:
                reply = f"Hello! I see we've analyzed your style profile. You can ask me about styling for your **{predicted_size}** size, body shape, or fit suggestions."
            else:
                reply = "Hello! I am your virtual stylist. Upload a photo to start, or ask me any question about sizing, colors, or fits!"
                
        elif 'thank' in msg:
            reply = "It's my pleasure! Let me know if you want tips on accessories, suit selections, or fabric care."
            
        else:
            if body_type:
                reply = f"I've analyzed your styling details. I recommend exploring the **Collection** tab for outfits suited for a **{body_type}** body structure, or ask about size or color palette."
            else:
                reply = "That's an interesting style query! You can ask me about sizes, fit matching, color palettes, or how to style for specific occasions like weddings."
                
        return jsonify({"reply": reply})
    except Exception as e:
        logger.error(f"Chat API error: {e}")
        return jsonify({"reply": "Sorry, I encountered an error. Please try again."}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login."""
    try:
        if request.method == 'POST':
            username = request.form.get('username', '')
            password = request.form.get('password', '')
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
            conn.close()
            
            if user:
                session['admin'] = True
                return redirect(url_for('admin'))
            else:
                return "Invalid Credentials", 401
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Login error: {e}")
        return f"Login error: {str(e)}", 500

@app.route('/logout')
def logout():
    """Admin logout."""
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    """Admin dashboard."""
    try:
        if not session.get('admin'):
            return redirect(url_for('login'))
            
        conn = get_db_connection()
        products = conn.execute('SELECT * FROM products').fetchall()
        
        # Analytics
        total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        total_uploads = conn.execute('SELECT COUNT(*) FROM uploads').fetchone()[0]
        
        # Most recommended size
        top_size_row = conn.execute('SELECT predicted_size, COUNT(*) as count FROM uploads GROUP BY predicted_size ORDER BY count DESC LIMIT 1').fetchone()
        top_size = top_size_row['predicted_size'] if top_size_row else "N/A"
        
        # Most common body type
        top_body_row = conn.execute('SELECT body_type, COUNT(*) as count FROM uploads GROUP BY body_type ORDER BY count DESC LIMIT 1').fetchone()
        top_body = top_body_row['body_type'] if top_body_row else "N/A"
        
        conn.close()
        
        stats = {
            "total_users": total_users,
            "total_uploads": total_uploads,
            "top_size": top_size,
            "top_body": top_body
        }
        
        return render_template('admin.html', products=products, stats=stats)
    except Exception as e:
        logger.error(f"Admin error: {e}")
        return f"Admin error: {str(e)}", 500

@app.route('/admin/add', methods=['POST'])
def add_product():
    """Add a new product."""
    try:
        if not session.get('admin'):
            return redirect(url_for('login'))
            
        name = request.form.get('name', '')
        code = request.form.get('code', '')
        desc = request.form.get('description', '')
        gender = request.form.get('gender', '')
        cat = request.form.get('category', '')
        body_type = request.form.get('body_type_suitability', '')
        fit = request.form.get('suggested_fit', '')
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO products (name, code, description, gender, category, body_type_suitability, suggested_fit) VALUES (?, ?, ?, ?, ?, ?, ?)',
                         (name, code, desc, gender, cat, body_type, fit))
            conn.commit()
        except sqlite3.IntegrityError as e:
            logger.warning(f"Product insert error (likely duplicate): {e}")
        finally:
            conn.close()
        
        return redirect(url_for('admin'))
    except Exception as e:
        logger.error(f"Add product error: {e}")
        return f"Error adding product: {str(e)}", 500

@app.route('/admin/delete/<int:id>')
def delete_product(id):
    """Delete a product."""
    try:
        if not session.get('admin'):
            return redirect(url_for('login'))
        conn = get_db_connection()
        conn.execute('DELETE FROM products WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return redirect(url_for('admin'))
    except Exception as e:
        logger.error(f"Delete product error: {e}")
        return f"Error deleting product: {str(e)}", 500

@app.route('/generate_pdf')
def generate_pdf():
    """Generate PDF report."""
    try:
        if 'image_path' not in session:
            return redirect(url_for('index'))
            
        analysis = get_current_analysis()
        if not analysis:
            return redirect(url_for('index'))
            
        # Resolve the absolute path of the uploaded image for xhtml2pdf compatibility
        image_path = session['image_path']
        abs_image_path = os.path.join(app.root_path, 'static', image_path)
        abs_image_path = abs_image_path.replace('\\', '/')

        html = render_template('pdf_report.html', 
                               analysis=analysis,
                               image_path=abs_image_path)
                               
        try:
            pdf_io = BytesIO()
            pisa_status = pisa.CreatePDF(html, dest=pdf_io)
            
            if pisa_status.err:
                logger.error(f"PDF generation error: {pisa_status.err}")
                return f"Error generating PDF: {pisa_status.err}", 500
                
            response = make_response(pdf_io.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = 'attachment; filename=wearwise_report.pdf'
            return response
        except Exception as e:
            logger.error(f"PDF creation error: {e}")
            return f"Error generating PDF. Detail: {e}", 500
    except Exception as e:
        logger.error(f"Generate PDF error: {e}")
        return f"Error: {str(e)}", 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return "Page not found", 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return "Internal server error", 500

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    
    # Get port from environment variable, default to 5000 for local development
    port = int(os.environ.get('PORT', 5000))
    
    # Run app
    app.run(host='0.0.0.0', port=port, debug=False)

