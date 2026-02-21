import pytesseract
import logging
from utils.helpers import get_composite_score, calculate_similarity

# Configure Windows Tesseract Path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_and_score_id(filepath, user_data):
    """
    Runs OCR on the image, verifies Sta. Rosa residency, 
    and scores the text against user input.
    """
    try:
        # Extract text
        ocr_text = pytesseract.image_to_string(filepath)
        if not ocr_text.strip():
            return {"success": False, "error": "No readable text found."}

        # Normalize text
        normalized_ocr = ocr_text.replace('\n', ' ').strip().lower()
        ocr_tokens = normalized_ocr.split(' ')

        # Step 1: City Validation (Sta. Rosa Only)
        if "sta. rosa" not in normalized_ocr and "santa rosa" not in normalized_ocr:
            logging.warning('OUTSIDE_STA_ROSA_DETECTED')
            return {"success": False, "error": "Address not within Sta. Rosa."}

        # Step 2: Scoring
        first_name_score = get_composite_score(user_data.get('first_name'), ocr_tokens)
        last_name_score = get_composite_score(user_data.get('last_name'), ocr_tokens)
        
        middle_name = user_data.get('middle_name')
        has_middle_name = bool(middle_name)
        middle_name_score = get_composite_score(middle_name, ocr_tokens) if has_middle_name else 0

        # Address Logic
        address_tokens = user_data.get('address', '').lower().split(' ')
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

        # Step 3: Final Weighted Score
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
        return {"success": False, "error": "System could not process image."}