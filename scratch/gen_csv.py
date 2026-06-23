import csv
import os

csv_path = r"C:\Users\karan\WearWise\wearwise_products.csv"

sizes = ['M', 'L', 'XL', 'S']
fits = ['Slim Fit', 'Tailored Fit', 'Oversized', 'Regular Fit']
categories = ['Casual', 'Office', 'Party', 'Wedding', 'Festive', 'College']
body_types = ['Pear', 'Rectangle', 'Apple', 'Inverted Triangle', 'Hourglass']
skin_tones = ['Medium', 'Wheatish', 'Dusky', 'Fair']
recommers = ['Peach, Cre', 'Emerald, N', 'Black, Silve', 'Maroon, G']

rows = []
for i in range(1, 31):
    id_val = i
    name_val = "Suit Collec"
    image_val = f"suit{i}.jpg"
    price_val = 1949 + (i - 1) * 50
    size_val = sizes[(i - 1) % 4]
    fit_val = fits[(i - 1) % 4]
    cat_val = categories[(i - 1) % 6]
    gender_val = "Women"
    
    # match score logic: starts at 81, goes up by 1 to 99 (at i=19), then at i=20 wraps to 80, then 81, 82...
    if i <= 19:
        match_score_val = 80 + i
    else:
        match_score_val = 80 + (i - 20)
        
    body_type_val = body_types[(i - 1) % 5]
    skin_tone_val = skin_tones[(i - 1) % 4]
    recommer_val = recommers[(i - 1) % 4]
    desc_val = f"Recommended outfit #{i} based on body analysis and style preferences."
    
    rows.append({
        "id": id_val,
        "name": name_val,
        "image": image_val,
        "price": price_val,
        "size": size_val,
        "fit": fit_val,
        "category": cat_val,
        "gender": gender_val,
        "match_score": match_score_val,
        "body_type": body_type_val,
        "skin_tone": skin_tone_val,
        "recommer": recommer_val,
        "description": desc_val,
        "style_match": match_score_val  # alias to prevent breaking existing python code
    })

fieldnames = ["id", "name", "image", "price", "size", "fit", "category", "gender", "match_score", "body_type", "skin_tone", "recommer", "description", "style_match"]

with open(csv_path, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("wearwise_products.csv generated successfully with 30 rows.")
