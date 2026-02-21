import cv2
import numpy as np
import logging

def analyze_id_structure(filepath):
    """
    Analyzes the physical structure of the uploaded ID image.
    Checks for rectangular shape and standard aspect ratio.
    """
    try:
        image = cv2.imread(filepath)
        if image is None:
            return {"success": False, "error": "Could not read image for structure analysis."}
        
        # 1. Preprocessing (Grayscale, Blur, Edges)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        
        # 2. Find Contours (Outlines)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {"success": False, "error": "No clear outlines detected in the image."}
            
        # 3. Find the largest contour (Assuming the ID card is the main subject)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # 4. Shape Detection: Approximate the contour to check if it's rectangular
        perimeter = cv2.arcLength(largest_contour, True)
        approx = cv2.approxPolyDP(largest_contour, 0.02 * perimeter, True)
        
        is_rectangular = len(approx) == 4
        
        # 5. Size/Proportion Detection
        x, y, w, h = cv2.boundingRect(largest_contour)
        aspect_ratio = float(w) / float(h)
        
        # Standard CR80 ID ratio is 1.586. 
        # We allow a tolerance range (1.4 to 1.7) to account for camera angles.
        is_valid_size = 1.4 <= aspect_ratio <= 1.7
        
        return {
            "success": True,
            "structural_analysis": {
                "is_rectangular": is_rectangular,
                "aspect_ratio": round(aspect_ratio, 3),
                "is_valid_size": is_valid_size,
                "pixel_dimensions": {"width": w, "height": h}
            }
        }

    except Exception as e:
        logging.error(f"VISION_ERROR: {str(e)}")
        return {"success": False, "error": "Structural analysis failed."}