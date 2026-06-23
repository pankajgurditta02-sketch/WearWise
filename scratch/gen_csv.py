import csv
import os

csv_path = r"C:\Users\karan\WearWise\wearwise_products.csv"

sizes = ['M', 'L', 'XL', 'S']
fits = ['Slim Fit', 'Tailored Fit', 'Oversized', 'Regular Fit']
categories = ['Casual', 'Office', 'Party', 'Wedding', 'Festive', 'College']
body_types = ['Pear', 'Rectangle', 'Apple', 'Inverted Triangle', 'Hourglass']
skin_tones = ['Medium', 'Wheatish', 'Dusky', 'Fair']
recommers = ['Peach, Cre', 'Emerald, N', 'Black, Silve', 'Maroon, G']

# Map strictly to valid existing files in static/products
valid_images = [
    "suit1.jpg", "suit2.jpg", "suit3.jpg", "suit5.jpg", "suit6.jpg", 
    "suit9.jpg", "suit10.jpg", "suit11.jpg", "suit13.jpg", "suit14.jpg", 
    "suit15.jpg", "suit16.jpg", "suit17.jpg", "suit18.jpg", "suit19.jpg", 
    "suit20.png", "suit21.jpg", "suit22.jpg", "suit23.jpg", "suit24.jpg", 
    "suit25.jpg", "suit26.jpg", "suit27.jpg", "suit28.jpg", "suit29.jpg", 
    "suit30.jpg"
]

rows = []
for i in range(1, 31):
    id_val = i
    name_val = f"Suit Collection #{i}"
    image_val = valid_images[(i - 1) % len(valid_images)]
    price_val = 1949 + (i - 1) * 50
    size_val = sizes[(i - 1) % 4]
    fit_val = fits[(i - 1) % 4]
    cat_val = categories[(i - 1) % 6]
    gender_val = "Women"
    
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
        "style_match": match_score_val
    })

fieldnames = ["id", "name", "image", "price", "size", "fit", "category", "gender", "match_score", "body_type", "skin_tone", "recommer", "description", "style_match"]

with open(csv_path, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("wearwise_products.csv updated with corrected images and names.")
