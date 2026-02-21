# CS124P ID Detection Project 

# ID Validation System (OCR + Structural Analysis)
This project is a Flask-based microservice designed to enhance the **Sta. Rosa Vet System**. 
It goes beyond text matching by analyzing the physical dimensions and shape of ID cards.

## Features
- **OCR Extraction**: Uses Tesseract to pull ID numbers and names.
- **Size Detection**: Calculates aspect ratio to ensure the ID isn't distorted.
- **Shape Analysis**: Uses OpenCV contour detection to verify rectangular integrity.

## Tech Stack
- Python 3.x
- Flask
- OpenCV
- Tesseract OCR