import os
import sys
from flask import Flask
from xhtml2pdf import pisa
from io import BytesIO

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates'))

# Mock data matching the analysis schema
analysis = {
    "body_analysis": {
        "shoulder_to_hip_ratio": 1.05,
        "torso_to_leg_ratio": 1.15,
        "shoulder_width": 0.35,
        "hip_width": 0.33,
        "waist_width": 0.28,
        "body_height": 1.65,
        "frame_size": "Regular",
        "gender": "Women"
    },
    "body_type_detection": {
        "type": "Hourglass",
        "confidence": 88.5
    },
    "size_prediction": {
        "size": "M",
        "reasoning": "Balanced shoulder width and standard torso height ratio indicates a medium-to-large sizing for optimal comfort and drape."
    },
    "style_dna": {
        "Luxury Classic": 35,
        "Smart Casual": 25,
        "Minimalist": 15,
        "Business Casual": 10,
        "Contemporary Fashion": 10,
        "Streetwear": 5
    },
    "color_analysis": {
        "best": ["Deep Teal", "Burgundy", "Olive Green", "Rich Cream", "Coral"],
        "accent": ["Polished Gold", "Warm Bronze"],
        "avoid": ["Pale Grey", "Neon Green"]
    },
    "best_fit_analysis": {
        "fit": "Tailored Hourglass Profile Fit",
        "reasoning": "A specialized cut structured to balance the unique features of a Hourglass silhouette, creating a fluid, high-end profile."
    },
    "outfit_recommendations": [
        {
            "name": "Luxury Casual Look",
            "match_score": 95,
            "occasion": "Casual Look",
            "fit_type": "Regular Fit",
            "color_palette": ["Deep Teal", "Polished Gold", "Burgundy"],
            "reasoning": "✓ Tailored for Hourglass body type | ✓ Complements Medium skin tone | ✓ Fits M profile"
        },
        {
            "name": "Luxury Office Look",
            "match_score": 92,
            "occasion": "Office Look",
            "fit_type": "Slim Fit",
            "color_palette": ["Burgundy", "Rich Cream", "Olive Green"],
            "reasoning": "✓ Tailored for Hourglass body type | ✓ Complements Medium skin tone | ✓ Fits M profile"
        }
    ],
    "analytics_overview": {
        "body_symmetry_score": 85,
        "proportion_balance_score": 90,
        "fashion_confidence_score": 88
    }
}

filepath = 'static/products/suit1.jpg' # generic path
with app.test_request_context():
    from flask import render_template
    html = render_template('pdf_report.html', 
                           analysis=analysis,
                           image_path=filepath)
    
    pdf_io = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_io)
    print("Pisa status err:", pisa_status.err)
    if not pisa_status.err:
        with open('static/wearwise_report_test.pdf', 'wb') as f:
            f.write(pdf_io.getvalue())
        print("Generated wearwise_report_test.pdf successfully!")
