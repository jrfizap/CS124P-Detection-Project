import pytesseract
import logging
import cv2
import re
from utils.helpers import get_composite_score, calculate_similarity

# Configure Windows Tesseract Path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_and_score_id(filepath, user_data):
    """
    Runs OCR on the image with grayscale preprocessing.
    Checks for standard ID terminology to validate document type,
    then uses Token-based Fuzzy Matching to verify Sta. Rosa residency.
    """
    try:
        # 1. Pre-process the image for better OCR reading
        image = cv2.imread(filepath)
        if image is None:
            return {"success": False, "error": "Could not read image for OCR."}
            
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        ocr_text = pytesseract.image_to_string(gray)
        
        if not ocr_text.strip():
            return {"success": False, "error": "No readable text found on the image."}

        # 2. Tokenize the OCR text (break it into individual words)
        normalized_ocr = ocr_text.replace('\n', ' ').strip().lower()
        clean_ocr = re.sub(r'[^a-z0-9\s]', '', normalized_ocr)
        ocr_tokens = clean_ocr.split()

        # ==========================================
        # 3. Valid ID Detection (Keyword Matching)
        # ==========================================
        # List of common words found on standard Philippine IDs
        id_keywords = [
            "republic", "philippines", "identification", "card", "license", 
            "umid", "philsys", "tin", "voter", "postal", "passport", "barangay", 
            "signature", "birth", "dob", "address", "name", "crn", "valid"
        ]
        
        # Count how many common ID keywords are found in the cleaned OCR text
        keywords_found = sum(1 for keyword in id_keywords if keyword in clean_ocr)
        
        # If the computer cannot find at least 2 common ID terms, reject it as a non-ID
        if keywords_found < 2:
            logging.warning("INVALID_ID_DETECTED: No standard ID keywords found in OCR text.")
            return {
                "success": False, 
                "error": "The uploaded document does not appear to be a valid ID. Please upload a clear photo of a recognized government identification card."
            }

        # ==========================================
        # 4. TOKEN LOGIC: City Validation
        # ==========================================
        score_santa = get_composite_score("santa", ocr_tokens)
        score_sta = get_composite_score("sta", ocr_tokens)
        score_rosa = get_composite_score("rosa", ocr_tokens)

        best_first_word_score = max(score_santa, score_sta)

        is_from_sta_rosa = (best_first_word_score >= 0.75) and (score_rosa >= 0.75)
        
        if not is_from_sta_rosa:
            smashed_text = clean_ocr.replace(" ", "")
            if "starosa" in smashed_text or "santarosa" in smashed_text:
                is_from_sta_rosa = True

        if not is_from_sta_rosa:
            logging.warning(f"OUTSIDE_STA_ROSA_DETECTED. Best token scores -> Santa/Sta: {best_first_word_score}, Rosa: {score_rosa}")
            return {
                "success": False, 
                "error": "Address not within Sta. Rosa. Please ensure your ID displays a valid Sta. Rosa address."
            }

        # ==========================================
        # 5. Scoring Logic (Names & Address)
        # ==========================================
        first_name_score = get_composite_score(user_data.get('first_name'), ocr_tokens)
        last_name_score = get_composite_score(user_data.get('last_name'), ocr_tokens)
        
        middle_name = user_data.get('middle_name')
        has_middle_name = bool(middle_name)
        middle_name_score = get_composite_score(middle_name, ocr_tokens) if has_middle_name else 0

        address_tokens = user_data.get('address', '').lower().split()
        address_matches = 0
        valid_address_tokens = 0
        
        for token in address_tokens:
            if len(token) < 3:
                continue
            valid_address_tokens += 1
            
            for ocr_token in ocr_tokens:
                if calculate_similarity(token, ocr_token) >= 0.80:
                    address_matches += 1
                    break
                    
        address_score = (address_matches / valid_address_tokens) if valid_address_tokens > 0 else 0

        # ==========================================
        # 6. Final Weighted Score Matrix
        # ==========================================
        if has_middle_name:
            total_score = (last_name_score * 0.35) + (first_name_score * 0.30) + (middle_name_score * 0.10) + (address_score * 0.25)
        else:
            total_score = (last_name_score * 0.40) + (first_name_score * 0.35) + (address_score * 0.25)

        return {
            "success": True,
            "raw_text": ocr_text[:500],
            "total_score": total_score,
            "scores": {
                "first_name": first_name_score,
                "last_name": last_name_score,
                "middle_name": middle_name_score,
                "address": address_score
            }
        }

    except Exception as e:
        logging.error(f"OCR_ERROR: {str(e)}")
        return {"success": False, "error": "System could not process image text."}