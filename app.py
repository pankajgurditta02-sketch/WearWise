from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
import os
import sqlite3
from werkzeug.utils import secure_filename
import pandas as pd
from models.body_analysis import analyze_body
import pdfkit

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
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
            return f"Error: {analysis['error']}"
            
        # Log to analytics
        body_type = analysis['body_type_detection']['type']
        predicted_size = analysis['size_prediction']['size']
        
        conn = get_db_connection()
        conn.execute('INSERT INTO uploads (predicted_size, body_type, gender) VALUES (?, ?, ?)',
                     (predicted_size, body_type, gender))
        conn.commit()
        conn.close()
        
        # Store in session for result page
        session['analysis'] = analysis
        session['image_path'] = f'uploads/{filename}'
        session['gender'] = gender
        
        return redirect(url_for('result'))

@app.route('/result')
def result():
    if 'analysis' not in session:
        return redirect(url_for('index'))
    return render_template('result.html')

@app.route('/recommendations')
def recommendations():
    if 'analysis' not in session:
        return redirect(url_for('index'))
        
    predicted_size = session['analysis']['size_prediction']['size']
    style_dna = session['analysis'].get('style_dna', {})
    top_style = max(style_dna, key=style_dna.get) if style_dna else "Luxury"
    
    csv_path = os.path.join(os.path.dirname(__file__), 'wearwise_30_suits.csv')
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        df = pd.DataFrame()

    if not df.empty:
        size_matches = df[df['size'] == predicted_size].copy()
        
        def get_match_score(product_style):
            ps_lower = str(product_style).lower()
            ts_lower = str(top_style).lower()
            if ps_lower in ts_lower or ts_lower in ps_lower:
                return 98
            elif ps_lower == 'luxury':
                return 90
            elif ps_lower in ['festive', 'wedding', 'party wea']:
                return 85
            else:
                return 75
                
        size_matches['match_score'] = size_matches['style'].apply(get_match_score)
        size_matches = size_matches.sort_values(by='match_score', ascending=False)
        final_products = size_matches.head(6)
        
        if len(final_products) < 6:
            needed = 6 - len(final_products)
            alternatives = df[df['size'] != predicted_size].copy()
            alternatives['match_score'] = alternatives['style'].apply(get_match_score) - 10
            alternatives = alternatives.sort_values(by='match_score', ascending=False).head(needed)
            final_products = pd.concat([final_products, alternatives])
            
        products = final_products.to_dict('records')
    else:
        products = []
    
    return render_template('recommendations.html', products=products)

@app.route('/api/bmi', methods=['POST'])
def bmi_api():
    # Deprecated/mocked for now
    return jsonify({"bmi": 0, "category": "N/A"})

@app.route('/api/chat', methods=['POST'])
def chat_api():
    data = request.json
    msg = data.get('message', '').lower()
    
    # Mock AI Assistant responses
    if 'size' in msg:
        reply = "I recommend uploading a full-body photo so I can precisely determine your perfect size using our MediaPipe computer vision."
    elif 'color' in msg:
        reply = "Your best colors depend on your skin tone and body type. Upload a photo and select your skin tone, and I'll give you a personalized palette!"
    elif 'wedding' in msg:
        reply = "For weddings, rich colors like Maroon, Emerald, and Gold work beautifully. Try an elegant Saree or a tailored suit!"
    elif 'fit' in msg:
        reply = "A tailored or regular fit is universally flattering, but if you have an athletic build, a slim fit can accentuate your shoulders."
    else:
        reply = "That's a great fashion question! I'm best at analyzing body proportions and recommending fits. Try asking about sizes, colors, or event styling."
        
    return jsonify({"reply": reply})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        
        if user:
            session['admin'] = True
            return redirect(url_for('admin'))
        else:
            return "Invalid Credentials"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
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

@app.route('/admin/add', methods=['POST'])
def add_product():
    if not session.get('admin'):
        return redirect(url_for('login'))
        
    name = request.form['name']
    code = request.form['code']
    desc = request.form['description']
    gender = request.form['gender']
    cat = request.form['category']
    body_type = request.form['body_type_suitability']
    fit = request.form['suggested_fit']
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO products (name, code, description, gender, category, body_type_suitability, suggested_fit) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (name, code, desc, gender, cat, body_type, fit))
        conn.commit()
    except Exception as e:
        pass # Handle unique constraint error etc.
    conn.close()
    
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:id>')
def delete_product(id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/generate_pdf')
def generate_pdf():
    if 'analysis' not in session:
        return redirect(url_for('index'))
        
    html = render_template('pdf_report.html', 
                           analysis=session['analysis'])
                           
    try:
        # Look for wkhtmltopdf in the default Windows installation folder
        path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        
        if os.path.exists(path_wkhtmltopdf):
            config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
            pdf = pdfkit.from_string(html, False, configuration=config)
        else:
            # Fallback to checking the system PATH
            pdf = pdfkit.from_string(html, False)
            
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=wearwise_report.pdf'
        return response
    except Exception as e:
        return f"Error generating PDF. Please ensure wkhtmltopdf is installed. Detail: {e}"

if __name__ == '__main__':
    app.run(debug=True)
