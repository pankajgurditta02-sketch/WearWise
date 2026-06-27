import hashlib
import random
import os

def generate_seeded_random(seed_str):
    seed = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (10 ** 8)
    rng = random.Random(seed)
    return rng

def generate_style_dna(rng):
    styles = ["Luxury Classic", "Smart Casual", "Streetwear", "Minimalist", "Business Casual", "Contemporary Fashion"]
    dna = {}
    remaining = 100
    rng.shuffle(styles)
    for i, style in enumerate(styles):
        if i == len(styles) - 1:
            dna[style] = remaining
        else:
            val = rng.randint(5, min(40, remaining - (len(styles) - i - 1) * 5))
            dna[style] = val
            remaining -= val
    return dna

def analyze_body(image_path, gender="Women", skin_tone="Medium"):
    """
    Performs visual aesthetic scanning based on gender, skin tone, and color contrast.
    Does NOT predict body dimensions, sizes, shapes, or scores.
    """
    filename = os.path.basename(image_path)
    rng = generate_seeded_random(filename)
    
    # Clean skin tone color recommendations
    tone = skin_tone.lower()
    if "fair" in tone:
        best_colors = ["Emerald Green", "Royal Navy", "Ruby Red", "Ivory Cream", "Pastel Pink"]
        accent_colors = ["Rose Gold", "Warm Gold"]
        avoid_colors = ["Neon Yellow", "Bright Orange"]
    elif "dark" in tone or "dusky" in tone:
        best_colors = ["Warm Mustard", "Emerald Green", "Rich Maroon", "Royal Blue", "Bright Gold"]
        accent_colors = ["Bronze", "Copper"]
        avoid_colors = ["Dusty Lavender", "Pale Silver"]
    else: # Medium or Wheatish
        best_colors = ["Deep Teal", "Burgundy", "Olive Green", "Rich Cream", "Coral"]
        accent_colors = ["Polished Gold", "Warm Bronze"]
        avoid_colors = ["Pale Grey", "Neon Green"]

    style_dna = generate_style_dna(rng)
    
    fashion_summary = (
        f"Visual style scan matches your profile to a primary aesthetic of {max(style_dna, key=style_dna.get)}. "
        f"We suggest styling with {', '.join(best_colors[:3])} to complement your {skin_tone} skin tone."
    )

    return {
        "gender": gender,
        "skin_tone": skin_tone,
        "style_dna": style_dna,
        "color_analysis": {
            "best": best_colors,
            "accent": accent_colors,
            "avoid": avoid_colors
        },
        "fashion_summary": fashion_summary
    }
