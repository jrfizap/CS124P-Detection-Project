# Santa Rosa Resident Verification System (CS124P)

An automated 3-step identity verification microservice developed for the **Sta. Rosa Veterinary Office** project. This system integrates advanced **OCR (Tesseract)** and **Computer Vision (OpenCV)** to verify residency and ID authenticity.

## Features
- **3-Step Registration Flow**: A professional web interface for Personal Profile, ID Upload, and Result Summary.
- **CR80 Standard Validation**: Verifies physical ID dimensions against ISO/IEC 7810 standards (1.5858 aspect ratio).
- **Fuzzy Token Matching**: Intelligent text comparison that accounts for OCR misreads (e.g., "Sta. Rosa" vs "Santa Rosa").
- **Structural Integrity**: Analyzes solidity and contour area to reject non-ID objects like handwritten notes.

## Tech Stack
- **Backend**: Python 3.x, Flask
- **Frontend**: Tailwind CSS, Jinja2 Templates
- **Processing**: OpenCV, PyTesseract

## Prerequisites
1. **Tesseract OCR**: 
   - Install the engine from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).
   - Ensure the path in `services/ocr_service.py` matches your installation (Default: `C:\Program Files\Tesseract-OCR\tesseract.exe`).
2. **Assets**: 
   - Ensure `PawsBackground.png`, `Logo.png`, and `sample-national-id.png` are in the `static/images/` folder.

## Installation & Setup
1. **Create and Activate Virtual Environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   py app.py