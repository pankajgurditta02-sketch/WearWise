import os
import sys

# Add the project directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, session
from models.body_analysis import analyze_body
from xhtml2pdf import pisa
from io import BytesIO

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates'))
app.secret_key = 'test'

# Mock session context
filename = 'test.jpg' # let's just mock a run
filepath = 'static/products/suit1.jpg' # use an existing file to test
gender = 'Women'
skin_tone = 'Medium'

analysis = analyze_body(filepath, gender, skin_tone)
if analysis and "error" not in analysis:
    analysis['body_type'] = analysis['body_type_detection']['type']
    analysis['predicted_size'] = analysis['size_prediction']['size']
    analysis['skin_tone'] = skin_tone

with app.test_request_context():
    from flask import render_template
    html = render_template('pdf_report.html', 
                           analysis=analysis,
                           image_path=filepath)
    
    pdf_io = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_io)
    print("Pisa status err:", pisa_status.err)
    if pisa_status.err:
        print("Pisa errors details:", pisa_status.err)
