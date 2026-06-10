# WearWise AI - Smart Body Analysis and Clothing Recommendation System

WearWise AI is a complete production-quality web application that analyzes a user's full-body image to estimate body proportions using computer vision, determines body type and clothing size, and recommends suitable clothing items.

## Features
- AI Body Analysis (MediaPipe Pose)
- Size Prediction & Smart Clothing Recommendation
- BMI Calculator
- Color Recommendation AI & Fashion Stylist AI
- Admin Panel & Analytics Dashboard
- Responsive Premium UI with Glassmorphism

## Setup Instructions

1. **Install Python**: Ensure Python 3.8+ is installed on your Windows machine.
2. **Install wkhtmltopdf**: This is required for PDF generation (`pdfkit`). Download and install it from [https://wkhtmltopdf.org/downloads.html](https://wkhtmltopdf.org/downloads.html). After installation, add the `bin` folder to your system PATH.
3. **Install Dependencies**:
   Open a terminal in the project directory and run:
   ```bash
   pip install -r requirements.txt
   ```
4. **Initialize Database**:
   Run the following script to create the SQLite database and populate it with sample products and the default admin user.
   ```bash
   python database.py
   ```
5. **Run the Application**:
   ```bash
   python app.py
   ```
6. **Access the App**:
   Open your browser and go to `http://127.0.0.1:5000`.

## Admin Credentials
- **Username**: admin
- **Password**: admin

## Folder Structure
- `app.py`: Main Flask application.
- `database.py`: Database setup script.
- `models/`: Contains AI logic (Computer Vision & Recommendations).
- `templates/`: HTML files.
- `static/`: CSS, JS, and image uploads.
