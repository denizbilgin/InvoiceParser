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


def extract_tables_from_page_text(page_text: str) -> List[List[str]]:
    raw_tables = [tbl.strip() for tbl in re.split(r'\n(?:[ \t]*\n)+', page_text) if tbl.strip()]

    tables = []
    for raw_table in raw_tables:
        rows = [line.strip() for line in raw_table.splitlines() if line.strip()]
        if rows:
            tables.append(rows)

    return tables


def ocr_text_with_paragraphs(image, ocr_config='--oem 3 --psm 8', threshold_factor=1.0):
    data = pytesseract.image_to_data(image, config=ocr_config, output_type=pytesseract.Output.DICT)

    n_boxes = len(data['level'])
    lines = []
    last_line_num = -1
    line_text = ""

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

    heights = [data['height'][i] for i in range(n_boxes) if data['text'][i].strip() != ""]
    avg_line_height = sum(heights) / len(heights) if heights else 15  # default 15 px

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