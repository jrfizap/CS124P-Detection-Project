import os
import uuid
import logging
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# Import our new organized service
from services.ocr_service import extract_and_score_id

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/api/validate', methods=['POST'])
def validate_id():
    # 1. Input Validation
    if 'id_file' not in request.files:
        return jsonify({"error": "No ID file uploaded"}), 400
        
    file = request.files['id_file']
    
    # Grab the user data sent from Laravel
    user_data = {
        'first_name': request.form.get('first_name', ''),
        'middle_name': request.form.get('middle_name', ''),
        'last_name': request.form.get('last_name', ''),
        'address': request.form.get('address', '')
    }

    # 2. Save file temporarily
    filename = f"id_{uuid.uuid4().hex[:10]}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
    file.save(filepath)

    # 3. Process via Service
    result = extract_and_score_id(filepath, user_data)

    # 4. Clean up local file
    if os.path.exists(filepath):
        os.remove(filepath)

    # 5. Return Results
    if not result.get("success"):
        return jsonify({"success": False, "error": result.get("error")}), 400
        
    return jsonify({
        "success": True,
        "message": "OCR Processing Complete",
        "data": result
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)