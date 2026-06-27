from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
import os
import sqlite3
from werkzeug.utils import secure_filename
import uuid
import base64
from models.body_analysis import analyze_body
from models.recommendation import get_style_recommendations
from models.virtual_tryon import generate_tryon

app = Flask(__name__)
app.secret_key = 'wearwise_super_secret_key'
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_current_analysis():
    if 'image_path' not in session:
        return None
    image_path = session['image_path']
    filepath = os.path.join(app.root_path, 'static', image_path)
    gender = session.get('gender', 'Women')
    skin_tone = session.get('skin_tone', 'Medium')
    
    analysis = analyze_body(filepath, gender, skin_tone)
    if analysis:
        return analysis
    return None

class FakeSession(dict):
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
    # Make cart count globally available
    cart_count = len(session.get('cart', []))
    if 'image_path' in session:
        return dict(session=FakeSession(session), cart_count=cart_count)
    return dict(session=session, cart_count=cart_count)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    # Can accept standard multipart file upload OR base64 camera input JSON
    gender = 'Women'
    skin_tone = 'Medium'
    
    # Handle Base64 Camera JSON
    if request.is_json:
        data = request.json
        image_data = data.get('image')
        gender = data.get('gender', 'Women')
        skin_tone = data.get('skin_tone', 'Medium')
        
        if not image_data:
            return jsonify({"success": False, "error": "No image data provided"}), 400
            
        try:
            header, encoded = image_data.split(",", 1)
            data_bytes = base64.b64decode(encoded)
            filename = f"scan_{uuid.uuid4().hex}.jpg"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(filepath, "wb") as f:
                f.write(data_bytes)
                
            # Log scan in uploads table
            conn = get_db_connection()
            conn.execute('INSERT INTO uploads (gender, skin_tone) VALUES (?, ?)', (gender, skin_tone))
            conn.commit()
            conn.close()
            
            session['image_path'] = f'uploads/{filename}'
            session['gender'] = gender
            session['skin_tone'] = skin_tone
            
            return jsonify({"success": True, "redirect": url_for('result')})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # Fallback to standard multipart upload
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
        
        conn = get_db_connection()
        conn.execute('INSERT INTO uploads (gender, skin_tone) VALUES (?, ?)', (gender, skin_tone))
        conn.commit()
        conn.close()
        
        session['image_path'] = f'uploads/{filename}'
        session['gender'] = gender
        session['skin_tone'] = skin_tone
        
        return redirect(url_for('result'))

@app.route('/result')
def result():
    if 'image_path' not in session:
        return redirect(url_for('index'))
    return render_template('result.html')

@app.route('/recommendations')
def recommendations():
    gender = session.get('gender', 'Women')
    skin_tone = session.get('skin_tone', 'Medium')
    
    analysis = get_current_analysis()
    if not analysis:
        # Load default styling attributes for guest browsing
        analysis = {
            "style_dna": {"Minimalist": 40, "Smart Casual": 30, "Luxury Classic": 30},
            "color_analysis": {"best": ["Emerald Green", "Royal Blue"], "accent": ["Gold", "Rose Gold"], "avoid": ["Neon Orange"]},
            "fashion_summary": "Explore our premium handpicked coordinates."
        }
        
    style_dna = analysis.get('style_dna', {})
    
    # Fetch products with dynamic compatibility and review counts
    conn = get_db_connection()
    products_db = conn.execute('''
        SELECT p.*, COALESCE(AVG(r.rating), 0.0) as avg_rating, COUNT(r.id) as review_count
        FROM products p
        LEFT JOIN reviews r ON p.id = r.product_id
        GROUP BY p.id
    ''').fetchall()
    
    # Calculate visual matching score
    products = []
    top_style = max(style_dna, key=style_dna.get) if style_dna else "Minimalist"
    
    for p in products_db:
        p_dict = dict(p)
        p_dict['avg_rating'] = round(p_dict['avg_rating'], 1)
        
        # Determine styling fit compatibility
        gender_match = 1.0 if p_dict['gender'].lower() == gender.lower() else 0.4
        
        p_cat = p_dict['category'].lower()
        category_match = 0.5
        if "classic" in top_style.lower() and p_cat in ["office", "wedding"]:
            category_match = 1.0
        elif "casual" in top_style.lower() and p_cat in ["casual", "college"]:
            category_match = 1.0
        elif "business" in top_style.lower() and p_cat in ["office"]:
            category_match = 1.0
        elif "contemporary" in top_style.lower() and p_cat in ["party", "festive"]:
            category_match = 1.0
            
        compatibility = int((gender_match * 60) + (category_match * 40))
        p_dict['compatibility_score'] = max(60, min(99, compatibility))
        
        # Load reviews list for this product
        reviews = conn.execute('SELECT * FROM reviews WHERE product_id = ? ORDER BY timestamp DESC', (p['id'],)).fetchall()
        p_dict['reviews'] = [dict(rev) for rev in reviews]
        
        products.append(p_dict)
        
    conn.close()
    
    # Sort by compatibility
    products.sort(key=lambda x: x['compatibility_score'], reverse=True)
    return render_template('recommendations.html', products=products)

# Review API
@app.route('/api/products/<int:product_id>/review', methods=['POST'])
def add_review(product_id):
    data = request.json
    user_name = data.get('user_name', 'Anonymous')
    rating = data.get('rating', 5)
    comment = data.get('comment', '').strip()
    
    if not comment:
        return jsonify({"success": False, "message": "Review comment cannot be empty."}), 400
        
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO reviews (product_id, user_name, rating, comment) VALUES (?, ?, ?, ?)',
                     (product_id, user_name, rating, comment))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Thank you for your feedback!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Cart API Actions
@app.route('/api/cart/add', methods=['POST'])
def cart_add():
    data = request.json
    product_id = data.get('product_id')
    size = data.get('size', 'M')
    
    if 'cart' not in session:
        session['cart'] = []
        
    session['cart'].append({"product_id": product_id, "size": size})
    session.modified = True
    return jsonify({"success": True, "cart_count": len(session['cart'])})

@app.route('/api/cart/clear', methods=['POST'])
def cart_clear():
    session.pop('cart', None)
    return jsonify({"success": True})

@app.route('/api/cart/checkout', methods=['POST'])
def cart_checkout():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    
    if not all([name, email, phone]):
        return jsonify({"success": False, "message": "Name, email and phone number are required."}), 400
        
    cart = session.get('cart', [])
    if not cart:
        return jsonify({"success": False, "message": "Your cart is empty."}), 400
        
    try:
        conn = get_db_connection()
        for item in cart:
            p_id = item['product_id']
            size = item['size']
            
            # Fetch product details
            prod = conn.execute('SELECT * FROM products WHERE id = ?', (p_id,)).fetchone()
            if prod:
                price = prod['price']
                suit_name = prod['name']
                
                # Insert order (reservation)
                conn.execute('''
                    INSERT INTO reservations (name, email, phone, suit_name, price, selected_size, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (name, email, phone, suit_name, price, size, 'Pending'))
                
                # Reduce stock quantity
                conn.execute('UPDATE products SET stock_quantity = MAX(0, stock_quantity - 1) WHERE id = ?', (p_id,))
                
        conn.commit()
        conn.close()
        
        session.pop('cart', None)
        return jsonify({"success": True, "message": "Order placed successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        
        if user:
            if user['role'] == 'admin':
                session['admin'] = True
                session['username'] = user['username']
                return redirect(url_for('admin'))
            else:
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid Username or Password")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'customer')", (username, password))
            conn.commit()
            conn.close()
            return render_template('login.html', success="Registration successful! Please login.")
        except Exception:
            conn.close()
            return render_template('register.html', error="Username already exists")
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    reservations = conn.execute('SELECT * FROM reservations ORDER BY timestamp DESC').fetchall()
    
    # Enhanced Analytics
    total_scans = conn.execute('SELECT COUNT(*) FROM uploads').fetchone()[0]
    total_orders = conn.execute('SELECT COUNT(*) FROM reservations').fetchone()[0]
    today_orders = conn.execute("SELECT COUNT(*) FROM reservations WHERE date(timestamp) = date('now')").fetchone()[0]
    pending_orders = conn.execute("SELECT COUNT(*) FROM reservations WHERE status = 'Pending'").fetchone()[0]
    completed_orders = conn.execute("SELECT COUNT(*) FROM reservations WHERE status = 'Completed'").fetchone()[0]
    
    total_customers = conn.execute('SELECT COUNT(DISTINCT email) FROM reservations').fetchone()[0]
    total_revenue_row = conn.execute("SELECT SUM(price) FROM reservations WHERE status != 'Cancelled'").fetchone()
    total_revenue = total_revenue_row[0] if total_revenue_row[0] is not None else 0
    
    # Graphs Data (Sales trends over past 7 days)
    sales_trend_rows = conn.execute('''
        SELECT date(timestamp) as day, SUM(price) as sales, COUNT(id) as count 
        FROM reservations 
        GROUP BY day 
        ORDER BY day ASC 
        LIMIT 7
    ''').fetchall()
    
    trend_labels = [row['day'] for row in sales_trend_rows]
    trend_sales = [row['sales'] for row in sales_trend_rows]
    trend_counts = [row['count'] for row in sales_trend_rows]
    
    # Popular Categories
    cat_rows = conn.execute('''
        SELECT suit_name, COUNT(id) as count 
        FROM reservations 
        GROUP BY suit_name 
        ORDER BY count DESC 
        LIMIT 5
    ''').fetchall()
    cat_labels = [row['suit_name'] for row in cat_rows]
    cat_counts = [row['count'] for row in cat_rows]

    conn.close()
    
    stats = {
        "total_scans": total_scans,
        "total_orders": total_orders,
        "today_orders": today_orders,
        "pending_orders": pending_orders,
        "completed_orders": completed_orders,
        "total_customers": total_customers,
        "total_revenue": total_revenue,
        "total_products": len(products)
    }
    
    # Size-wise sales breakdown
    size_sales = {}
    try:
        size_rows = db.execute("SELECT size, SUM(quantity) as total FROM order_items GROUP BY size ORDER BY total DESC").fetchall()
        for row in size_rows:
            size_sales[row['size']] = row['total']
    except Exception:
        pass
    size_labels = list(size_sales.keys()) if size_sales else []
    size_counts = list(size_sales.values()) if size_sales else []

    graph_data = {
        "trend_labels": trend_labels,
        "trend_sales": trend_sales,
        "trend_counts": trend_counts,
        "cat_labels": cat_labels,
        "cat_counts": cat_counts,
        "size_labels": size_labels,
        "size_counts": size_counts
    }
    
    return render_template('admin.html', products=products, stats=stats, reservations=reservations, graph_data=graph_data)

# Update Order Status checkmarks
@app.route('/admin/order/status', methods=['POST'])
def update_order_status():
    if not session.get('admin'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    data = request.json
    order_id = data.get('id')
    status = data.get('status')
    
    try:
        conn = get_db_connection()
        conn.execute('UPDATE reservations SET status = ? WHERE id = ?', (status, order_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Add/Edit/Delete products
@app.route('/admin/product/add', methods=['POST'])
def add_product():
    if not session.get('admin'):
        return redirect(url_for('login'))
        
    name = request.form['name']
    code = request.form['code']
    desc = request.form['description']
    gender = request.form['gender']
    cat = request.form['category']
    price = int(request.form.get('price', 2999))
    stock = int(request.form.get('stock', 10))
    sizes = request.form.get('sizes', 'S, M, L, XL, XXL')
    suggested_fit = request.form.get('suggested_fit', 'Regular Fit')
    body_type_suitability = request.form.get('body_type_suitability', 'All Body Types')
    
    # Handle Image Upload
    image_file = request.files.get('image')
    image_filename = "suit1.jpg"
    if image_file and image_file.filename:
        filename = secure_filename(image_file.filename)
        products_dir = os.path.join(app.root_path, 'static', 'products')
        os.makedirs(products_dir, exist_ok=True)
        image_file.save(os.path.join(products_dir, filename))
        image_filename = filename

    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO products (name, code, description, gender, category, price, image, stock_quantity, available_sizes, suggested_fit, body_type_suitability)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, code, desc, gender, cat, price, image_filename, stock, sizes, suggested_fit, body_type_suitability))
        conn.commit()
    except Exception as e:
        print(f"Error adding product: {e}")
    conn.close()
    
    return redirect(url_for('admin'))

@app.route('/admin/product/edit/<int:id>', methods=['POST'])
def edit_product(id):
    if not session.get('admin'):
        return redirect(url_for('login'))
        
    name = request.form['name']
    code = request.form['code']
    desc = request.form['description']
    gender = request.form['gender']
    cat = request.form['category']
    price = int(request.form.get('price', 2999))
    stock = int(request.form.get('stock', 10))
    sizes = request.form.get('sizes', 'S, M, L, XL, XXL')
    suggested_fit = request.form.get('suggested_fit', 'Regular Fit')
    body_type_suitability = request.form.get('body_type_suitability', 'All Body Types')
    
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE products 
            SET name = ?, code = ?, description = ?, gender = ?, category = ?, price = ?, stock_quantity = ?, available_sizes = ?, suggested_fit = ?, body_type_suitability = ?
            WHERE id = ?
        ''', (name, code, desc, gender, cat, price, stock, sizes, suggested_fit, body_type_suitability, id))
        conn.commit()
    except Exception as e:
        print(f"Error editing product: {e}")
    conn.close()
    
    return redirect(url_for('admin'))

@app.route('/admin/product/delete/<int:id>')
def delete_product(id):
    if not session.get('admin'):
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

# Virtual Try-On progressive endpoints
@app.route('/tryon')
def tryon():
    return render_template('tryon.html')

@app.route('/api/tryon/upload', methods=['POST'])
def tryon_upload():
    data = request.json
    image_data = data.get('image')
    if not image_data:
        return jsonify({"success": False, "error": "No image data provided"}), 400
    
    try:
        header, encoded = image_data.split(",", 1)
        data_bytes = base64.b64decode(encoded)
        
        filename = f"tryon_{uuid.uuid4().hex}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(filepath, "wb") as f:
            f.write(data_bytes)
        
        # Get all products from SQLite
        conn = get_db_connection()
        products = conn.execute('SELECT * FROM products').fetchall()
        conn.close()
        
        products_list = []
        for row in products:
            products_list.append({
                "id": row['id'],
                "name": row['name'],
                "price": row['price'],
                "sizes": row['available_sizes'],
                "category": row['category'],
                "image": row['image']
            })
        
        return jsonify({
            "success": True,
            "upload_id": filename,
            "products": products_list
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/tryon/generate/<upload_id>/<int:product_id>')
def tryon_generate(upload_id, product_id):
    upload_id = secure_filename(upload_id)
    user_path = os.path.join(app.config['UPLOAD_FOLDER'], upload_id)
    if not os.path.exists(user_path):
        return jsonify({"success": False, "error": "User image not found"}), 404
        
    conn = get_db_connection()
    product_row = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    
    if not product_row:
        return jsonify({"success": False, "error": "Product not found"}), 404
        
    product_img_name = product_row['image']
    product_path = os.path.join(app.root_path, 'static', 'products', product_img_name)
    if not os.path.exists(product_path):
        return jsonify({"success": False, "error": f"Product image file not found: {product_img_name}"}), 404
        
    out_filename = f"tryon_out_{product_id}_{upload_id}"
    out_path = os.path.join(app.config['UPLOAD_FOLDER'], out_filename)
    
    try:
        success = generate_tryon(user_path, product_path, out_path)
        if success:
            return jsonify({
                "success": True,
                "image_url": url_for('static', filename=f"uploads/{out_filename}"),
                "product_id": product_id
            })
        else:
            return jsonify({"success": False, "error": "Generation failed"}), 500
    except Exception as e:
        error_msg = str(e)
        if "GPU_RUNTIME_REQUIRED" in error_msg:
            return jsonify({
                "success": False, 
                "error": "GPU_RUNTIME_REQUIRED", 
                "message": "A GPU-enabled runtime environment (PyTorch + CUDA) is required to execute the CatVTON / IDM-VTON model pipeline."
            }), 400
        else:
            return jsonify({"success": False, "error": error_msg}), 500

if __name__ == '__main__':
    app.run(debug=True)
