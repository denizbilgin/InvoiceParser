import json
import os
import re
from typing import Any, List
import cv2
import PyPDF2
import numpy as np
import pytesseract
from PIL import Image
from readers.pdf_type import PDFType


def export_outputs_as_json(result: dict[str, Any], filename: str, folder_path: str):
    """
    This function exports given dictionary to given filename
    :param result: Dictionary to export
    :param filename: Name of the file to export
    :param folder_path: Folder to export
    :return: None
    """
    json_filename = os.path.splitext(filename)[0] + ".json"
    output_path = os.path.join(folder_path, json_filename)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)


def detect_pdf_type(file_path: str) -> PDFType:
    """
    This function detects type of given PDF by using custom enum
    :param file_path: File to detect type
    :return: Type of the file
    """
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
    """
    This function preprocesses a given PIL image to enhance text visibility for OCR.
    :param image: A PIL.Image object representing the input image
    :return: A binarized and enhanced PIL.Image object suitable for OCR or further processing
    """
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


def extract_tables_from_page_text(page_text: str) -> List[List[str]]:
    """
    This function extracts/groups given text of the page by regex process
    :param page_text: Page text to group
    :return: Organized and grouped page data
    """
    # Extracts tables if it see '/n', '/n/n' or '/n /n /n'
    raw_tables = [tbl.strip() for tbl in re.split(r'\n(?:[ \t]*\n)+', page_text) if tbl.strip()]

    tables = []
    for raw_table in raw_tables:
        rows = [line.strip() for line in raw_table.splitlines() if line.strip()]
        if rows:
            tables.append(rows)

    return tables


def ocr_text_with_paragraphs(image, ocr_config='--oem 3 --psm 8', threshold_factor=1.0):
    """
    This function performs Optical Character Recognition (OCR) on a given image and reconstructs the recognized text
    with basic paragraph and line separation logic based on line spacing.
    :param image: A PIL.Image object containing the image to be processed
    :param ocr_config: Tesseract OCR configuration string. Defaults to '--oem 3 --psm 8'
    :param threshold_factor: (Optional) A multiplier for average line height to determine paragraph spacing
                             Larger values make paragraph detection stricter. Default is 1.0
    :return: A string containing the reconstructed OCR text with appropriate newlines and paragraph breaks
    """
    data = pytesseract.image_to_data(image, config=ocr_config, output_type=pytesseract.Output.DICT)

    n_boxes = len(data['level'])
    lines = []
    last_line_num = -1
    line_text = ""

    # Group words into lines based on line_num
    for i in range(n_boxes):
        line_num = data['line_num'][i]
        text = data['text'][i].strip()

        if text == "":
            continue

        if line_num != last_line_num:
            if line_text:
                lines.append((last_line_num, line_text))
            line_text = text
            last_line_num = line_num
        else:
            line_text += " " + text

    if line_text:
        lines.append((last_line_num, line_text))

    result_text = ""
    last_bottom = None
    last_top = None

    # Calculate average line height for spacing-based decisions
    heights = [data['height'][i] for i in range(n_boxes) if data['text'][i].strip() != ""]
    avg_line_height = sum(heights) / len(heights) if heights else 15  # default 15 px

    # Reconstruct text with line/paragraph breaks based on vertical spacing
    for i, (line_num, text) in enumerate(lines):
        ys = [data['top'][j] for j in range(n_boxes) if data['line_num'][j] == line_num]
        hs = [data['height'][j] for j in range(n_boxes) if data['line_num'][j] == line_num]

        if not ys or not hs:
            continue

        top = min(ys)
        bottom = max([y + h for y, h in zip(ys, hs)])

        if last_bottom is None:
            result_text += text
        else:
            gap = top - last_bottom
            adjusted_threshold = avg_line_height * threshold_factor

            if line_num != lines[i-1][0]:
                if gap > adjusted_threshold * 1.5:
                    result_text += "\n\n" + text
                else:
                    result_text += "\n" + text
            else:
                result_text += " " + text

        last_bottom = bottom
        last_top = top

    return result_text
