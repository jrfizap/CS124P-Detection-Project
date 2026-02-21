import cv2
import numpy as np
import logging

def analyze_id_structure(filepath):
    """
    Analyzes the physical structure of the uploaded ID image.
    Uses Solidity and Rotated Rectangles to handle rounded corners and tilted camera angles,
    specifically targeting the CR80 ISO 7810 standard format.
    """
    try:
        image = cv2.imread(filepath)
        if image is None:
            return {"success": False, "error": "Could not read image for structure analysis."}
        
        # 1. Preprocessing (Grayscale, Bilateral Blur, Edges, Morphological Close)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Bilateral filter is better than Gaussian here because it blurs the background 
        # while keeping the edges of the ID card sharp.
        blurred = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Lowered the thresholds slightly to catch the edge of the ID against the skin
        edges = cv2.Canny(blurred, 30, 100)
        
        # Use a morphological 'close' to connect any broken lines in the edge detection
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # 2. Find Contours
        contours, _ = cv2.findContours(closed_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # --- VALIDATION ERROR ---
        if not contours:
            logging.warning("No contours detected in the image.")
            return {
                "success": False, 
                "error": "No ID-like shape or clear edges were detected. Please ensure you are uploading a clear photo of a physical ID card, not a handwritten note or document."
            }
        
        # Filter for small noise contours to ensure we have a substantial object
        valid_contours = [c for c in contours if cv2.contourArea(c) > 1000]
        if not valid_contours:
             logging.warning("Only small noise contours detected.")
             return {
                "success": False, 
                "error": "No significant shape detected. Please upload a clear, close-up photo of your ID card."
            }
            
        # 3. Find the largest contour (The ID Card)
        largest_contour = max(valid_contours, key=cv2.contourArea)
        
        # 4. Shape Detection (Using Solidity instead of counting sharp corners)
        contour_area = cv2.contourArea(largest_contour)
        hull = cv2.convexHull(largest_contour)
        hull_area = cv2.contourArea(hull)
        
        # Solidity is the ratio of the ID area to its "rubber band" area.
        # A perfect rectangle is 1.0. An ID with rounded corners is usually ~0.95 to 0.98.
        solidity = float(contour_area) / float(hull_area) if hull_area > 0 else 0
        is_rectangular = solidity > 0.90 # Relaxed to 90% to allow for slight background bleeding
        
        # 5. Size/Proportion Detection (CR80 ISO 7810 Format)
        # CR80 Physical Dimensions: 85.60 mm × 53.98 mm (3.375 in × 2.125 in)
        rect = cv2.minAreaRect(largest_contour)
        (center_x, center_y), (w, h), angle = rect
        
        # Ensure we always divide the long side by the short side, regardless of orientation
        width = max(w, h)
        height = min(w, h)
        
        aspect_ratio = float(width) / float(height) if height > 0 else 0
        
        # Target CR80 ISO 7810 aspect ratio is ~1.586
        # Tightened the tolerance (1.45 to 1.70) to strictly enforce the ID shape 
        # while allowing a small buffer for 3D camera perspective distortion.
        is_cr80_aspect_ratio = 1.45 <= aspect_ratio <= 1.70
        
        # Check minimum pixel resolution (e.g., ~150 DPI minimum for a CR80 card is ~500px wide)
        # Adjust this value based on how high-quality you need the uploads to be.
        min_pixel_width = 500
        is_valid_resolution = width >= min_pixel_width
        
        # It is a valid size if it matches the CR80 proportions AND is large enough to read
        is_valid_size = is_cr80_aspect_ratio and is_valid_resolution
        
        return {
            "success": True,
            "structural_analysis": {
                "is_rectangular": bool(is_rectangular),
                "aspect_ratio": round(aspect_ratio, 3),
                "solidity": round(solidity, 3),
                "is_valid_size": bool(is_valid_size),
                "matches_cr80_format": bool(is_cr80_aspect_ratio),
                "pixel_dimensions": {"width": int(width), "height": int(height)}
            }
        }

    except Exception as e:
        logging.error(f"VISION_ERROR: {str(e)}")
        return {"success": False, "error": "Structural analysis failed."}