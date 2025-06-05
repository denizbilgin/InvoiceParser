import json
import os
from typing import Any
import cv2
import PyPDF2
import numpy as np
from PIL import Image
from readers.pdf_type import PDFType


def export_raw_ocr_outputs_as_json(result: dict[str, Any], filename: str, raw_ocr_outputs_folder_path: str):
    json_filename = os.path.splitext(filename)[0] + ".json"
    output_path = os.path.join(raw_ocr_outputs_folder_path, json_filename)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)


def detect_pdf_type(file_path: str) -> PDFType:
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)

            text_found = False
            for page_number in range(min(3, len(pdf_reader.pages))):
                page = pdf_reader.pages[page_number]
                text = page.extract_text().strip()
                if len(text) > 50:
                    text_found = True
                    break
            return PDFType.TEXT_BASED if text_found else PDFType.SCANNED_IMAGE
    except Exception as e:
        print(f"PDF type not detected: {e}")
        return PDFType.MIXED


def preprocess_image(image: Image.Image) -> Image.Image:
    try:
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        denoised = cv2.fastNlMeansDenoising(gray)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return Image.fromarray(thresh)

    except Exception as e:
        print(f"Image preprocessing error: {e}")
        return image
