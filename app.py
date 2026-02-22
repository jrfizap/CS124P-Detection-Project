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
    # Mock data to replace Laravel's $barangays query
    barangays = [
        {"Barangay_ID": "1", "Barangay_Name": "Aplaya"},
        {"Barangay_ID": "2", "Barangay_Name": "Balibago"},
        {"Barangay_ID": "3", "Barangay_Name": "Don Jose"},
        {"Barangay_ID": "4", "Barangay_Name": "Macabling"},
        {"Barangay_ID": "5", "Barangay_Name": "Pooc"},
        {"Barangay_ID": "6", "Barangay_Name": "Tagapo"}
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
    """Processes the image and uses the session data for OCR scoring."""
    if 'id_file' not in request.files:
        return jsonify({"success": False, "error": "No ID file uploaded"}), 400
        
    file = request.files['id_file']
    user_data = session.get('user_data', {})

    filename = f"id_{uuid.uuid4().hex[:10]}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
    file.save(filepath)

    # 1. Structural Analysis
    vision_result = analyze_id_structure(filepath)
    if not vision_result.get("success"):
        # if os.path.exists(filepath): os.remove(filepath)
        # Returns the specific error (e.g., "No shape detected") to the frontend
        return jsonify({"success": False, "error": vision_result.get("error")}), 400

    # 2. OCR Text Extraction (Using Step 1 data)
    ocr_result = extract_and_score_id(filepath, user_data)
    
    if os.path.exists(filepath): 
        os.remove(filepath)

    if not ocr_result.get("success"):
        # Returns the specific error (e.g., "Not a valid ID" or "Not Sta Rosa")
        return jsonify({"success": False, "error": ocr_result.get("error")}), 400

    # 3. Final Validation Logic
    # We now check is_valid_size (which includes the CR80 check) and solidity
    structure_passed = vision_result['structural_analysis']['is_rectangular'] and vision_result['structural_analysis']['is_valid_size']
    text_passed = ocr_result.get('total_score', 0) >= 0.70

    if structure_passed and text_passed:
        final_status = "Valid"
    elif text_passed and not structure_passed:
        final_status = "Suspicious"
    else:
        final_status = "Invalid"

    # Save the results to the session so Step 3 can read them
    session['verification_results'] = {
        "final_status": final_status,
        "structural_data": vision_result['structural_analysis'],
        "ocr_data": ocr_result
    }

    return jsonify({"success": True, "redirect": url_for('step3')}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)