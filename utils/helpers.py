import difflib

def calculate_similarity(str1, str2):
    """Built-in fuzzy string matching. Returns a ratio between 0 and 1."""
    if not str1 or not str2:
        return 0.0
    return difflib.SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def get_composite_score(user_input, ocr_tokens):
    """Finds the best match for a user input word inside the OCR text."""
    if not user_input:
        return 0.0
    
    best_score = 0.0
    for token in ocr_tokens:
        score = calculate_similarity(user_input, token)
        if score > best_score:
            best_score = score
            
    return best_score