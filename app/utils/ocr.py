import cv2
import pytesseract
import numpy as np
from imutils.perspective import four_point_transform
def perform_ocr(image_path):
    # Load the image
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply thresholding
    processed = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

    # OCR processing
    text = pytesseract.image_to_string(processed, config="--psm 6")
    return text
