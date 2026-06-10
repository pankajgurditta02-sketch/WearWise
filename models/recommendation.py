def calculate_bmi(height_cm, weight_kg):
    """
    Calculates BMI and returns the category.
    """
    try:
        height_m = float(height_cm) / 100
        weight_kg = float(weight_kg)
        bmi = weight_kg / (height_m * height_m)
        bmi = round(bmi, 1)
        
        if bmi < 18.5:
            category = "Underweight"
        elif 18.5 <= bmi < 24.9:
            category = "Normal"
        elif 25 <= bmi < 29.9:
            category = "Overweight"
        else:
            category = "Obese"
            
        return {"bmi": bmi, "category": category}
    except (ValueError, TypeError, ZeroDivisionError):
        return {"error": "Invalid height or weight inputs."}


def recommend_colors(skin_tone, body_type):
    """
    Heuristic-based color recommendation AI based on skin tone and body type.
    """
    colors = {
        "Fair": {
            "best": ["Navy", "Emerald Green", "Maroon", "Black"],
            "why": "Darker, rich shades contrast beautifully with fair skin, making it pop without washing it out."
        },
        "Wheatish": {
            "best": ["Olive", "Mustard", "Burgundy", "Teal"],
            "why": "Warm earth tones perfectly complement the natural golden undertones of wheatish skin."
        },
        "Medium": {
            "best": ["White", "Cobalt Blue", "Ruby Red", "Forest Green"],
            "why": "Bright and bold colors bring out the healthy glow of medium skin tones."
        },
        "Dark": {
            "best": ["Beige", "Pastel Pink", "White", "Bright Yellow"],
            "why": "Lighter shades create a stunning contrast, highlighting the rich undertones of darker skin."
        }
    }
    
    # Body type modifications
    recommendation = colors.get(skin_tone, {"best": ["Black", "Navy", "Beige", "Olive", "White", "Maroon"], "why": "These are universally flattering colors."})
    
    if body_type == "Plus Size" and "Black" not in recommendation["best"]:
        recommendation["best"].append("Black")
        recommendation["why"] += " Black is added as it provides a slimming effect."
        
    return recommendation


def get_fashion_styles(gender, body_type):
    """
    Fashion Stylist AI generating looks based on gender and body type.
    """
    styles = []
    if gender == "Men":
        styles = [
            {"name": "Casual Look", "outfit": "Plain V-neck T-shirt with dark wash denim", "colors": "Navy & Dark Blue", "tips": "Roll up the sleeves slightly for a relaxed vibe."},
            {"name": "College Look", "outfit": "Graphic tee layered with an unbuttoned flannel shirt and chinos", "colors": "Olive & Beige", "tips": "Pair with white sneakers for comfort."},
            {"name": "Party Look", "outfit": "Fitted blazer over a crisp black shirt with trousers", "colors": "Black & Charcoal", "tips": "Add a metallic watch to elevate the look."},
            {"name": "Wedding Look", "outfit": "Silk Kurta with Pajama or tailored suit", "colors": "Maroon & Gold", "tips": "Ensure the fit across the shoulders is perfect."},
            {"name": "Office Look", "outfit": "Button-down oxford shirt with tailored dress pants", "colors": "Light Blue & Grey", "tips": "Tuck in the shirt and match your belt with your shoes."}
        ]
    else:
        styles = [
            {"name": "Casual Look", "outfit": "Oversized graphic tee with high-waisted mom jeans", "colors": "Pastel Pink & Light Blue", "tips": "Tuck the front of the tee for a better silhouette."},
            {"name": "College Look", "outfit": "Comfortable Kurti with leggings or a skater dress", "colors": "Mustard & White", "tips": "Layer with a denim jacket if it's chilly."},
            {"name": "Party Look", "outfit": "A-line sequin dress or a stylish jumpsuit", "colors": "Emerald Green or Black", "tips": "Accessorize with statement earrings."},
            {"name": "Wedding Look", "outfit": "Heavy embroidered Saree or Lehenga", "colors": "Red & Gold", "tips": "Drape the saree to highlight your best features."},
            {"name": "Office Look", "outfit": "Blazer over a blouse with pencil skirt or formal trousers", "colors": "Navy & Beige", "tips": "Keep jewelry minimal and professional."}
        ]
        
    return styles


def rate_outfit(body_type):
    """
    Mock Outfit Score. In a real scenario, this would use an object detection model to analyze clothing items.
    """
    # Generating a mock score with suggestions based on body type for demo purposes.
    score = 8.5
    suggestions = [
        "The color harmony is excellent.",
        "Consider adding a belt to enhance balance.",
    ]
    if body_type == "Slim":
        suggestions.append("Layering would add more dimension to the fit.")
    elif body_type == "Plus Size":
        suggestions.append("Ensure the fabric has a good drape to flatter your silhouette.")
        
    return {
        "score": score,
        "fit_analysis": "Good proportion",
        "balance": "Slightly top-heavy",
        "color_harmony": "Excellent",
        "suggestions": suggestions
    }
