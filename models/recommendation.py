import sqlite3
import os

def get_style_recommendations(gender, skin_tone, style_dna):
    """
    Query products from database and calculate compatibility based on:
    - Occasion matches (derived from style DNA)
    - Color pairings
    - Gender profiles
    """
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Select all products
    products = cursor.execute('SELECT * FROM products').fetchall()
    conn.close()

    # Determine highest style preferences
    top_style = max(style_dna, key=style_dna.get) if style_dna else "Minimalist"
    
    recommended_list = []
    for p in products:
        p_dict = dict(p)
        
        # Gender matching: if product gender matches user selection
        gender_match = 1.0 if p_dict['gender'].lower() == gender.lower() else 0.4
        
        # Occasion category matching based on style_dna
        category_match = 0.5
        p_cat = p_dict['category'].lower()
        if "classic" in top_style.lower() and p_cat in ["office", "wedding"]:
            category_match = 1.0
        elif "casual" in top_style.lower() and p_cat in ["casual", "college"]:
            category_match = 1.0
        elif "business" in top_style.lower() and p_cat in ["office"]:
            category_match = 1.0
        elif "contemporary" in top_style.lower() and p_cat in ["party", "festive"]:
            category_match = 1.0
            
        # Calculate compatibility
        compatibility = int((gender_match * 60) + (category_match * 40))
        compatibility = max(60, min(99, compatibility))
        
        p_dict['compatibility_score'] = compatibility
        recommended_list.append(p_dict)
        
    # Sort by compatibility
    recommended_list.sort(key=lambda x: x['compatibility_score'], reverse=True)
    return recommended_list
