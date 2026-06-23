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
    user_body = analysis.get('body_type_detection', {}).get('type', 'Regular')
    user_tone = session.get('skin_tone', 'Medium')
    
    csv_path = os.path.join(os.path.dirname(__file__), 'wearwise_products.csv')
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        df = pd.DataFrame()

    if not df.empty:
        dynamic_scores = []
        for index, row in df.iterrows():
            # Base match score from CSV
            base_score = int(row.get('match_score', 85))
            
            # Check compatibility
            body_match = 1.0 if str(row.get('body_type', '')).strip().lower() == user_body.strip().lower() else 0.5
            tone_match = 1.0 if str(row.get('skin_tone', '')).strip().lower() == user_tone.strip().lower() else 0.5
            
            # Category and Style DNA compatibility
            prod_cat = str(row.get('category', '')).strip().lower()
            style_bonus = 0
            for style, pct in style_dna.items():
                style_l = style.lower()
                if pct > 15:
                    if 'casual' in style_l and prod_cat in ['casual', 'college']:
                        style_bonus += 3
                    elif 'luxury' in style_l and prod_cat in ['wedding', 'office']:
                        style_bonus += 3
                    elif 'business' in style_l and prod_cat in ['office']:
                        style_bonus += 3
                    elif 'contemporary' in style_l and prod_cat in ['party', 'festive']:
                        style_bonus += 3
            
            # Calculate final score: weighted combination + small session-seeded variation
            import hashlib
            seed_key = f"{session.get('image_path', '')}_{row.get('id', '')}"
            val_hash = int(hashlib.md5(seed_key.encode()).hexdigest(), 16) % 10
            noise = (val_hash - 5) / 2.0  # -2.5 to 2.5
            
            computed_score = int(base_score * 0.7 + (body_match * 15) + (tone_match * 10) + style_bonus + noise)
            computed_score = max(50, min(99, computed_score))
            
            row_dict = row.to_dict()
            row_dict['style_match'] = computed_score
            row_dict['match_score'] = computed_score
            row_dict['size'] = predicted_size  # Override size to match predicted size
            dynamic_scores.append(row_dict)
            
        dynamic_scores.sort(key=lambda x: x['style_match'], reverse=True)
        products = dynamic_scores
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
    msg = data.get('message', '').strip()
    msg_lower = msg.lower()
    
    # Track cycle index in session to rotate variations
    if 'reply_cycle_index' not in session:
        session['reply_cycle_index'] = 0
    cycle_idx = session['reply_cycle_index']
    session['reply_cycle_index'] = cycle_idx + 1
    session.modified = True

    # Predefined 10 Q&A pairs with 3 variations each
    predefined_qa = {
        "what is my best suited wedding outfit?": [
            "For a formal wedding, I highly recommend our **Suit Collection #4** in deep burgundy.",
            "Our **Suit Collection #8** in a tailored emerald green is an exceptional choice for weddings.",
            "The **Suit Collection #12** offers a timeless navy tone perfect for grand wedding events."
        ],
        "which color palette fits my skin tone best?": [
            "Your undertones harmonize beautifully with jewel tones like emerald green and navy.",
            "Rich warm tones like burgundy, teal, and cream complement your undertones perfectly.",
            "Deep earth tones and polished gold accents match your complexion spectacularly."
        ],
        "how does the ai determine my body type?": [
            "Our vision engine calculates skeletal ratios like your shoulder-to-hip balance.",
            "The AI analyzes your body proportions by mapping key skeletal joint landmarks.",
            "Our algorithms compare your torso-to-leg ratios to standard silhouette profiles."
        ],
        "what styling mistake should i avoid for my silhouette?": [
            "Avoid wearing completely formless boxy styles that mask your natural waist structure.",
            "Try to bypass stiff fabrics that drape poorly over your natural shoulder curvature.",
            "We recommend staying away from heavy visual patterns that disrupt your proportions."
        ],
        "can you recommend a casual suit for a weekend brunch?": [
            "The relaxed structure of **Suit Collection #5** paired with a light crewneck is an ideal fit.",
            "Our **Suit Collection #1** is an effortless smart-casual choice for brunch outings.",
            "The lightweight fabric drape of **Suit Collection #17** works beautifully for casual days."
        ],
        "what are the latest fashion trends for this season?": [
            "Quiet luxury separates and monochromatic layering dominate this season's collections.",
            "Minimalist tailoring and deep, saturated jewel tones are leading the current season.",
            "Sophisticated separates and structured blazers are highly popular in high-end design."
        ],
        "how should i dress for a professional executive meeting?": [
            "Opt for the sharp, structured shoulder profile of **Suit Collection #2** to command elegance.",
            "The tailored fit of **Suit Collection #14** projects a clean, authoritative corporate look.",
            "For key corporate calls, styling the sleek profile of **Suit Collection #20** is optimal."
        ],
        "which outfit is recommended for a campus presentation?": [
            "The smart-casual balance of **Suit Collection #6** offers the perfect mix of comfort and focus.",
            "Our **Suit Collection #12** in a clean, regular fit presents a highly polished student look.",
            "Styling **Suit Collection #18** with simple clean pieces is perfect for presentations."
        ],
        "how do i choose the correct size for custom luxury suits?": [
            "Our model matches your skeletal frame parameters directly to standard luxury sizes.",
            "We calibrate your shoulder width and waist ratio to ensure the ideal suit size matches.",
            "All recommended fits are pre-filtered to size standard parameters to guarantee comfort."
        ],
        "what makes wearwise different from other styling tools?": [
            "We combine precision skeletal landmark scans with high-end luxury fashion theory.",
            "Our tool analyzes body geometry and color chemistry rather than basic style quizzes.",
            "WearWise generates custom Style DNA profiles mapped to a real curated catalog."
        ]
    }

    # Cycling engaging follow-up questions
    styling_questions = [
        "Would you prefer styling this with gold accents or minimalist silver jewelry?",
        "Are you planning to layer this look with a light knitwear piece or keep it simple?",
        "Should we pair this with classic leather oxfords or modern luxury sneakers?",
        "Are you looking to focus on warm earth tones or rich jewel shades for this look?",
        "Would you style this suit open with a silk camisole or buttoned up for structure?",
        "Do you prefer a tailored slim silhouette or a relaxed contemporary drape?",
        "Would you wear this outfit to an evening social function or a daytime event?",
        "Should we match this outfit with structured neutral outerwear or a pop of color?"
    ]
    followup_q = styling_questions[cycle_idx % len(styling_questions)]

    # Match predefined question
    clean_key = msg_lower.replace("?", "").strip() + "?"
    reply_core = None
    for k, variations in predefined_qa.items():
        if clean_key == k or msg_lower == k:
            reply_core = variations[cycle_idx % len(variations)]
            break

    if reply_core:
        reply = f"{reply_core} {followup_q}"
    else:
        # Dynamic fallback matching
        analysis = get_current_analysis()
        predicted_size = analysis.get('size_prediction', {}).get('size') if analysis else "M"
        body_type = analysis.get('body_type_detection', {}).get('type') if analysis else "Rectangle"
        skin_tone = session.get('skin_tone', 'Medium')

        # Wedding
        if any(word in msg_lower for word in ['wedding', 'marriage', 'festive', 'reception', 'traditional', 'party']):
            options = [
                f"Based on your **{body_type}** frame, the deep burgundy profile of **Suit Collection #4** is highly recommended.",
                f"For weddings, matching your **{skin_tone}** tone with the emerald **Suit Collection #8** is stunning.",
                f"I suggest styling the navy **Suit Collection #12** in size **{predicted_size}** for formal festive events."
            ]
            reply_core = options[cycle_idx % len(options)]
        # College
        elif any(word in msg_lower for word in ['college', 'school', 'university', 'campus', 'classes', 'student']):
            options = [
                f"For college, the relaxed structure of **Suit Collection #6** provides comfort and smart lines.",
                f"I recommend the lightweight smart draping of **Suit Collection #12** for daily campus wear.",
                f"Opt for **Suit Collection #18** to combine modern collegiate comfort with clean lines."
            ]
            reply_core = options[cycle_idx % len(options)]
        # Office
        elif any(word in msg_lower for word in ['office', 'work', 'job', 'interview', 'meeting', 'professional', 'formal']):
            options = [
                "I recommend the structured shoulders of **Suit Collection #2** for professional authority.",
                f"The tailored corporate fit of **Suit Collection #14** in size **{predicted_size}** works beautifully for meetings.",
                "Opt for the sharp corporate design of **Suit Collection #20** to command elegance."
            ]
            reply_core = options[cycle_idx % len(options)]
        # Color
        elif any(word in msg_lower for word in ['color', 'skin', 'palette', 'shade', 'hue', 'tone']):
            options = [
                f"Your **{skin_tone}** tone works beautifully with jewel tones, but bypass neons.",
                "We recommend matching your undertones with rich, earthy shades and warm metallics.",
                "Opt for deep classic navy, emerald, or burgundy to contrast with your complexion profile."
            ]
            reply_core = options[cycle_idx % len(options)]
        # Body Shape / Fit
        elif any(word in msg_lower for word in ['body type', 'body shape', 'hourglass', 'pear', 'rectangle', 'triangle', 'apple', 'athletic', 'silhouette', 'fit', 'cut']):
            options = [
                f"A custom cut like **Suit Collection #7** will balance your **{body_type}** frame nicely.",
                f"For a **{body_type}** frame, we look to build structured lines with targeted waist styling.",
                f"Opt for the balanced drape of **Suit Collection #3** (Oversized) to highlight your proportions."
            ]
            reply_core = options[cycle_idx % len(options)]
        # Size
        elif any(word in msg_lower for word in ['size', 'measurement', 'fit me', 'proportion', 'tall', 'short']):
            options = [
                f"All suits in your collection are pre-filtered to size **{predicted_size}** to guarantee an optimal drape.",
                f"We align standard frame width sizes with your predicted size **{predicted_size}** locker.",
                f"Sizing is locked to **{predicted_size}** to prevent loose sagging or uncomfortable pulling."
            ]
            reply_core = options[cycle_idx % len(options)]
        # Avoid
        elif any(word in msg_lower for word in ['mistake', 'avoid', 'don\'t wear', 'should not wear', 'bad fit']):
            options = [
                "Avoid boxy clothing that hides your waist structure completely.",
                "Bypass heavy, high-contrast patterns that distract from your natural frame.",
                "Avoid flat neon shades that clash with your color Undertones."
            ]
            reply_core = options[cycle_idx % len(options)]
        # Trends
        elif any(word in msg_lower for word in ['trend', 'latest', 'modern', 'current', 'in style', 'season', 'summer', 'winter']):
            options = [
                "Quiet luxury and clean monochromatic layers are this season's best look.",
                "Saturated jewel tones and structured separates are dominating modern design.",
                "Classic minimalist tailoring is the leading trend for luxury styling this season."
            ]
            reply_core = options[cycle_idx % len(options)]
        # Casual
        elif any(word in msg_lower for word in ['casual', 'weekend', 'brunch', 'everyday', 'simple']):
            options = [
                f"For smart-casual days, the comfortable drape of **Suit Collection #1** is excellent.",
                f"I recommend the relaxed styling of **Suit Collection #5** in size **{predicted_size}** for weekends.",
                "Style the regular-fit **Suit Collection #17** with clean basic layers for effortless leisure."
            ]
            reply_core = options[cycle_idx % len(options)]
        # Fallback
        else:
            options = [
                f"To support your **{body_type}** frame, I recommend exploring **Suit Collection #1** in size **{predicted_size}**.",
                f"I suggest starting with **Suit Collection #4** in size **{predicted_size}** to match your style DNA.",
                f"Opt for the tailored versatility of **Suit Collection #10** to build your outfit foundation."
            ]
            reply_core = options[cycle_idx % len(options)]

        reply = f"{reply_core} {followup_q}"

    # Remove bold markdown formatting if present
    reply = reply.replace('**', '')

    # Append to chat history
    if 'chat_history' not in session:
        session['chat_history'] = []
    session['chat_history'].append({"user": msg, "bot": reply})
    session.modified = True
    
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

@app.route('/api/reserve', methods=['POST'])
def api_reserve():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    bust = data.get('bust', '')
    waist = data.get('waist', '')
    hips = data.get('hips', '')
    height = data.get('height', '')
    suit_name = data.get('suit_name')
    price = data.get('price')
    
    if not all([name, email, phone, suit_name, price]):
        return jsonify({"success": False, "message": "Required fields are missing."}), 400
        
    try:
        if isinstance(price, str):
            price = price.replace('₹', '').strip()
        price_val = int(price)
    except Exception:
        price_val = 0

    try:
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO reservations (name, email, phone, bust, waist, hips, height, suit_name, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, phone, bust, waist, hips, height, suit_name, price_val))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Your reservation has been recorded successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Database error: {e}"}), 500

@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    reservations = conn.execute('SELECT * FROM reservations ORDER BY timestamp DESC').fetchall()
    
    # Analytics
    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    total_uploads = conn.execute('SELECT COUNT(*) FROM uploads').fetchone()[0]
    total_reservations = conn.execute('SELECT COUNT(*) FROM reservations').fetchone()[0]
    
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
        "total_reservations": total_reservations,
        "top_size": top_size,
        "top_body": top_body
    }
    
    return render_template('admin.html', products=products, stats=stats, reservations=reservations)

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
    price = request.form.get('price', 2999)
    
    # Handle Image Upload
    image_file = request.files.get('image')
    image_filename = ""
    if image_file and image_file.filename:
        filename = secure_filename(image_file.filename)
        products_dir = os.path.join(app.root_path, 'static', 'products')
        os.makedirs(products_dir, exist_ok=True)
        image_file.save(os.path.join(products_dir, filename))
        image_filename = filename

    # Save to CSV so it shows up in Recommendations/Collections
    csv_path = os.path.join(os.path.dirname(__file__), 'wearwise_products.csv')
    try:
        df = pd.read_csv(csv_path)
    except Exception:
        df = pd.DataFrame(columns=["id", "name", "image", "price", "size", "fit", "category", "gender", "match_score", "body_type", "skin_tone", "recommer", "description", "style_match"])

    next_id = int(df['id'].max() + 1) if not df.empty else 1
    new_row = {
        "id": next_id,
        "name": name,
        "image": image_filename,
        "price": int(price),
        "size": "M",  # Base size
        "fit": fit,
        "category": cat,
        "gender": gender,
        "match_score": 85,
        "body_type": body_type,
        "skin_tone": "Medium",
        "recommer": "Peach, Cre",
        "description": desc,
        "style_match": 85
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(csv_path, index=False)

    # Save to SQLite Database
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO products (name, code, description, gender, category, body_type_suitability, suggested_fit) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (name, code, desc, gender, cat, body_type, fit))
        conn.commit()
    except Exception as e:
        pass
    conn.close()
    
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:id>')
def delete_product(id):
    if not session.get('admin'):
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (id,)).fetchone()
    if product:
        name_to_delete = product['name']
        conn.execute('DELETE FROM products WHERE id = ?', (id,))
        conn.commit()
        
        # Also remove from CSV
        csv_path = os.path.join(os.path.dirname(__file__), 'wearwise_products.csv')
        try:
            df = pd.read_csv(csv_path)
            # Remove by matching name (case-insensitive)
            df = df[df['name'].str.lower() != name_to_delete.lower()]
            df.to_csv(csv_path, index=False)
        except Exception:
            pass
            
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
