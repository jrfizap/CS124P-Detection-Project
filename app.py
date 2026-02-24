import os
import uuid
import logging
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from werkzeug.utils import secure_filename

from services.ocr_service import extract_and_score_id
from services.vision_service import analyze_id_structure

app = Flask(__name__)
# Secret key is required to use Flask sessions securely
app.secret_key = 'cs124p-super-secret-key'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==========================================
# FRONTEND ROUTES (Landing, Step 1, Step 2, Step 3)
# ==========================================

@app.route('/', methods=['GET'])
def index():
    """Displays the Landing Page."""
    # Render the new index.html instead of instantly redirecting
    return render_template('index.html')

@app.route('/step1', methods=['GET', 'POST'])
def step1():
    """Handles the Personal Profile form."""
    
    # Updated to include all 18 barangays of Sta. Rosa
    barangays = [
        {"Barangay_ID": "1", "Barangay_Name": "Aplaya"},
        {"Barangay_ID": "2", "Barangay_Name": "Balibago"},
        {"Barangay_ID": "3", "Barangay_Name": "Caingin"},
        {"Barangay_ID": "4", "Barangay_Name": "Dila"},
        {"Barangay_ID": "5", "Barangay_Name": "Dita"},
        {"Barangay_ID": "6", "Barangay_Name": "Don Jose"},
        {"Barangay_ID": "7", "Barangay_Name": "Ibaba"},
        {"Barangay_ID": "8", "Barangay_Name": "Kanluran"},
        {"Barangay_ID": "9", "Barangay_Name": "Labas"},
        {"Barangay_ID": "10", "Barangay_Name": "Macabling"},
        {"Barangay_ID": "11", "Barangay_Name": "Malitlit"},
        {"Barangay_ID": "12", "Barangay_Name": "Malusak"},
        {"Barangay_ID": "13", "Barangay_Name": "Market Area"},
        {"Barangay_ID": "14", "Barangay_Name": "Pook"},
        {"Barangay_ID": "15", "Barangay_Name": "Pulong Santa Cruz"},
        {"Barangay_ID": "16", "Barangay_Name": "Santo Domingo"},
        {"Barangay_ID": "17", "Barangay_Name": "Sinalhan"},
        {"Barangay_ID": "18", "Barangay_Name": "Tagapo"}
    ]

    if request.method == 'POST':
        # Capture all the new fields exactly as they are named in HTML
        session['user_data'] = {
            'first_name': request.form.get('First_Name', ''),
            'middle_name': request.form.get('Middle_Name', ''),
            'last_name': request.form.get('Last_Name', ''),
            'birthdate': request.form.get('Birthdate', ''),
            'civil_status': request.form.get('Civil_Status', ''),
            'years_of_residency': request.form.get('Years_Of_Residency', ''),
            'contact_number': request.form.get('Contact_Number', ''),
            'barangay_id': request.form.get('Barangay_ID', ''),
            'city': request.form.get('City', 'Sta. Rosa, Laguna'),
            'address': request.form.get('Address', '')
        }
        return redirect(url_for('step2'))
        
    return render_template('step1.html', barangays=barangays, data=session.get('user_data', {}))

@app.route('/step2', methods=['GET'])
def step2():
    """Handles the ID Upload page."""
    # If they skipped step 1, send them back
    if 'user_data' not in session:
        return redirect(url_for('step1'))
        
    return render_template('step2.html')

@app.route('/step3', methods=['GET'])
def step3():
    """Displays the final verification results."""
    # Retrieve the results saved during the API validation
    results = session.get('verification_results')
    
    # If there are no results, they haven't uploaded an ID yet
    if not results:
        return redirect(url_for('step2'))
        
    return render_template('step3.html', results=results)

# ==========================================
# BACKEND API ROUTE
# ==========================================

@app.route('/api/validate', methods=['POST'])
def validate_id():
    """Processes the image and ALWAYS redirects to Step 3, even on failure."""
    if 'id_file' not in request.files:
        return jsonify({"success": False, "error": "No ID file uploaded"}), 400
        
    file = request.files['id_file']
    user_data = session.get('user_data', {})

    filename = f"id_{uuid.uuid4().hex[:10]}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
    file.save(filepath)

    # 1. Run both analysis services
    vision_result = analyze_id_structure(filepath)
    ocr_result = extract_and_score_id(filepath, user_data)
    
    # 2. Setup default "Failed" data in case a service crashed or rejected the image
    # This prevents Step 3's HTML from crashing when it tries to display percentages
    structural_data = vision_result.get('structural_analysis', {
        "is_rectangular": False, "aspect_ratio": 0.0, "solidity": 0.0,
        "is_valid_size": False, "matches_cr80_format": False,
        "pixel_dimensions": {"width": 0, "height": 0},
        "processed_image": "" 
    })
    
    ocr_data = ocr_result if ocr_result.get("success") else {
        "total_score": 0.0,
        "scores": {"first_name": 0.0, "last_name": 0.0, "middle_name": 0.0, "address": 0.0}
    }

    # 3. Determine Final Status and capture the specific error message
    error_message = None
    if not vision_result.get("success"):
        final_status = "Invalid"
        error_message = vision_result.get("error")
    elif not ocr_result.get("success"):
        final_status = "Invalid"
        error_message = ocr_result.get("error")
    else:
        # If both services succeeded, do the final math
        structure_passed = structural_data['is_rectangular'] and structural_data['is_valid_size']
        text_passed = ocr_data.get('total_score', 0) >= 0.70

        if structure_passed and text_passed:
            final_status = "Valid"
        elif text_passed and not structure_passed:
            final_status = "Suspicious"
        else:
            final_status = "Invalid"

    # 4. Save to session so Step 3 can render it
    session['verification_results'] = {
        "final_status": final_status,
        "specific_error": error_message,  # We pass the exact reason it failed
        "structural_data": structural_data,
        "ocr_data": ocr_data
    }

    # ALWAYS return success: True so the frontend JS redirects to Step 3
    return jsonify({"success": True, "redirect": url_for('step3')}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)