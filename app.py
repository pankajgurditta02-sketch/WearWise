from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
import os
import sqlite3
from werkzeug.utils import secure_filename
import pandas as pd
from models.body_analysis import analyze_body
from xhtml2pdf import pisa
from io import BytesIO

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
    
    # Calculate deterministically
    analysis = analyze_body(filepath, gender, skin_tone)
    if analysis and "error" not in analysis:
        analysis['body_type'] = analysis['body_type_detection']['type']
        analysis['predicted_size'] = analysis['size_prediction']['size']
        analysis['skin_tone'] = skin_tone
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
    if 'image_path' in session:
        return dict(session=FakeSession(session))
    return dict(session=session)


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
        
        # Store only metadata in session to stay within 4KB cookie limits
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
        df = pd.DataFrame()

    if not df.empty:
        # Filter products to match the user's predicted size from the AI analysis
        if 'size' in df.columns:
            df = df[df['size'].astype(str).str.strip().str.upper() == predicted_size.strip().upper()]
        # Sort by style_match score descending
        df = df.sort_values(by='style_match', ascending=False)
        products = df.to_dict('records')
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
        skin_tone = session.get('analysis', {}).get('skin_tone', 'Medium')
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
            return f"Error generating PDF: {pisa_status.err}"
            
        response = make_response(pdf_io.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=wearwise_report.pdf'
        return response
    except Exception as e:
        return f"Error generating PDF. Detail: {e}"

if __name__ == '__main__':
    app.run(debug=True)
