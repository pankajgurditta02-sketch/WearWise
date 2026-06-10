import os

products_dir = r"C:\Users\asus2\OneDrive\Desktop\WearWise\static\products"
if os.path.exists(products_dir):
    for filename in os.listdir(products_dir):
        if filename.endswith(".jpg.jpg"):
            new_name = filename.replace(".jpg.jpg", ".jpg")
        elif filename.endswith(".png.jpg"):
            new_name = filename.replace(".png.jpg", ".png")
        else:
            new_name = filename
            
        if filename != new_name:
            old_path = os.path.join(products_dir, filename)
            new_path = os.path.join(products_dir, new_name)
            try:
                os.rename(old_path, new_path)
                print(f"Renamed {filename} -> {new_name}")
            except Exception as e:
                print(f"Failed to rename {filename}: {e}")
